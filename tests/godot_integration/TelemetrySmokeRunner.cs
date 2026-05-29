using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json;
using Godot;
using GodotSpacetime;
using GodotSpacetime.Connection;
using GodotSpacetime.Reducers;
using GodotSpacetime.Subscriptions;
using SpacetimeDB.Types;
using Environment = System.Environment;

namespace GodotSpacetime.IntegrationTests;

// Drives Story 9.3 telemetry verification against a real runtime.
// The contract is enforced by tests/test_story_9_3_connection_telemetry_integration.py.
public partial class TelemetrySmokeRunner : Node
{
    private enum Phase
    {
        None,
        Connect,
        Subscribe,
        InvokeReducer,
        ObserveRowChange,
        ReadTelemetry,
        Disconnect,
        Reconnect,
        ReadTelemetryReconnect,
        Done,
    }

    private static readonly StringName MessagesSentMonitorId = new("GodotSpacetime/Connection/MessagesSent");
    private static readonly StringName MessagesReceivedMonitorId = new("GodotSpacetime/Connection/MessagesReceived");
    private static readonly StringName BytesSentMonitorId = new("GodotSpacetime/Connection/BytesSent");
    private static readonly StringName BytesReceivedMonitorId = new("GodotSpacetime/Connection/BytesReceived");
    private static readonly StringName UptimeSecondsMonitorId = new("GodotSpacetime/Connection/UptimeSeconds");
    private static readonly StringName LastReducerRoundTripMonitorId = new("GodotSpacetime/Reducers/LastRoundTripMilliseconds");
    private static readonly StringName MessagesReceivedPerSecondMonitorId = new("GodotSpacetime/Connection/MessagesReceivedPerSecond");
    private static readonly StringName MessagesSentPerSecondMonitorId = new("GodotSpacetime/Connection/MessagesSentPerSecond");
    private static readonly StringName BytesReceivedPerSecondMonitorId = new("GodotSpacetime/Connection/BytesReceivedPerSecond");
    private static readonly StringName BytesSentPerSecondMonitorId = new("GodotSpacetime/Connection/BytesSentPerSecond");
    // The four GodotSpacetime/Reducers/{LatencyMinMs,LatencyMaxMs,SampleCount,PendingRequests}
    // monitor-equivalents are derived from the single CurrentTelemetry snapshot in
    // CaptureTelemetrySnapshot (not via Performance.GetCustomMonitor), so the parity gate compares
    // them against the SAME snapshot the categories are read from — no second pull, no drift.
    // See the 2026-05-28 spec amendment (finding 1).

    // Fixed order matches ConnectionTelemetryStats' 9 CategoryTelemetry properties and the
    // adapter's TryReadCategoryTelemetry order. Used to emit per-category scalars in payloads.
    private static readonly string[] CategoryNames =
    {
        "reducers",
        "procedures",
        "subscriptions",
        "one_off_queries",
        "all_reducers",
        "parse_message_queue",
        "parse_message",
        "apply_message_queue",
        "apply_message",
    };

    private string _host = "";
    private string _moduleName = "";
    private string _expectedValue = "";
    private double _stepTimeoutSeconds = 30.0;

    private SpacetimeClient? _client;
    private Phase _phase = Phase.None;
    private double _phaseStartedAt;
    private bool _finished;
    private bool _expectDisconnectForReconnect;

    private bool _sawGetRows;
    private bool _sawTypedTableHandle;
    private bool _sawRowChangedEvent;
    // Row-change events arrive from the SDK on a TransactionUpdate before the
    // matching ReducerCallSucceeded callback, so the insert signal for the
    // pending ping_insert value typically fires during the InvokeReducer phase.
    // Buffer every matching insert value so observation state can be re-seeded
    // when ObserveRowChange begins instead of waiting for a signal that has
    // already passed.
    private readonly HashSet<string> _observedInsertValues = new();
    private TelemetrySnapshot? _telemetryBeforeTraffic;
    private ReducerCallResult? _lastReducerResult;
    private ConnectionTelemetryStats? _stableTelemetryReference;
    private bool _stableTelemetryReusedAfterReconnect;
    private bool _postReconnectSubscribeRequested;

    public override void _Ready()
    {
        try
        {
            _host = Environment.GetEnvironmentVariable("SPACETIME_E2E_HOST") ?? "";
            _moduleName = Environment.GetEnvironmentVariable("SPACETIME_E2E_MODULE") ?? "";
            _expectedValue = (Environment.GetEnvironmentVariable("SPACETIME_E2E_VALUE") ?? "").Trim();

            var timeoutRaw = Environment.GetEnvironmentVariable("SPACETIME_E2E_STEP_TIMEOUT") ?? "30";
            if (!double.TryParse(timeoutRaw, NumberStyles.Float, CultureInfo.InvariantCulture, out var parsedTimeout))
                parsedTimeout = 30.0;
            _stepTimeoutSeconds = Math.Max(1.0, parsedTimeout);

            if (string.IsNullOrWhiteSpace(_host) ||
                string.IsNullOrWhiteSpace(_moduleName) ||
                string.IsNullOrWhiteSpace(_expectedValue))
            {
                Console.Error.WriteLine(
                    "TelemetrySmokeRunner: missing required env vars " +
                    "(SPACETIME_E2E_HOST, SPACETIME_E2E_MODULE, SPACETIME_E2E_VALUE).");
                Quit(1);
                return;
            }

            var settings = new SpacetimeSettings
            {
                Host = NormalizeHost(_host.Trim()),
                Database = _moduleName.Trim(),
            };

            _client = new SpacetimeClient { Settings = settings };
            _stableTelemetryReference = _client.CurrentTelemetry;
            _client.ConnectionStateChanged += OnConnectionStateChanged;
            _client.SubscriptionApplied += OnSubscriptionApplied;
            _client.SubscriptionFailed += OnSubscriptionFailed;
            _client.ReducerCallSucceeded += OnReducerCallSucceeded;
            _client.ReducerCallFailed += OnReducerCallFailed;
            _client.RowChanged += OnRowChanged;
            AddChild(_client);

            StartPhase(Phase.Connect);
            _client.Connect();
        }
        catch (Exception ex)
        {
            EmitError("bootstrap", ex.GetType().Name + ": " + ex.Message);
            Finish(pass: false);
        }
    }

    public override void _ExitTree()
    {
        if (_client == null)
            return;

        _client.ConnectionStateChanged -= OnConnectionStateChanged;
        _client.SubscriptionApplied -= OnSubscriptionApplied;
        _client.SubscriptionFailed -= OnSubscriptionFailed;
        _client.ReducerCallSucceeded -= OnReducerCallSucceeded;
        _client.ReducerCallFailed -= OnReducerCallFailed;
        _client.RowChanged -= OnRowChanged;
    }

    public override void _Process(double delta)
    {
        if (_finished || _phase == Phase.None || _phase == Phase.Done)
            return;

        var now = Time.GetTicksMsec() / 1000.0;
        if ((now - _phaseStartedAt) > _stepTimeoutSeconds)
        {
            EmitError(StepName(_phase), $"timed out after {_stepTimeoutSeconds:F1}s waiting for step completion");
            Finish(pass: false);
        }
    }

    private void StartPhase(Phase phase)
    {
        _phase = phase;
        _phaseStartedAt = Time.GetTicksMsec() / 1000.0;
    }

    private void OnConnectionStateChanged(ConnectionStatus status)
    {
        if (_finished || status == null || _client == null)
            return;

        if (_expectDisconnectForReconnect && status.State == ConnectionState.Disconnected)
        {
            _expectDisconnectForReconnect = false;

            var disconnectedTelemetry = CaptureTelemetrySnapshot();
            if (!IsResetSnapshot(disconnectedTelemetry))
            {
                EmitError(
                    "disconnect",
                    "disconnect must reset counters, uptime, and last reducer RTT to zero before reconnect.");
                Finish(pass: false);
                return;
            }

            EmitStepOk("disconnect", disconnectedTelemetry.ToPayload(includeMonitorComparison: true));

            StartPhase(Phase.Reconnect);
            try
            {
                _client.Connect();
            }
            catch (Exception ex)
            {
                EmitError("connect_reconnect", ex.GetType().Name + ": " + ex.Message);
                Finish(pass: false);
            }

            return;
        }

        if (status.State == ConnectionState.Connected)
        {
            switch (_phase)
            {
                case Phase.Connect:
                    EmitStepOk("connect", new Dictionary<string, object?>
                    {
                        ["description"] = status.Description,
                        ["active_compression_mode"] = status.ActiveCompressionMode.ToString(),
                    });
                    StartPhase(Phase.Subscribe);
                    SubscribeCurrentSession();
                    return;
                case Phase.Reconnect:
                    _stableTelemetryReusedAfterReconnect = ReferenceEquals(_stableTelemetryReference, _client.CurrentTelemetry);
                    EmitStepOk("connect_reconnect", new Dictionary<string, object?>
                    {
                        ["description"] = status.Description,
                        ["stable_telemetry_instance_reused"] = _stableTelemetryReusedAfterReconnect,
                    });
                    StartPhase(Phase.ReadTelemetryReconnect);
                    EmitReconnectTelemetry();
                    return;
            }
        }

        if (status.State == ConnectionState.Disconnected &&
            _phase != Phase.None &&
            _phase != Phase.Done &&
            _phase != Phase.Disconnect)
        {
            EmitError(StepName(_phase), $"disconnected mid-flight: {status.Description}");
            Finish(pass: false);
        }
    }

    private void OnSubscriptionApplied(SubscriptionAppliedEvent appliedEvent)
    {
        if (_finished || _client == null)
            return;

        if (_phase == Phase.ReadTelemetryReconnect && _postReconnectSubscribeRequested)
        {
            _postReconnectSubscribeRequested = false;
            FinishAfterPostReconnectTraffic();
            return;
        }

        if (_phase != Phase.Subscribe)
            return;

        EmitStepOk("subscribe", new Dictionary<string, object?>
        {
            ["synchronized"] = new[] { "smoke_test" },
        });

        _telemetryBeforeTraffic = CaptureTelemetrySnapshot();
        StartPhase(Phase.InvokeReducer);
        InvokeReducerForCurrentValue();
    }

    private void OnSubscriptionFailed(SubscriptionFailedEvent failedEvent)
    {
        if (_finished)
            return;

        EmitError("subscribe", "SubscriptionFailed signal fired");
        Finish(pass: false);
    }

    private void OnReducerCallSucceeded(ReducerCallResult result)
    {
        if (_finished || result == null || result.ReducerName != "ping_insert")
            return;

        if (_phase != Phase.InvokeReducer)
            return;

        _lastReducerResult = result;
        EmitStepOk("invoke_reducer", new Dictionary<string, object?>
        {
            ["reducer"] = result.ReducerName,
            ["invocation_id"] = result.InvocationId,
            ["reducer_round_trip_milliseconds"] = (result.CompletedAt - result.CalledAt).TotalMilliseconds,
        });

        ResetObservationState();
        StartPhase(Phase.ObserveRowChange);
        CheckTypedTableHandle();
        CheckGetRows();
        TryCompleteObservation();
    }

    private void OnReducerCallFailed(ReducerCallError error)
    {
        if (_finished || error == null)
            return;

        EmitError(
            StepName(_phase),
            $"{error.ReducerName}: {error.ErrorMessage} ({error.FailureCategory})");
        Finish(pass: false);
    }

    private void OnRowChanged(RowChangedEvent rowEvent)
    {
        if (_finished || rowEvent == null)
            return;

        if (rowEvent.TableName != "SmokeTest" || rowEvent.ChangeType != RowChangeType.Insert)
            return;

        var value = ExtractRowValue(rowEvent.NewRow);
        if (value == null)
            return;

        _observedInsertValues.Add(value);

        if (value != _expectedValue)
            return;

        _sawRowChangedEvent = true;
        CheckTypedTableHandle();
        CheckGetRows();
        TryCompleteObservation();
    }

    private void SubscribeCurrentSession()
    {
        try
        {
            _client!.Subscribe(new[] { "SELECT * FROM smoke_test" });
        }
        catch (Exception ex)
        {
            EmitError("subscribe", ex.GetType().Name + ": " + ex.Message);
            Finish(pass: false);
        }
    }

    private void InvokeReducerForCurrentValue()
    {
        try
        {
            _client!.InvokeReducer(new Reducer.PingInsert(_expectedValue));
        }
        catch (Exception ex)
        {
            EmitError("invoke_reducer", ex.GetType().Name + ": " + ex.Message);
            Finish(pass: false);
        }
    }

    private void ResetObservationState()
    {
        _sawGetRows = false;
        _sawTypedTableHandle = false;
        // Seed from the buffered insert set — the RowChanged signal for the
        // current _expectedValue may already have fired during InvokeReducer
        // because the SDK delivers row-change callbacks before the matching
        // ReducerCallSucceeded for the same TransactionUpdate.
        _sawRowChangedEvent = _observedInsertValues.Contains(_expectedValue);
    }

    private void CheckTypedTableHandle()
    {
        if (_sawTypedTableHandle || _client == null)
            return;

        try
        {
            var db = _client.GetDb<RemoteTables>();
            if (db == null || db.SmokeTest.Count == 0)
                return;

            foreach (var row in db.SmokeTest.Iter())
            {
                if (row.Value == _expectedValue)
                {
                    _sawTypedTableHandle = true;
                    break;
                }
            }
        }
        catch (Exception ex)
        {
            EmitError("observe_row_change", "typed table handle threw: " + ex.Message);
            Finish(pass: false);
        }
    }

    private void CheckGetRows()
    {
        if (_sawGetRows || _client == null)
            return;

        try
        {
            foreach (var row in _client.GetRows("SmokeTest"))
            {
                if (ExtractRowValue(row) == _expectedValue)
                {
                    _sawGetRows = true;
                    break;
                }
            }
        }
        catch (Exception ex)
        {
            EmitError("observe_row_change", "GetRows threw: " + ex.Message);
            Finish(pass: false);
        }
    }

    private void TryCompleteObservation()
    {
        if (_finished || _phase != Phase.ObserveRowChange)
            return;

        if (!_sawTypedTableHandle || !_sawGetRows || !_sawRowChangedEvent)
            return;

        EmitStepOk("observe_row_change", new Dictionary<string, object?>
        {
            ["via"] = new[] { "typed_table_handle", "get_rows", "row_changed_event" },
            ["value"] = _expectedValue,
        });

        StartPhase(Phase.ReadTelemetry);
        EmitTelemetryRead();
    }

    private void EmitTelemetryRead()
    {
        var snapshot = CaptureTelemetrySnapshot();
        if (_telemetryBeforeTraffic == null)
        {
            EmitError("read_telemetry", "telemetry baseline was never captured before reducer traffic.");
            Finish(pass: false);
            return;
        }

        if (_lastReducerResult == null)
        {
            EmitError("read_telemetry", "missing ReducerCallSucceeded result needed for RTT validation.");
            Finish(pass: false);
            return;
        }

        var reducerResultRtt = (_lastReducerResult.CompletedAt - _lastReducerResult.CalledAt).TotalMilliseconds;
        var telemetryDelta = Math.Abs(snapshot.LastReducerRoundTripMilliseconds - reducerResultRtt);

        if (snapshot.MessagesSent <= _telemetryBeforeTraffic.MessagesSent ||
            snapshot.BytesSent <= _telemetryBeforeTraffic.BytesSent ||
            snapshot.MessagesReceived < _telemetryBeforeTraffic.MessagesReceived ||
            snapshot.BytesReceived < _telemetryBeforeTraffic.BytesReceived)
        {
            EmitError(
                "read_telemetry",
                "real session traffic must increase telemetry counters after subscribe + reducer + row-change flow.");
            Finish(pass: false);
            return;
        }

        if (snapshot.LastReducerRoundTripMilliseconds <= 0 || reducerResultRtt <= 0 || telemetryDelta > 250.0)
        {
            EmitError(
                "read_telemetry",
                $"telemetry RTT must be positive and agree with ReducerCallSucceeded timing. telemetry={snapshot.LastReducerRoundTripMilliseconds:F3}ms result={reducerResultRtt:F3}ms.");
            Finish(pass: false);
            return;
        }

        if (!snapshot.BytesSentProven)
        {
            EmitError(
                "read_telemetry",
                "bytes_sent_proven was false. Outbound byte validation must fail loudly when runtime proof is unavailable.");
            Finish(pass: false);
            return;
        }

        // The Reducers category (index 0) must populate after a real reducer round-trip.
        // SampleCount reflects the completed ping_insert call; latency min/max are finite and
        // >= 0 (windowed — may read 0.0 if the last 1s saw no traffic). Categories that stay
        // empty on the 2.1.0 client are recorded in the payload, not asserted on.
        var reducers = snapshot.Categories[0];
        if (reducers.SampleCount < 1 ||
            reducers.MinMs < 0 || reducers.MaxMs < 0 ||
            double.IsNaN(reducers.MinMs) || double.IsNaN(reducers.MaxMs) ||
            double.IsInfinity(reducers.MinMs) || double.IsInfinity(reducers.MaxMs))
        {
            EmitError(
                "read_telemetry",
                $"reducers category must populate after real reducer traffic: sample_count={reducers.SampleCount} min_ms={reducers.MinMs:F3} max_ms={reducers.MaxMs:F3}.");
            Finish(pass: false);
            return;
        }

        EmitStepOk("read_telemetry", snapshot.ToPayload(includeMonitorComparison: true, includeSource: true));

        StartPhase(Phase.Disconnect);
        _expectDisconnectForReconnect = true;
        _client!.Disconnect();
    }

    private void EmitReconnectTelemetry()
    {
        var snapshot = CaptureTelemetrySnapshot();
        if (_telemetryBeforeTraffic == null)
        {
            EmitError("read_telemetry_reconnect", "telemetry baseline missing during reconnect validation.");
            Finish(pass: false);
            return;
        }

        if (snapshot.LastReducerRoundTripMilliseconds != 0)
        {
            EmitError("read_telemetry_reconnect", "reconnect must clear the last reducer RTT.");
            Finish(pass: false);
            return;
        }

        if (snapshot.MessagesReceivedPerSecond != 0 ||
            snapshot.MessagesSentPerSecond != 0 ||
            snapshot.BytesReceivedPerSecond != 0 ||
            snapshot.BytesSentPerSecond != 0)
        {
            EmitError("read_telemetry_reconnect", "reconnect must clear the public per-second telemetry fields.");
            Finish(pass: false);
            return;
        }

        if (snapshot.MessagesSent > _telemetryBeforeTraffic.MessagesSent ||
            snapshot.MessagesReceived > _telemetryBeforeTraffic.MessagesReceived ||
            snapshot.BytesSent > _telemetryBeforeTraffic.BytesSent ||
            snapshot.BytesReceived > _telemetryBeforeTraffic.BytesReceived)
        {
            EmitError("read_telemetry_reconnect", "reconnect telemetry carried over counts from the prior session.");
            Finish(pass: false);
            return;
        }

        EmitStepOk("read_telemetry_reconnect", snapshot.ToPayload(includeMonitorComparison: true, includeSource: true));

        // Prove outbound-byte tracking survives the disconnect/reconnect cycle by
        // exercising the public subscribe path once more and re-capturing the
        // telemetry source for the done event. Test harness expects the
        // read_telemetry_reconnect step to observe an empty source (the session
        // was just reset) AND the done event to observe the SDK-BSATN source
        // (because traffic after reconnect still flows through the pinned
        // ClientMessage.BSATN serializer).
        _postReconnectSubscribeRequested = true;
        try
        {
            _client!.Subscribe(new[] { "SELECT * FROM smoke_test" });
        }
        catch (Exception ex)
        {
            EmitError("read_telemetry_reconnect", "post-reconnect subscribe threw: " + ex.Message);
            Finish(pass: false);
        }
    }

    private void FinishAfterPostReconnectTraffic()
    {
        var finalSnapshot = CaptureTelemetrySnapshot();
        Finish(pass: true, new Dictionary<string, object?>
        {
            ["stable_telemetry_instance_reused"] = _stableTelemetryReusedAfterReconnect,
            ["bytes_sent_source"] = finalSnapshot.BytesSentSource,
            ["bytes_sent_proven"] = finalSnapshot.BytesSentProven,
        });
    }

    private TelemetrySnapshot CaptureTelemetrySnapshot()
    {
        // Single shared CurrentTelemetry evaluation. Every scalar that participates in the
        // monitor_matches_public_surface parity gate for the four Reducers/* monitors is read
        // from THIS one ConnectionTelemetryStats reference (no second pull), so the sliding
        // 1-second windowed-latency reads and the mutating SampleCount/PendingRequests counters
        // cannot drift between the "monitor" operand and the "public surface" operand.
        // See the 2026-05-28 spec amendment (finding 1): two separate CurrentTelemetry reads
        // each re-evaluate GetMinMaxTimes(1) at a different wall-clock instant and would flake
        // the hard parity boolean whenever a window rolls or an in-flight request completes.
        var telemetry = _client!.CurrentTelemetry;

        // The Connection/* and per-second monitors are stable counters/derived rates, safe to
        // read through Performance.GetCustomMonitor. The four Reducers/* monitor-equivalents are
        // sourced from `telemetry` above (same single snapshot) rather than from a second pull.
        var monitorValues = new Dictionary<string, double>
        {
            ["GodotSpacetime/Connection/MessagesSent"] = ReadMonitor(MessagesSentMonitorId),
            ["GodotSpacetime/Connection/MessagesReceived"] = ReadMonitor(MessagesReceivedMonitorId),
            ["GodotSpacetime/Connection/BytesSent"] = ReadMonitor(BytesSentMonitorId),
            ["GodotSpacetime/Connection/BytesReceived"] = ReadMonitor(BytesReceivedMonitorId),
            ["GodotSpacetime/Connection/UptimeSeconds"] = ReadMonitor(UptimeSecondsMonitorId),
            ["GodotSpacetime/Reducers/LastRoundTripMilliseconds"] = ReadMonitor(LastReducerRoundTripMonitorId),
            ["GodotSpacetime/Connection/MessagesReceivedPerSecond"] = ReadMonitor(MessagesReceivedPerSecondMonitorId),
            ["GodotSpacetime/Connection/MessagesSentPerSecond"] = ReadMonitor(MessagesSentPerSecondMonitorId),
            ["GodotSpacetime/Connection/BytesReceivedPerSecond"] = ReadMonitor(BytesReceivedPerSecondMonitorId),
            ["GodotSpacetime/Connection/BytesSentPerSecond"] = ReadMonitor(BytesSentPerSecondMonitorId),
            // Reducers/* monitor-equivalents derived from the single shared snapshot — these mirror
            // the allocation-free Math.Max(0, CurrentTelemetry.Reducers.*) callables registered on
            // SpacetimeClient, but read from `telemetry` so the parity gate compares like-for-like.
            ["GodotSpacetime/Reducers/LatencyMinMs"] = Math.Max(0, telemetry.Reducers.MinMs),
            ["GodotSpacetime/Reducers/LatencyMaxMs"] = Math.Max(0, telemetry.Reducers.MaxMs),
            ["GodotSpacetime/Reducers/SampleCount"] = Math.Max(0, telemetry.Reducers.SampleCount),
            ["GodotSpacetime/Reducers/PendingRequests"] = Math.Max(0, telemetry.Reducers.PendingRequests),
        };

        // Capture all 9 categories' six scalars in the fixed CategoryNames order so the
        // read_telemetry / read_telemetry_reconnect payloads record empirical per-tracker
        // population (which trackers fill on the live 2.1.0 client vs. stay empty). These read
        // from the SAME `telemetry` reference used for the Reducers/* monitor-equivalents above.
        var categories = new[]
        {
            telemetry.Reducers,
            telemetry.Procedures,
            telemetry.Subscriptions,
            telemetry.OneOffQueries,
            telemetry.AllReducers,
            telemetry.ParseMessageQueue,
            telemetry.ParseMessage,
            telemetry.ApplyMessageQueue,
            telemetry.ApplyMessage,
        };
        var categoryReadings = new CategorySnapshot[categories.Length];
        for (var index = 0; index < categories.Length; index++)
        {
            var category = categories[index];
            categoryReadings[index] = new CategorySnapshot(
                category.MinMs,
                category.MaxMs,
                category.AllTimeMinMs,
                category.AllTimeMaxMs,
                category.SampleCount,
                category.PendingRequests);
        }

        return new TelemetrySnapshot(
            telemetry.MessagesSent,
            telemetry.MessagesReceived,
            telemetry.BytesSent,
            telemetry.BytesReceived,
            telemetry.ConnectionUptimeSeconds,
            telemetry.LastReducerRoundTripMilliseconds,
            telemetry.MessagesReceivedPerSecond,
            telemetry.MessagesSentPerSecond,
            telemetry.BytesReceivedPerSecond,
            telemetry.BytesSentPerSecond,
            monitorValues,
            categoryReadings,
            _client.TelemetryBytesSentSource,
            _client.TelemetryBytesSentProven);
    }

    private static bool IsResetSnapshot(TelemetrySnapshot snapshot)
    {
        foreach (var category in snapshot.Categories)
        {
            if (category.MinMs != 0 || category.MaxMs != 0 ||
                category.AllTimeMinMs != 0 || category.AllTimeMaxMs != 0 ||
                category.SampleCount != 0 || category.PendingRequests != 0)
            {
                return false;
            }
        }

        return snapshot.MessagesSent == 0 &&
               snapshot.MessagesReceived == 0 &&
               snapshot.BytesSent == 0 &&
               snapshot.BytesReceived == 0 &&
               snapshot.ConnectionUptimeSeconds == 0 &&
               snapshot.LastReducerRoundTripMilliseconds == 0 &&
               snapshot.MessagesReceivedPerSecond == 0 &&
               snapshot.MessagesSentPerSecond == 0 &&
               snapshot.BytesReceivedPerSecond == 0 &&
               snapshot.BytesSentPerSecond == 0;
    }

    private static double ReadMonitor(StringName monitorId)
    {
        var raw = Performance.GetCustomMonitor(monitorId);
        var text = raw.ToString();
        return double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out var parsed)
            ? Math.Max(0, parsed)
            : 0.0;
    }

    private void EmitStepOk(string name, Dictionary<string, object?>? extra)
    {
        var payload = new Dictionary<string, object?>
        {
            ["event"] = "step",
            ["name"] = name,
            ["status"] = "ok",
            ["elapsed_ms"] = (int)((Time.GetTicksMsec() / 1000.0 - _phaseStartedAt) * 1000),
        };

        if (extra != null)
        {
            foreach (var kv in extra)
                payload[kv.Key] = kv.Value;
        }

        WriteJsonLine(payload);
    }

    private void EmitError(string name, string reason)
    {
        WriteJsonLine(new Dictionary<string, object?>
        {
            ["event"] = "step",
            ["name"] = name,
            ["status"] = "error",
            ["reason"] = reason,
        });
    }

    private static void WriteJsonLine(object payload)
    {
        try
        {
            var json = JsonSerializer.Serialize(payload);
            Console.WriteLine("E2E-EVENT " + json);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("TelemetrySmokeRunner: failed to serialize event: " + ex.Message);
        }
    }

    private void Finish(bool pass, Dictionary<string, object?>? extra = null)
    {
        if (_finished)
            return;

        _finished = true;
        _phase = Phase.Done;

        var payload = new Dictionary<string, object?>
        {
            ["event"] = "done",
            ["status"] = pass ? "pass" : "fail",
        };

        if (extra != null)
        {
            foreach (var kv in extra)
                payload[kv.Key] = kv.Value;
        }

        WriteJsonLine(payload);
        Quit(pass ? 0 : 1);
    }

    private void Quit(int code)
    {
        var tree = GetTree();
        if (tree != null)
        {
            tree.Quit(code);
        }
        else
        {
            Environment.Exit(code);
        }
    }

    private static string? ExtractRowValue(object? row)
    {
        if (row == null)
            return null;

        if (row is SmokeTest typed)
            return typed.Value;

        var field = row.GetType().GetField("Value");
        if (field != null)
            return field.GetValue(row) as string;

        var property = row.GetType().GetProperty("Value");
        return property?.GetValue(row) as string;
    }

    private static string NormalizeHost(string host)
    {
        if (host.StartsWith("http://", StringComparison.OrdinalIgnoreCase))
            return "ws://" + host.Substring("http://".Length);

        if (host.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
            return "wss://" + host.Substring("https://".Length);

        return host;
    }

    private static string StepName(Phase phase) => phase switch
    {
        Phase.Connect => "connect",
        Phase.Subscribe => "subscribe",
        Phase.InvokeReducer => "invoke_reducer",
        Phase.ObserveRowChange => "observe_row_change",
        Phase.ReadTelemetry => "read_telemetry",
        Phase.Disconnect => "disconnect",
        Phase.Reconnect => "connect_reconnect",
        Phase.ReadTelemetryReconnect => "read_telemetry_reconnect",
        _ => "unknown",
    };

    private sealed record CategorySnapshot(
        double MinMs,
        double MaxMs,
        double AllTimeMinMs,
        double AllTimeMaxMs,
        long SampleCount,
        long PendingRequests)
    {
        internal Dictionary<string, object?> ToPayload() => new()
        {
            ["min_ms"] = MinMs,
            ["max_ms"] = MaxMs,
            ["all_time_min_ms"] = AllTimeMinMs,
            ["all_time_max_ms"] = AllTimeMaxMs,
            ["sample_count"] = SampleCount,
            ["pending_requests"] = PendingRequests,
        };
    }

    private sealed record TelemetrySnapshot(
        long MessagesSent,
        long MessagesReceived,
        long BytesSent,
        long BytesReceived,
        double ConnectionUptimeSeconds,
        double LastReducerRoundTripMilliseconds,
        double MessagesReceivedPerSecond,
        double MessagesSentPerSecond,
        double BytesReceivedPerSecond,
        double BytesSentPerSecond,
        IReadOnlyDictionary<string, double> PerformanceMonitors,
        IReadOnlyList<CategorySnapshot> Categories,
        string BytesSentSource,
        bool BytesSentProven)
    {
        internal Dictionary<string, object?> ToPayload(bool includeMonitorComparison, bool includeSource = false)
        {
            var categoriesPayload = new Dictionary<string, object?>();
            for (var index = 0; index < Categories.Count; index++)
                categoriesPayload[CategoryNames[index]] = Categories[index].ToPayload();

            var payload = new Dictionary<string, object?>
            {
                ["categories"] = categoriesPayload,
                ["messages_sent"] = MessagesSent,
                ["messages_received"] = MessagesReceived,
                ["bytes_sent"] = BytesSent,
                ["bytes_received"] = BytesReceived,
                ["connection_uptime_seconds"] = ConnectionUptimeSeconds,
                ["last_reducer_round_trip_milliseconds"] = LastReducerRoundTripMilliseconds,
                ["messages_received_per_second"] = MessagesReceivedPerSecond,
                ["messages_sent_per_second"] = MessagesSentPerSecond,
                ["bytes_received_per_second"] = BytesReceivedPerSecond,
                ["bytes_sent_per_second"] = BytesSentPerSecond,
                ["performance_monitors"] = PerformanceMonitors,
                ["bytes_sent_proven"] = BytesSentProven,
            };

            if (includeSource)
                payload["bytes_sent_source"] = BytesSentSource;

            if (includeMonitorComparison)
            {
                // Hard parity gate (asserted True by the live lane). The four Reducers/* monitor
                // operands and the Categories[0] snapshot operands are sourced from the SAME single
                // CurrentTelemetry evaluation in CaptureTelemetrySnapshot, so SampleCount and
                // PendingRequests are exact (no in-flight request can tick between two pulls).
                //
                // The two WINDOWED latency monitors (LatencyMinMs/LatencyMaxMs) are deliberately
                // EXCLUDED from this hard boolean and recorded as informational fields below: the
                // 1-second GetMinMaxTimes window can legitimately read 0.0 when the last sample has
                // aged past the boundary, so a 0.0 monitor read against a populated snapshot (or
                // vice-versa) must NOT fail the gate (2026-05-28 amendment, finding 1).
                payload["monitor_matches_public_surface"] =
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Connection/MessagesSent"] - MessagesSent) < 0.001 &&
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Connection/MessagesReceived"] - MessagesReceived) < 0.001 &&
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Connection/BytesSent"] - BytesSent) < 0.001 &&
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Connection/BytesReceived"] - BytesReceived) < 0.001 &&
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Connection/UptimeSeconds"] - ConnectionUptimeSeconds) < 0.250 &&
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Reducers/LastRoundTripMilliseconds"] - LastReducerRoundTripMilliseconds) < 0.250 &&
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Connection/MessagesReceivedPerSecond"] - MessagesReceivedPerSecond) < 0.001 &&
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Connection/MessagesSentPerSecond"] - MessagesSentPerSecond) < 0.001 &&
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Connection/BytesReceivedPerSecond"] - BytesReceivedPerSecond) < 0.001 &&
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Connection/BytesSentPerSecond"] - BytesSentPerSecond) < 0.001 &&
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Reducers/SampleCount"] - Math.Max(0, Categories[0].SampleCount)) < 0.001 &&
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Reducers/PendingRequests"] - Math.Max(0, Categories[0].PendingRequests)) < 0.001;

                // Informational: windowed-latency monitor-vs-snapshot deltas. Recorded for the Dev
                // Notes / observability of the live run; intentionally NOT part of the hard gate.
                payload["reducers_latency_min_monitor_delta"] =
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Reducers/LatencyMinMs"] - Math.Max(0, Categories[0].MinMs));
                payload["reducers_latency_max_monitor_delta"] =
                    Math.Abs(PerformanceMonitors["GodotSpacetime/Reducers/LatencyMaxMs"] - Math.Max(0, Categories[0].MaxMs));
            }

            return payload;
        }
    }
}

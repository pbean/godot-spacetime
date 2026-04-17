using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Godot;
using GodotSpacetime.Connection;
using GodotSpacetime.Runtime.Connection;

namespace GodotSpacetime.IntegrationTests;

// Drives ConnectionTelemetryCollector directly so reconnect/session-boundary
// behavior can be exercised without a live SpacetimeDB runtime.
public partial class TelemetryCollectorHardeningRunner : Node
{
    private const string EventPrefix = "E2E-EVENT ";
    private const long SessionOneId = 1;
    private const long SessionTwoId = 2;

    private readonly ConnectionTelemetryCollector _collector = new();
    // Captures taken at different lifecycle points: pre-session, post-first-StartSession,
    // and post-second-StartSession (which implicitly Reset). If the collector ever reallocates
    // its stable stats object across any of these transitions, ReferenceEquals against the
    // current telemetry will fail for at least one capture and the CaptureSnapshot check breaks.
    private readonly List<ConnectionTelemetryStats> _capturedStableReferences = new();
    private ConnectionTelemetryStats? _stableTelemetryReference;
    private bool _finished;

    public override void _Ready()
    {
        _ = RunScenarioAsync();
    }

    private async Task RunScenarioAsync()
    {
        try
        {
            _stableTelemetryReference = _collector.CurrentTelemetry;
            _capturedStableReferences.Add(_stableTelemetryReference);

            _collector.StartSession(SessionOneId);
            _capturedStableReferences.Add(_collector.CurrentTelemetry);
            _collector.InitializeTrackerBaseline(SessionOneId, 0, 0);
            EmitStepOk("session_1_started", CaptureSnapshot().ToPayload(includeStableTelemetryReference: true));

            _collector.RecordOutboundMessage(SessionOneId, 32);
            _collector.RecordInboundMessage(SessionOneId, 64);
            await DelayAsync(1.25);

            var sessionOneRates = CaptureSnapshot();
            if (sessionOneRates.MessagesSent != 1 ||
                sessionOneRates.MessagesReceived != 1 ||
                sessionOneRates.BytesSent != 32 ||
                sessionOneRates.BytesReceived != 64 ||
                sessionOneRates.ConnectionUptimeSeconds < 1.0 ||
                sessionOneRates.MessagesReceivedPerSecond <= 0 ||
                sessionOneRates.MessagesSentPerSecond <= 0 ||
                sessionOneRates.BytesReceivedPerSecond <= 0 ||
                sessionOneRates.BytesSentPerSecond <= 0)
            {
                EmitError("session_1_rates", "session 1 must refresh monotonic uptime and per-second counters after the 1-second boundary.");
                Finish(pass: false);
                return;
            }

            EmitStepOk("session_1_rates", sessionOneRates.ToPayload(includeStableTelemetryReference: true));

            _collector.StartSession(SessionTwoId);
            _capturedStableReferences.Add(_collector.CurrentTelemetry);
            _collector.InitializeTrackerBaseline(SessionTwoId, 100, 200);
            _collector.SyncTrackerCounts(SessionTwoId, 100, 200);

            var sessionTwoReset = CaptureSnapshot();
            if (!sessionTwoReset.IsZeroed())
            {
                EmitError("session_2_reset", "starting a new session must keep telemetry zeroed when only stale tracker totals are present.");
                Finish(pass: false);
                return;
            }

            EmitStepOk("session_2_reset", sessionTwoReset.ToPayload(includeStableTelemetryReference: true));

            var staleCalledAt = DateTimeOffset.UtcNow;
            _collector.RecordInboundMessage(SessionOneId, 8);
            _collector.RecordOutboundMessage(SessionOneId, 16);
            _collector.RecordReducerRoundTrip(SessionOneId, staleCalledAt, staleCalledAt.AddMilliseconds(50));
            _collector.SyncTrackerCounts(SessionOneId, 101, 201);

            var oldSessionIgnored = CaptureSnapshot();
            if (!oldSessionIgnored.IsZeroed())
            {
                EmitError("old_session_callbacks_ignored", "late callbacks from the prior session must not repopulate reset telemetry.");
                Finish(pass: false);
                return;
            }

            EmitStepOk("old_session_callbacks_ignored", oldSessionIgnored.ToPayload(includeStableTelemetryReference: true));

            var activeCalledAt = DateTimeOffset.UtcNow;
            _collector.RecordOutboundMessage(SessionTwoId, 24);
            _collector.RecordInboundMessage(SessionTwoId, 40);
            _collector.SyncTrackerCounts(SessionTwoId, 101, 201);
            _collector.RecordReducerRoundTrip(SessionTwoId, activeCalledAt, activeCalledAt.AddMilliseconds(50));
            await DelayAsync(1.25);

            var sessionTwoTraffic = CaptureSnapshot();
            if (sessionTwoTraffic.MessagesSent != 1 ||
                sessionTwoTraffic.MessagesReceived != 1 ||
                sessionTwoTraffic.BytesSent != 24 ||
                sessionTwoTraffic.BytesReceived != 40 ||
                sessionTwoTraffic.LastReducerRoundTripMilliseconds <= 0 ||
                sessionTwoTraffic.MessagesReceivedPerSecond <= 0 ||
                sessionTwoTraffic.MessagesSentPerSecond <= 0 ||
                sessionTwoTraffic.BytesReceivedPerSecond <= 0 ||
                sessionTwoTraffic.BytesSentPerSecond <= 0)
            {
                EmitError("session_2_traffic", "new-session traffic must survive tracker rebasing and refresh the per-second fields.");
                Finish(pass: false);
                return;
            }

            EmitStepOk("session_2_traffic", sessionTwoTraffic.ToPayload(includeStableTelemetryReference: true));
            Finish(pass: true, new Dictionary<string, object?>
            {
                ["stable_telemetry_instance_reused"] = sessionTwoTraffic.StableTelemetryInstanceReused,
            });
        }
        catch (Exception ex)
        {
            EmitError("runtime", ex.GetType().Name + ": " + ex.Message);
            Finish(pass: false);
        }
    }

    private async Task DelayAsync(double seconds)
    {
        var tree = GetTree();
        if (tree != null)
        {
            await ToSignal(tree.CreateTimer(seconds), SceneTreeTimer.SignalName.Timeout);
            return;
        }

        await Task.Delay(TimeSpan.FromSeconds(seconds));
    }

    private TelemetrySnapshot CaptureSnapshot()
    {
        var telemetry = _collector.CurrentTelemetry;
        // stableTelemetryInstanceReused is true only when every prior capture (pre-session,
        // post-first-StartSession, post-second-StartSession as they accumulate) still
        // ReferenceEquals the current telemetry. This catches a regression that reallocates
        // _stats on any session transition, not just a regression in Reset.
        var instanceReused = ReferenceEquals(_stableTelemetryReference, telemetry);
        foreach (var captured in _capturedStableReferences)
        {
            if (!ReferenceEquals(captured, telemetry))
            {
                instanceReused = false;
                break;
            }
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
            instanceReused);
    }

    private void EmitStepOk(string name, Dictionary<string, object?> payload)
    {
        payload["event"] = "step";
        payload["name"] = name;
        payload["status"] = "ok";
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

    private void Finish(bool pass, Dictionary<string, object?>? extra = null)
    {
        // A post-pass failure (exception raised after Finish(pass:true) already queued Quit(0))
        // must override and exit non-zero, otherwise a late crash is silently reported as success.
        if (_finished)
        {
            if (!pass)
            {
                WriteJsonLine(new Dictionary<string, object?>
                {
                    ["event"] = "done",
                    ["status"] = "fail",
                    ["reason"] = "post_pass_failure",
                });
                System.Environment.Exit(1);
            }
            return;
        }

        _finished = true;
        var payload = new Dictionary<string, object?>
        {
            ["event"] = "done",
            ["status"] = pass ? "pass" : "fail",
        };

        if (extra != null)
        {
            foreach (var entry in extra)
                payload[entry.Key] = entry.Value;
        }

        WriteJsonLine(payload);
        var tree = GetTree();
        if (tree != null)
            tree.Quit(pass ? 0 : 1);
        else
            System.Environment.Exit(pass ? 0 : 1);
    }

    private static void WriteJsonLine(object payload)
    {
        try
        {
            Console.WriteLine(EventPrefix + JsonSerializer.Serialize(payload));
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("TelemetryCollectorHardeningRunner: failed to serialize event: " + ex.Message);
        }
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
        bool StableTelemetryInstanceReused)
    {
        internal bool IsZeroed()
        {
            return MessagesSent == 0 &&
                   MessagesReceived == 0 &&
                   BytesSent == 0 &&
                   BytesReceived == 0 &&
                   LastReducerRoundTripMilliseconds == 0 &&
                   MessagesReceivedPerSecond == 0 &&
                   MessagesSentPerSecond == 0 &&
                   BytesReceivedPerSecond == 0 &&
                   BytesSentPerSecond == 0;
        }

        internal Dictionary<string, object?> ToPayload(bool includeStableTelemetryReference)
        {
            var payload = new Dictionary<string, object?>
            {
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
            };

            if (includeStableTelemetryReference)
                payload["stable_telemetry_instance_reused"] = StableTelemetryInstanceReused;

            return payload;
        }
    }
}

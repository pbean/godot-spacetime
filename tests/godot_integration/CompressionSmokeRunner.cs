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

namespace GodotSpacetime.IntegrationTests;

// Drives SpacetimeClient through connect -> subscribe -> invoke-reducer ->
// observe-row-change against a real runtime while varying the requested
// compression mode. The contract is enforced by
// tests/test_story_9_1_message_compression_integration.py.
public partial class CompressionSmokeRunner : Node
{
    private enum Step
    {
        None,
        Connect,
        Subscribe,
        InvokeReducer,
        ObserveRowChange,
        Done,
    }

    private string _host = "";
    private string _moduleName = "";
    private string _expectedValue = "";
    private double _stepTimeoutSeconds = 30.0;
    private MessageCompressionMode _requestedCompressionMode = MessageCompressionMode.None;
    private MessageCompressionMode _effectiveCompressionMode = MessageCompressionMode.None;

    private SpacetimeClient? _client;
    private Step _currentStep = Step.None;
    private double _stepStartedAt;
    private bool _sawGetRows;
    private bool _sawTypedTableHandle;
    private bool _sawRowChangedEvent;
    private bool _finished;

    public override void _Ready()
    {
        try
        {
            _host = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_HOST") ?? "";
            _moduleName = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_MODULE") ?? "";
            _expectedValue = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_VALUE") ?? "";
            var compression = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_COMPRESSION") ?? "";

            var timeoutStr = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_STEP_TIMEOUT") ?? "30";
            if (double.TryParse(
                    timeoutStr,
                    NumberStyles.Float,
                    CultureInfo.InvariantCulture,
                    out var parsed))
            {
                _stepTimeoutSeconds = Math.Max(1.0, parsed);
            }

            if (string.IsNullOrWhiteSpace(_host) ||
                string.IsNullOrWhiteSpace(_moduleName) ||
                string.IsNullOrWhiteSpace(_expectedValue) ||
                string.IsNullOrWhiteSpace(compression))
            {
                Console.Error.WriteLine(
                    "CompressionSmokeRunner: missing required env vars " +
                    "(SPACETIME_E2E_HOST, SPACETIME_E2E_MODULE, SPACETIME_E2E_VALUE, SPACETIME_E2E_COMPRESSION)");
                Quit(1);
                return;
            }

            _requestedCompressionMode = ParseCompressionMode(compression);
            _expectedValue = _expectedValue.Trim();

            var settings = new SpacetimeSettings
            {
                Host = NormalizeHost(_host.Trim()),
                Database = _moduleName.Trim(),
                CompressionMode = _requestedCompressionMode,
            };

            _client = new SpacetimeClient { Settings = settings };
            _client.ConnectionStateChanged += OnConnectionStateChanged;
            _client.SubscriptionApplied += OnSubscriptionApplied;
            _client.SubscriptionFailed += OnSubscriptionFailed;
            _client.ReducerCallSucceeded += OnReducerCallSucceeded;
            _client.ReducerCallFailed += OnReducerCallFailed;
            _client.RowChanged += OnRowChanged;
            AddChild(_client);

            StartStep(Step.Connect);
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
        if (_finished || _currentStep == Step.None || _currentStep == Step.Done)
            return;

        var now = Time.GetTicksMsec() / 1000.0;
        if ((now - _stepStartedAt) > _stepTimeoutSeconds)
        {
            EmitError(
                StepName(_currentStep),
                $"timed out after {_stepTimeoutSeconds:F1}s waiting for step completion");
            Finish(pass: false);
        }
    }

    private void StartStep(Step step)
    {
        _currentStep = step;
        _stepStartedAt = Time.GetTicksMsec() / 1000.0;
    }

    private void OnConnectionStateChanged(ConnectionStatus status)
    {
        if (_finished || status == null)
            return;

        _effectiveCompressionMode = status.ActiveCompressionMode;

        if (_currentStep == Step.Connect && status.State == ConnectionState.Connected)
        {
            EmitStepOk("connect", new Dictionary<string, object?>
            {
                ["description"] = status.Description,
                ["requested_compression_mode"] = _requestedCompressionMode.ToString(),
                ["effective_compression_mode"] = _effectiveCompressionMode.ToString(),
            });
            StartStep(Step.Subscribe);
            try
            {
                _client!.Subscribe(new[] { "SELECT * FROM smoke_test" });
            }
            catch (Exception ex)
            {
                EmitError("subscribe", ex.GetType().Name + ": " + ex.Message);
                Finish(pass: false);
            }
            return;
        }

        if (status.State == ConnectionState.Disconnected &&
            _currentStep != Step.None &&
            _currentStep != Step.Done)
        {
            EmitError(
                StepName(_currentStep),
                $"disconnected mid-flight: {status.Description}");
            Finish(pass: false);
        }
    }

    private void OnSubscriptionApplied(SubscriptionAppliedEvent appliedEvent)
    {
        if (_finished || _currentStep != Step.Subscribe)
            return;

        EmitStepOk("subscribe", new Dictionary<string, object?>
        {
            ["synchronized"] = new[] { "smoke_test" },
            ["requested_compression_mode"] = _requestedCompressionMode.ToString(),
            ["effective_compression_mode"] = _effectiveCompressionMode.ToString(),
        });
        StartStep(Step.InvokeReducer);
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

        if (_currentStep != Step.InvokeReducer)
            return;

        EmitStepOk("invoke_reducer", new Dictionary<string, object?>
        {
            ["reducer"] = result.ReducerName,
            ["invocation_id"] = result.InvocationId,
            ["requested_compression_mode"] = _requestedCompressionMode.ToString(),
            ["effective_compression_mode"] = _effectiveCompressionMode.ToString(),
        });
        StartStep(Step.ObserveRowChange);

        CheckTypedTableHandle();
        CheckGetRows();
        TryFinishObserveRowChange();
    }

    private void OnReducerCallFailed(ReducerCallError error)
    {
        if (_finished || error == null)
            return;

        EmitError(
            "invoke_reducer",
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
        if (value != _expectedValue)
            return;

        _sawRowChangedEvent = true;
        CheckTypedTableHandle();
        CheckGetRows();
        TryFinishObserveRowChange();
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

    private void TryFinishObserveRowChange()
    {
        if (_finished || _currentStep != Step.ObserveRowChange)
            return;

        if (_sawTypedTableHandle && _sawGetRows && _sawRowChangedEvent)
        {
            EmitStepOk("observe_row_change", new Dictionary<string, object?>
            {
                ["via"] = new[] { "typed_table_handle", "get_rows", "row_changed_event" },
                ["value"] = _expectedValue,
                ["requested_compression_mode"] = _requestedCompressionMode.ToString(),
                ["effective_compression_mode"] = _effectiveCompressionMode.ToString(),
            });
            Finish(pass: true);
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

        var prop = row.GetType().GetProperty("Value");
        return prop?.GetValue(row) as string;
    }

    private static string NormalizeHost(string host)
    {
        if (host.StartsWith("http://", StringComparison.OrdinalIgnoreCase))
            return "ws://" + host.Substring("http://".Length);

        if (host.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
            return "wss://" + host.Substring("https://".Length);

        return host;
    }

    private static MessageCompressionMode ParseCompressionMode(string raw)
    {
        return raw.Trim().ToLowerInvariant() switch
        {
            "none" => MessageCompressionMode.None,
            "gzip" => MessageCompressionMode.Gzip,
            "brotli" => MessageCompressionMode.Brotli,
            _ => throw new InvalidOperationException(
                $"Unsupported SPACETIME_E2E_COMPRESSION value '{raw}'. Expected None, Gzip, or Brotli."),
        };
    }

    private void EmitStepOk(string name, Dictionary<string, object?>? extra)
    {
        var payload = new Dictionary<string, object?>
        {
            ["event"] = "step",
            ["name"] = name,
            ["status"] = "ok",
            ["elapsed_ms"] = (int)((Time.GetTicksMsec() / 1000.0 - _stepStartedAt) * 1000),
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
            Console.Error.WriteLine("CompressionSmokeRunner: failed to serialize event: " + ex.Message);
        }
    }

    private void Finish(bool pass)
    {
        if (_finished)
            return;

        _finished = true;
        _currentStep = Step.Done;
        WriteJsonLine(new Dictionary<string, object?>
        {
            ["event"] = "done",
            ["status"] = pass ? "pass" : "fail",
        });
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
            System.Environment.Exit(code);
        }
    }

    private static string StepName(Step step) => step switch
    {
        Step.Connect => "connect",
        Step.Subscribe => "subscribe",
        Step.InvokeReducer => "invoke_reducer",
        Step.ObserveRowChange => "observe_row_change",
        _ => "unknown",
    };
}

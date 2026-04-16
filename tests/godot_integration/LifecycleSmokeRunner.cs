using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using Godot;
using GodotSpacetime;
using GodotSpacetime.Connection;
using GodotSpacetime.Reducers;
using GodotSpacetime.Subscriptions;
using SpacetimeDB.Types;

namespace GodotSpacetime.IntegrationTests;

// Drives SpacetimeClient through connect -> subscribe -> invoke-reducer ->
// observe-row-change against a real SpacetimeDB runtime, emitting a JSON-per-
// line event trail to the file named in SPACETIME_E2E_LOG. Used by
// tests/test_story_7_1_dynamic_lifecycle_integration.py. NEVER mocks any
// Internal/Platform/DotNet/ adapter — that is the entire point of this runner.
public partial class LifecycleSmokeRunner : Node
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

    private string _logPath = "";
    private string _host = "";
    private string _moduleName = "";
    private string _expectedValue = "";
    private double _stepTimeoutSeconds = 30.0;

    private SpacetimeClient? _client;
    private StreamWriter? _logWriter;
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
            _logPath = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_LOG") ?? "";
            _host = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_HOST") ?? "";
            _moduleName = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_MODULE") ?? "";
            _expectedValue = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_VALUE") ?? "";

            // Parse with InvariantCulture so `SPACETIME_E2E_STEP_TIMEOUT=0.5` works
            // regardless of the runner's current locale, and clamp to a positive
            // floor so a stray `0` or `-5` can't immediately time out every step.
            var timeoutStr = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_STEP_TIMEOUT") ?? "30";
            if (double.TryParse(
                    timeoutStr,
                    System.Globalization.NumberStyles.Float,
                    System.Globalization.CultureInfo.InvariantCulture,
                    out var parsed))
            {
                _stepTimeoutSeconds = Math.Max(1.0, parsed);
            }

            // SPACETIME_E2E_LOG is optional — events are always echoed to stdout as
            // "E2E-EVENT <json>" and stdout is the authoritative channel read by the
            // pytest wrapper. The file is a convenience for local debugging only.
            // Use IsNullOrWhiteSpace so a stray " " from shell templating is treated
            // as "unset" rather than as a valid (empty-looking) value.
            if (string.IsNullOrWhiteSpace(_host) ||
                string.IsNullOrWhiteSpace(_moduleName) ||
                string.IsNullOrWhiteSpace(_expectedValue))
            {
                Console.Error.WriteLine(
                    "LifecycleSmokeRunner: missing required env vars " +
                    "(SPACETIME_E2E_HOST, SPACETIME_E2E_MODULE, SPACETIME_E2E_VALUE)");
                Quit(1);
                return;
            }

            _host = _host.Trim();
            _moduleName = _moduleName.Trim();
            _expectedValue = _expectedValue.Trim();

            if (!string.IsNullOrWhiteSpace(_logPath))
            {
                var dir = Path.GetDirectoryName(_logPath);
                if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
                {
                    Directory.CreateDirectory(dir);
                }
                // Truncate on open — the log file is a per-run debug aid, never
                // an append-across-runs log. Avoids confusing stale events from
                // a previous run bleeding into the current run's output.
                _logWriter = new StreamWriter(_logPath, append: false) { AutoFlush = true };
            }

            // Adapter NormalizeUri defaults to wss:// for bare hosts; for a local HTTP
            // runtime we need plain ws://. Convert http(s):// to ws(s):// before passing
            // to SpacetimeSettings.Host so the runner works against a local dev instance.
            var cleanHost = _host;
            if (cleanHost.StartsWith("http://", StringComparison.OrdinalIgnoreCase))
            {
                cleanHost = "ws://" + cleanHost.Substring("http://".Length);
            }
            else if (cleanHost.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
            {
                cleanHost = "wss://" + cleanHost.Substring("https://".Length);
            }

            var settings = new SpacetimeSettings
            {
                Host = cleanHost,
                Database = _moduleName,
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

    public override void _Process(double delta)
    {
        if (_finished || _currentStep == Step.None || _currentStep == Step.Done)
        {
            return;
        }

        var now = Time.GetTicksMsec() / 1000.0;
        if ((now - _stepStartedAt) > _stepTimeoutSeconds)
        {
            EmitError(StepName(_currentStep),
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
        {
            return;
        }

        if (_currentStep == Step.Connect && status.State == ConnectionState.Connected)
        {
            EmitStepOk("connect", new Dictionary<string, object?>
            {
                ["description"] = status.Description,
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

        if (status.State == ConnectionState.Disconnected && _currentStep != Step.None && _currentStep != Step.Done)
        {
            EmitError(StepName(_currentStep),
                $"disconnected mid-flight: {status.Description}");
            Finish(pass: false);
        }
    }

    private void OnSubscriptionApplied(SubscriptionAppliedEvent appliedEvent)
    {
        if (_finished || _currentStep != Step.Subscribe)
        {
            return;
        }

        EmitStepOk("subscribe", new Dictionary<string, object?>
        {
            ["synchronized"] = new[] { "smoke_test" },
        });
        StartStep(Step.InvokeReducer);
        try
        {
            var args = new Reducer.PingInsert(_expectedValue);
            _client!.InvokeReducer(args);
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
        {
            return;
        }
        EmitError("subscribe", "SubscriptionFailed signal fired");
        Finish(pass: false);
    }

    private void OnReducerCallSucceeded(ReducerCallResult result)
    {
        if (_finished || result == null || result.ReducerName != "ping_insert")
        {
            return;
        }

        if (_currentStep != Step.InvokeReducer)
        {
            return;
        }

        EmitStepOk("invoke_reducer", new Dictionary<string, object?>
        {
            ["reducer"] = "ping_insert",
            ["value"] = _expectedValue,
            ["invocation_id"] = result.InvocationId,
        });
        StartStep(Step.ObserveRowChange);

        // The row may already be in cache by the time the success event fires
        // — poll the typed table-handle path and GetRows right away, then rely
        // on the RowChanged signal for the row-change event channel.
        CheckTypedTableHandle();
        CheckGetRows();
        TryFinishObserveRowChange();
    }

    private void OnReducerCallFailed(ReducerCallError err)
    {
        if (_finished || err == null)
        {
            return;
        }
        EmitError("invoke_reducer",
            $"{err.ReducerName}: {err.ErrorMessage} ({err.FailureCategory})");
        Finish(pass: false);
    }

    private void OnRowChanged(RowChangedEvent rowEvent)
    {
        if (_finished || rowEvent == null)
        {
            return;
        }
        if (rowEvent.TableName != "SmokeTest" || rowEvent.ChangeType != RowChangeType.Insert)
        {
            return;
        }

        var value = ExtractRowValue(rowEvent.NewRow);
        if (value != _expectedValue)
        {
            return;
        }

        _sawRowChangedEvent = true;
        CheckTypedTableHandle();
        CheckGetRows();
        TryFinishObserveRowChange();
    }

    private void CheckTypedTableHandle()
    {
        if (_sawTypedTableHandle || _client == null)
        {
            return;
        }
        try
        {
            var db = _client.GetDb<RemoteTables>();
            if (db == null || db.SmokeTest.Count == 0)
            {
                return;
            }

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
        {
            return;
        }
        try
        {
            // GetRows takes the PascalCase generated property name on RemoteTables,
            // not the snake_case SQL table name used in the subscribe query.
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
        {
            return;
        }
        if (_sawTypedTableHandle && _sawGetRows && _sawRowChangedEvent)
        {
            EmitStepOk("observe_row_change", new Dictionary<string, object?>
            {
                ["via"] = new[] { "typed_table_handle", "get_rows", "row_changed_event" },
                ["value"] = _expectedValue,
            });
            Finish(pass: true);
        }
    }

    private static string? ExtractRowValue(object? row)
    {
        if (row == null)
        {
            return null;
        }
        if (row is SmokeTest typed)
        {
            return typed.Value;
        }
        // Fallback for any adapter that wraps rows differently.
        var field = row.GetType().GetField("Value");
        if (field != null)
        {
            return field.GetValue(row) as string;
        }
        var prop = row.GetType().GetProperty("Value");
        return prop?.GetValue(row) as string;
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
            {
                payload[kv.Key] = kv.Value;
            }
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

    private void WriteJsonLine(object payload)
    {
        try
        {
            var json = JsonSerializer.Serialize(payload);
            _logWriter?.WriteLine(json);
            // Also echo to stdout in case the log file is unreadable from the wrapper.
            Console.WriteLine("E2E-EVENT " + json);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("LifecycleSmokeRunner: failed to serialize event: " + ex.Message);
        }
    }

    private void Finish(bool pass)
    {
        if (_finished)
        {
            return;
        }
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
        try
        {
            _logWriter?.Flush();
            _logWriter?.Dispose();
            _logWriter = null;
        }
        catch { }

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

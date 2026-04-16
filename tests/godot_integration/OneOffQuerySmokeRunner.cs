using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Godot;
using GodotSpacetime;
using GodotSpacetime.Connection;
using GodotSpacetime.Queries;
using GodotSpacetime.Reducers;
using SpacetimeDB.Types;

namespace GodotSpacetime.IntegrationTests;

// Drives SpacetimeClient through connect -> invoke-reducer -> one-off-query
// against a real SpacetimeDB runtime without applying a subscription for
// smoke_test. The contract is enforced by
// tests/test_story_7_4_one_off_query_integration.py.
public partial class OneOffQuerySmokeRunner : Node
{
    private enum Step
    {
        None,
        Connect,
        InvokeReducer,
        Query,
        ValidationFaults,
        NegativeQuery,
        Done,
    }

    private string _host = "";
    private string _moduleName = "";
    private string _expectedValue = "";
    private double _stepTimeoutSeconds = 30.0;

    private SpacetimeClient? _client;
    private Step _currentStep = Step.None;
    private double _stepStartedAt;
    private bool _finished;

    public override void _Ready()
    {
        try
        {
            _host = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_HOST") ?? "";
            _moduleName = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_MODULE") ?? "";
            _expectedValue = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_VALUE") ?? "";

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
                string.IsNullOrWhiteSpace(_expectedValue))
            {
                Console.Error.WriteLine(
                    "OneOffQuerySmokeRunner: missing required env vars " +
                    "(SPACETIME_E2E_HOST, SPACETIME_E2E_MODULE, SPACETIME_E2E_VALUE)");
                Quit(1);
                return;
            }

            var settings = new SpacetimeSettings
            {
                Host = NormalizeHost(_host.Trim()),
                Database = _moduleName.Trim(),
            };

            _expectedValue = _expectedValue.Trim();

            _client = new SpacetimeClient { Settings = settings };
            _client.ConnectionStateChanged += OnConnectionStateChanged;
            _client.ReducerCallSucceeded += OnReducerCallSucceeded;
            _client.ReducerCallFailed += OnReducerCallFailed;
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
        _client.ReducerCallSucceeded -= OnReducerCallSucceeded;
        _client.ReducerCallFailed -= OnReducerCallFailed;
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

    private void OnConnectionStateChanged(ConnectionStatus status)
    {
        if (_finished || status == null)
            return;

        if (_currentStep == Step.Connect && status.State == ConnectionState.Connected)
        {
            var initialSnapshot = CaptureCacheSnapshot("connect");
            AssertCacheEmpty(initialSnapshot, "connect");

            EmitStepOk("connect", new Dictionary<string, object?>
            {
                ["cache_rows"] = initialSnapshot.GetRowsCount,
                ["cache_count"] = initialSnapshot.HandleCount,
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
            ["value"] = _expectedValue,
        });

        StartStep(Step.Query);
        _ = ExecuteQueryStepsAsync();
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

    private async Task ExecuteQueryStepsAsync()
    {
        try
        {
            await RunPositiveQueryAsync();
            StartStep(Step.ValidationFaults);
            await RunValidationFaultsAsync();
            StartStep(Step.NegativeQuery);
            await RunNegativeQueryAsync();
            Finish(pass: true);
        }
        catch (Exception ex)
        {
            EmitError(StepName(_currentStep), ex.GetType().Name + ": " + ex.Message);
            Finish(pass: false);
        }
    }

    private async Task RunPositiveQueryAsync()
    {
        var before = CaptureCacheSnapshot("query");
        AssertCacheEmpty(before, "query-before");

        var sqlClause = $"WHERE value = '{EscapeSqlLiteral(_expectedValue)}'";
        var rows = await _client!.QueryAsync<SmokeTest>(sqlClause);
        if (rows.Length != 1)
        {
            throw new InvalidOperationException(
                $"Expected exactly one typed SmokeTest row, got {rows.Length}.");
        }

        if (rows[0].Value != _expectedValue)
        {
            throw new InvalidOperationException(
                $"Query returned value '{rows[0].Value}', expected '{_expectedValue}'.");
        }

        var after = CaptureCacheSnapshot("query");
        AssertCacheEmpty(after, "query-after");

        EmitStepOk("query", new Dictionary<string, object?>
        {
            ["sql_clause"] = sqlClause,
            ["returned_count"] = rows.Length,
            ["value"] = rows[0].Value,
            ["cache_rows_before"] = before.GetRowsCount,
            ["cache_count_before"] = before.HandleCount,
            ["cache_rows_after"] = after.GetRowsCount,
            ["cache_count_after"] = after.HandleCount,
            ["observed_via"] = new[] { "query_async" },
        });
    }

    private async Task RunValidationFaultsAsync()
    {
        var before = CaptureCacheSnapshot("validation_faults");
        AssertCacheEmpty(before, "validation-faults-before");

        string blankSqlExceptionName;
        try
        {
            _ = await _client!.QueryAsync<SmokeTest>("   ");
            throw new InvalidOperationException("Blank SQL unexpectedly succeeded.");
        }
        catch (OneOffQueryError error)
        {
            throw new InvalidOperationException(
                $"Blank SQL must remain a programming fault, not {error.GetType().Name}.");
        }
        catch (ArgumentException error)
        {
            blankSqlExceptionName = error.GetType().Name;
        }

        // Use a nullable sentinel instead of a sentinel throw inside the try block so that a
        // future regression where QueryAsync<object> succeeds cannot be silently caught by the
        // catch (InvalidOperationException) handler below.
        string? unsupportedRowTypeExceptionName = null;
        try
        {
            _ = await _client!.QueryAsync<object>("WHERE value = 'ignored'");
        }
        catch (OneOffQueryError error)
        {
            throw new InvalidOperationException(
                $"Unsupported row type must remain a programming fault, not {error.GetType().Name}.");
        }
        catch (InvalidOperationException error)
        {
            unsupportedRowTypeExceptionName = error.GetType().Name;
        }

        if (unsupportedRowTypeExceptionName == null)
            throw new InvalidOperationException("Unsupported row type unexpectedly succeeded — QueryAsync<object> must throw InvalidOperationException.");

        var after = CaptureCacheSnapshot("validation_faults");
        AssertCacheEmpty(after, "validation-faults-after");

        EmitStepOk("validation_faults", new Dictionary<string, object?>
        {
            ["blank_sql_exception"] = blankSqlExceptionName,
            ["unsupported_row_type_exception"] = unsupportedRowTypeExceptionName,
            ["cache_rows_after"] = after.GetRowsCount,
            ["cache_count_after"] = after.HandleCount,
        });
    }

    private async Task RunNegativeQueryAsync()
    {
        var before = CaptureCacheSnapshot("negative_query");
        AssertCacheEmpty(before, "negative-query-before");

        var invalidClause = "WHERE value =";
        try
        {
            _ = await _client!.QueryAsync<SmokeTest>(invalidClause, TimeSpan.FromSeconds(5));
            throw new InvalidOperationException("Invalid SQL unexpectedly succeeded.");
        }
        catch (OneOffQueryError error)
        {
            if (error.FailureCategory != OneOffQueryFailureCategory.InvalidQuery)
            {
                throw new InvalidOperationException(
                    $"Expected InvalidQuery failure category, got {error.FailureCategory}.");
            }

            if (error.TargetTable != "smoke_test")
            {
                throw new InvalidOperationException(
                    $"Expected target table 'smoke_test', got '{error.TargetTable}'.");
            }

            if (error.RequestedRowType != typeof(SmokeTest))
            {
                throw new InvalidOperationException(
                    $"Expected requested row type '{typeof(SmokeTest).FullName}', got '{error.RequestedRowType.FullName}'.");
            }

            if (error.SqlClause != invalidClause)
            {
                throw new InvalidOperationException(
                    $"Expected failing SQL clause '{invalidClause}', got '{error.SqlClause}'.");
            }

            var after = CaptureCacheSnapshot("negative_query");
            AssertCacheEmpty(after, "negative-query-after");

            EmitStepOk("negative_query", new Dictionary<string, object?>
            {
                ["exception_type"] = error.GetType().FullName,
                ["failure_category"] = error.FailureCategory.ToString(),
                ["target_table"] = error.TargetTable,
                ["requested_row_type"] = error.RequestedRowType.FullName,
                ["sql_clause"] = error.SqlClause,
                ["error_message"] = error.ErrorMessage,
                ["recovery_guidance"] = error.RecoveryGuidance,
                ["requested_at_utc"] = error.RequestedAt.ToString("O", CultureInfo.InvariantCulture),
                ["failed_at_utc"] = error.FailedAt.ToString("O", CultureInfo.InvariantCulture),
                ["cache_rows_after"] = after.GetRowsCount,
                ["cache_count_after"] = after.HandleCount,
            });
        }
    }

    private CacheSnapshot CaptureCacheSnapshot(string phase)
    {
        var db = _client!.GetDb<RemoteTables>()
            ?? throw new InvalidOperationException(
                $"GetDb<RemoteTables>() returned null during {phase}.");

        var getRowsCount = _client.GetRows("SmokeTest").Count();
        return new CacheSnapshot(getRowsCount, db.SmokeTest.Count);
    }

    private static void AssertCacheEmpty(CacheSnapshot snapshot, string phase)
    {
        if (snapshot.GetRowsCount != 0 || snapshot.HandleCount != 0)
        {
            throw new InvalidOperationException(
                $"Expected smoke_test cache to stay empty during {phase}, got GetRows={snapshot.GetRowsCount}, Count={snapshot.HandleCount}.");
        }
    }

    private void StartStep(Step step)
    {
        _currentStep = step;
        _stepStartedAt = Time.GetTicksMsec() / 1000.0;
    }

    private static string NormalizeHost(string host)
    {
        if (host.StartsWith("http://", StringComparison.OrdinalIgnoreCase))
            return "ws://" + host.Substring("http://".Length);

        if (host.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
            return "wss://" + host.Substring("https://".Length);

        return host;
    }

    // Sufficient for the controlled alphanumeric/hyphen UUID values used by this harness only.
    private static string EscapeSqlLiteral(string value) =>
        value.Replace("'", "''", StringComparison.Ordinal);

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

    private static void WriteJsonLine(object payload)
    {
        try
        {
            var json = JsonSerializer.Serialize(payload);
            Console.WriteLine("E2E-EVENT " + json);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("OneOffQuerySmokeRunner: failed to serialize event: " + ex.Message);
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
        Step.InvokeReducer => "invoke_reducer",
        Step.Query => "query",
        Step.ValidationFaults => "validation_faults",
        Step.NegativeQuery => "negative_query",
        _ => "unknown",
    };

    private readonly record struct CacheSnapshot(int GetRowsCount, int HandleCount);
}

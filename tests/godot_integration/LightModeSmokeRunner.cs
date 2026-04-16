using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using Godot;
using GodotSpacetime;
using GodotSpacetime.Connection;
using GodotSpacetime.Reducers;
using GodotSpacetime.Subscriptions;
using SpacetimeDB;
using SpacetimeDB.Types;
using Environment = System.Environment;

namespace GodotSpacetime.IntegrationTests;

// Drives Story 9.2 light-mode verification against a real runtime. The Python
// contract lives in tests/test_story_9_2_light_mode_integration.py.
// The goal is to measure the supported runtime instead of trusting either the
// upstream migration docs or the builder surface in isolation.
public partial class LightModeSmokeRunner : Node
{
    private enum ScenarioKind
    {
        SingleSession,
        ToggleReconnect,
    }

    private enum Phase
    {
        None,
        Connect,
        Subscribe,
        InvokeReducer,
        ObserveRowChange,
        InvokeReducerSameSession,
        ObserveRowChangeSameSession,
        DisconnectForReconnect,
        Reconnect,
        SubscribeReconnect,
        InvokeReducerReconnect,
        ObserveRowChangeReconnect,
        Done,
    }

    private const string EventPrefix = "E2E-EVENT ";

    private string _host = "";
    private string _moduleName = "";
    private string _initialValue = "";
    private string _sameSessionValue = "";
    private string _reconnectValue = "";
    private string _currentExpectedValue = "";
    private double _stepTimeoutSeconds = 30.0;
    private bool _requestedLightMode;
    private ScenarioKind _scenario = ScenarioKind.SingleSession;

    private SpacetimeClient? _client;
    private RemoteTables? _hookedDb;
    private RemoteReducers? _hookedReducers;
    private Phase _phase = Phase.None;
    private double _phaseStartedAt;
    private bool _finished;
    private bool _expectDisconnectForReconnect;

    private bool _sawGetRows;
    private bool _sawTypedTableHandle;
    private bool _sawRowChangedEvent;
    private string _currentReducerContract = "";
    private Dictionary<string, object?>? _currentRowContext;
    private Dictionary<string, object?>? _currentReducerContext;

    private Dictionary<string, object?>? _initialObservation;
    private Dictionary<string, object?>? _sameSessionObservation;
    private Dictionary<string, object?>? _reconnectObservation;

    public override void _Ready()
    {
        try
        {
            _host = Environment.GetEnvironmentVariable("SPACETIME_E2E_HOST") ?? "";
            _moduleName = Environment.GetEnvironmentVariable("SPACETIME_E2E_MODULE") ?? "";
            _initialValue = Environment.GetEnvironmentVariable("SPACETIME_E2E_VALUE") ?? "";
            _sameSessionValue = Environment.GetEnvironmentVariable("SPACETIME_E2E_TOGGLED_VALUE") ?? "";
            _reconnectValue = Environment.GetEnvironmentVariable("SPACETIME_E2E_RECONNECTED_VALUE") ?? "";

            var scenarioRaw = Environment.GetEnvironmentVariable("SPACETIME_E2E_SCENARIO") ?? "single_session";
            var lightModeRaw = Environment.GetEnvironmentVariable("SPACETIME_E2E_LIGHT_MODE") ?? "";
            var timeoutRaw = Environment.GetEnvironmentVariable("SPACETIME_E2E_STEP_TIMEOUT") ?? "30";

            if (!double.TryParse(timeoutRaw, NumberStyles.Float, CultureInfo.InvariantCulture, out var parsedTimeout))
                parsedTimeout = 30.0;
            _stepTimeoutSeconds = Math.Max(1.0, parsedTimeout);

            _scenario = ParseScenario(scenarioRaw);
            _requestedLightMode = ParseLightMode(lightModeRaw);

            if (string.IsNullOrWhiteSpace(_host) ||
                string.IsNullOrWhiteSpace(_moduleName) ||
                string.IsNullOrWhiteSpace(_initialValue))
            {
                Console.Error.WriteLine(
                    "LightModeSmokeRunner: missing required env vars " +
                    "(SPACETIME_E2E_HOST, SPACETIME_E2E_MODULE, SPACETIME_E2E_VALUE, SPACETIME_E2E_LIGHT_MODE)");
                Quit(1);
                return;
            }

            if (_scenario == ScenarioKind.ToggleReconnect &&
                (string.IsNullOrWhiteSpace(_sameSessionValue) || string.IsNullOrWhiteSpace(_reconnectValue)))
            {
                Console.Error.WriteLine(
                    "LightModeSmokeRunner: toggle_reconnect requires SPACETIME_E2E_TOGGLED_VALUE " +
                    "and SPACETIME_E2E_RECONNECTED_VALUE.");
                Quit(1);
                return;
            }

            var settings = new SpacetimeSettings
            {
                Host = NormalizeHost(_host.Trim()),
                Database = _moduleName.Trim(),
                LightMode = _requestedLightMode,
            };

            _client = new SpacetimeClient { Settings = settings };
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
        DetachLowLevelObservers();

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
        if (_finished || status == null)
            return;

        if (_expectDisconnectForReconnect && status.State == ConnectionState.Disconnected)
        {
            _expectDisconnectForReconnect = false;
            StartPhase(Phase.Reconnect);
            try
            {
                _client!.Connect();
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
            try
            {
                AttachLowLevelObservers();
            }
            catch (Exception ex)
            {
                EmitError(StepName(_phase), "failed to attach low-level observers: " + ex.Message);
                Finish(pass: false);
                return;
            }

            switch (_phase)
            {
                case Phase.Connect:
                    EmitStepOk("connect", new Dictionary<string, object?>
                    {
                        ["description"] = status.Description,
                        ["requested_light_mode"] = _requestedLightMode,
                        ["settings_light_mode"] = _client!.Settings!.LightMode,
                        ["scenario"] = _scenario.ToString(),
                    });
                    StartPhase(Phase.Subscribe);
                    SubscribeCurrentSession("subscribe");
                    return;
                case Phase.Reconnect:
                    EmitStepOk("connect_reconnect", new Dictionary<string, object?>
                    {
                        ["description"] = status.Description,
                        ["requested_light_mode"] = _requestedLightMode,
                        ["settings_light_mode"] = _client!.Settings!.LightMode,
                        ["scenario"] = _scenario.ToString(),
                    });
                    StartPhase(Phase.SubscribeReconnect);
                    SubscribeCurrentSession("subscribe_reconnect");
                    return;
            }
        }

        if (status.State == ConnectionState.Disconnected &&
            _phase != Phase.None &&
            _phase != Phase.Done &&
            _phase != Phase.DisconnectForReconnect)
        {
            EmitError(StepName(_phase), $"disconnected mid-flight: {status.Description}");
            Finish(pass: false);
        }
    }

    private void OnSubscriptionApplied(SubscriptionAppliedEvent appliedEvent)
    {
        if (_finished)
            return;

        switch (_phase)
        {
            case Phase.Subscribe:
                EmitStepOk("subscribe", new Dictionary<string, object?>
                {
                    ["synchronized"] = new[] { "smoke_test" },
                    ["requested_light_mode"] = _requestedLightMode,
                    ["settings_light_mode"] = _client!.Settings!.LightMode,
                });
                ResetObservationState(_initialValue);
                StartPhase(Phase.InvokeReducer);
                InvokeReducerForCurrentValue("invoke_reducer");
                return;

            case Phase.SubscribeReconnect:
                EmitStepOk("subscribe_reconnect", new Dictionary<string, object?>
                {
                    ["synchronized"] = new[] { "smoke_test" },
                    ["requested_light_mode"] = _requestedLightMode,
                    ["settings_light_mode"] = _client!.Settings!.LightMode,
                });
                ResetObservationState(_reconnectValue);
                StartPhase(Phase.InvokeReducerReconnect);
                InvokeReducerForCurrentValue("invoke_reducer_reconnect");
                return;
        }
    }

    private void OnSubscriptionFailed(SubscriptionFailedEvent failedEvent)
    {
        if (_finished)
            return;

        EmitError(StepName(_phase), "SubscriptionFailed signal fired");
        Finish(pass: false);
    }

    private void OnReducerCallSucceeded(ReducerCallResult result)
    {
        if (_finished || result == null || result.ReducerName != "ping_insert")
            return;

        switch (_phase)
        {
            case Phase.InvokeReducer:
                _currentReducerContract = nameof(SpacetimeClient.ReducerCallSucceeded);
                EmitStepOk("invoke_reducer", new Dictionary<string, object?>
                {
                    ["contract"] = _currentReducerContract,
                    ["reducer"] = result.ReducerName,
                    ["invocation_id"] = result.InvocationId,
                    ["settings_light_mode"] = _client!.Settings!.LightMode,
                });
                StartPhase(Phase.ObserveRowChange);
                CheckTypedTableHandle();
                CheckGetRows();
                TryCompleteObservation();
                return;

            case Phase.InvokeReducerSameSession:
                _currentReducerContract = nameof(SpacetimeClient.ReducerCallSucceeded);
                EmitStepOk("invoke_reducer_same_session", new Dictionary<string, object?>
                {
                    ["contract"] = _currentReducerContract,
                    ["reducer"] = result.ReducerName,
                    ["invocation_id"] = result.InvocationId,
                    ["settings_light_mode"] = _client!.Settings!.LightMode,
                });
                StartPhase(Phase.ObserveRowChangeSameSession);
                CheckTypedTableHandle();
                CheckGetRows();
                TryCompleteObservation();
                return;

            case Phase.InvokeReducerReconnect:
                _currentReducerContract = nameof(SpacetimeClient.ReducerCallSucceeded);
                EmitStepOk("invoke_reducer_reconnect", new Dictionary<string, object?>
                {
                    ["contract"] = _currentReducerContract,
                    ["reducer"] = result.ReducerName,
                    ["invocation_id"] = result.InvocationId,
                    ["settings_light_mode"] = _client!.Settings!.LightMode,
                });
                StartPhase(Phase.ObserveRowChangeReconnect);
                CheckTypedTableHandle();
                CheckGetRows();
                TryCompleteObservation();
                return;
        }
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
        if (value != _currentExpectedValue)
            return;

        _sawRowChangedEvent = true;
        CheckTypedTableHandle();
        CheckGetRows();
        TryCompleteObservation();
    }

    private void SubscribeCurrentSession(string stepName)
    {
        try
        {
            _client!.Subscribe(new[] { "SELECT * FROM smoke_test" });
        }
        catch (Exception ex)
        {
            EmitError(stepName, ex.GetType().Name + ": " + ex.Message);
            Finish(pass: false);
        }
    }

    private void InvokeReducerForCurrentValue(string stepName)
    {
        try
        {
            _client!.InvokeReducer(new Reducer.PingInsert(_currentExpectedValue));
        }
        catch (Exception ex)
        {
            EmitError(stepName, ex.GetType().Name + ": " + ex.Message);
            Finish(pass: false);
        }
    }

    private void ResetObservationState(string expectedValue)
    {
        _currentExpectedValue = expectedValue.Trim();
        _sawGetRows = false;
        _sawTypedTableHandle = false;
        _sawRowChangedEvent = false;
        _currentReducerContract = "";
        _currentRowContext = null;
        _currentReducerContext = null;
    }

    private void AttachLowLevelObservers()
    {
        if (_client == null)
            throw new InvalidOperationException("SpacetimeClient missing.");

        DetachLowLevelObservers();

        var db = _client.GetDb<RemoteTables>()
            ?? throw new InvalidOperationException("GetDb<RemoteTables>() returned null while connected.");
        var connection = TryGetGeneratedConnection(_client)
            ?? throw new InvalidOperationException("Unable to resolve generated DbConnection from SpacetimeClient.");

        _hookedDb = db;
        _hookedReducers = connection.Reducers;
        _hookedDb.SmokeTest.OnInsert += OnLowLevelRowInsert;
        _hookedReducers.OnPingInsert += OnLowLevelReducerPingInsert;
    }

    private void DetachLowLevelObservers()
    {
        if (_hookedDb != null)
            _hookedDb.SmokeTest.OnInsert -= OnLowLevelRowInsert;

        if (_hookedReducers != null)
            _hookedReducers.OnPingInsert -= OnLowLevelReducerPingInsert;

        _hookedDb = null;
        _hookedReducers = null;
    }

    private static DbConnection? TryGetGeneratedConnection(SpacetimeClient client)
    {
        var connectionService = typeof(SpacetimeClient)
            .GetField("_connectionService", BindingFlags.Instance | BindingFlags.NonPublic)
            ?.GetValue(client);
        var adapter = connectionService?.GetType()
            .GetField("_adapter", BindingFlags.Instance | BindingFlags.NonPublic)
            ?.GetValue(connectionService);
        var connection = adapter?.GetType()
            .GetProperty("Connection", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public)
            ?.GetValue(adapter);

        return connection as DbConnection;
    }

    private void OnLowLevelRowInsert(EventContext ctx, SmokeTest row)
    {
        if (_finished || row.Value != _currentExpectedValue)
            return;

        _currentRowContext = CaptureContextSnapshot(ctx, ctx.Event);
        TryCompleteObservation();
    }

    private void OnLowLevelReducerPingInsert(ReducerEventContext ctx, string value)
    {
        if (_finished || value != _currentExpectedValue)
            return;

        _currentReducerContext = CaptureContextSnapshot(ctx, ctx.Event);
        TryCompleteObservation();
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
                if (row.Value == _currentExpectedValue)
                {
                    _sawTypedTableHandle = true;
                    break;
                }
            }
        }
        catch (Exception ex)
        {
            EmitError(StepName(_phase), "typed table handle threw: " + ex.Message);
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
                if (ExtractRowValue(row) == _currentExpectedValue)
                {
                    _sawGetRows = true;
                    break;
                }
            }
        }
        catch (Exception ex)
        {
            EmitError(StepName(_phase), "GetRows threw: " + ex.Message);
            Finish(pass: false);
        }
    }

    private void TryCompleteObservation()
    {
        if (_finished)
            return;

        if (_currentRowContext == null ||
            _currentReducerContext == null ||
            string.IsNullOrEmpty(_currentReducerContract) ||
            !_sawTypedTableHandle ||
            !_sawGetRows ||
            !_sawRowChangedEvent)
        {
            return;
        }

        var observation = BuildObservationSummary();

        switch (_phase)
        {
            case Phase.ObserveRowChange:
                EmitStepOk("observe_row_change", new Dictionary<string, object?>
                {
                    ["via"] = new[] { "typed_table_handle", "get_rows", "row_changed_event" },
                    ["value"] = _currentExpectedValue,
                    ["reducer_contract"] = _currentReducerContract,
                    ["observation_signature"] = observation["signature"],
                });

                if (_scenario == ScenarioKind.SingleSession)
                {
                    Finish(pass: true, new Dictionary<string, object?>
                    {
                        ["scenario"] = "single_session",
                        ["requested_light_mode"] = _requestedLightMode,
                        ["observation"] = observation,
                    });
                    return;
                }

                _initialObservation = observation;
                var lightModeBefore = _client!.Settings!.LightMode;
                _client.Settings.LightMode = true;
                EmitStepOk("toggle_mid_session", new Dictionary<string, object?>
                {
                    ["light_mode_before"] = lightModeBefore,
                    ["light_mode_after"] = _client.Settings.LightMode,
                });
                ResetObservationState(_sameSessionValue);
                StartPhase(Phase.InvokeReducerSameSession);
                InvokeReducerForCurrentValue("invoke_reducer_same_session");
                return;

            case Phase.ObserveRowChangeSameSession:
                EmitStepOk("observe_row_change_same_session", new Dictionary<string, object?>
                {
                    ["via"] = new[] { "typed_table_handle", "get_rows", "row_changed_event" },
                    ["value"] = _currentExpectedValue,
                    ["reducer_contract"] = _currentReducerContract,
                    ["observation_signature"] = observation["signature"],
                });
                _sameSessionObservation = observation;
                StartPhase(Phase.DisconnectForReconnect);
                _expectDisconnectForReconnect = true;
                _client!.Disconnect();
                return;

            case Phase.ObserveRowChangeReconnect:
                EmitStepOk("observe_row_change_reconnect", new Dictionary<string, object?>
                {
                    ["via"] = new[] { "typed_table_handle", "get_rows", "row_changed_event" },
                    ["value"] = _currentExpectedValue,
                    ["reducer_contract"] = _currentReducerContract,
                    ["observation_signature"] = observation["signature"],
                });
                _reconnectObservation = observation;

                var initialSignature = (Dictionary<string, object?>)_initialObservation!["signature"]!;
                var sameSessionSignature = (Dictionary<string, object?>)_sameSessionObservation!["signature"]!;
                var reconnectSignature = (Dictionary<string, object?>)_reconnectObservation["signature"]!;

                Finish(pass: true, new Dictionary<string, object?>
                {
                    ["scenario"] = "toggle_reconnect",
                    ["before_toggle"] = _initialObservation,
                    ["same_session_after_toggle"] = _sameSessionObservation,
                    ["after_reconnect"] = _reconnectObservation,
                    ["same_session_changed"] = !SignaturesEqual(initialSignature, sameSessionSignature),
                    ["reconnect_changed"] = !SignaturesEqual(initialSignature, reconnectSignature),
                });
                return;
        }
    }

    private Dictionary<string, object?> BuildObservationSummary()
    {
        return new Dictionary<string, object?>
        {
            ["requested_light_mode"] = _requestedLightMode,
            ["settings_light_mode"] = _client!.Settings!.LightMode,
            ["public_channels"] = new[] { "typed_table_handle", "get_rows", "row_changed_event" },
            ["reducer_contract"] = _currentReducerContract,
            ["row_context"] = _currentRowContext!,
            ["reducer_context"] = _currentReducerContext!,
            ["signature"] = BuildObservationSignature(_currentRowContext!, _currentReducerContext!, _currentReducerContract),
        };
    }

    private static Dictionary<string, object?> CaptureContextSnapshot(object context, object? eventPayload)
    {
        return new Dictionary<string, object?>
        {
            ["context_type"] = context.GetType().FullName ?? context.GetType().Name,
            ["context_members"] = ListPublicMemberNames(context),
            ["event_type"] = eventPayload?.GetType().FullName ?? "null",
            ["event_members"] = ListPublicMemberNames(eventPayload),
            ["has_caller_identity_member"] = HasMember(eventPayload, "CallerIdentity"),
            ["caller_identity_present"] = TryDescribeMemberValue(eventPayload, "CallerIdentity", out var callerIdentityValue),
            ["caller_identity_value"] = callerIdentityValue,
            ["has_energy_consumed_member"] = HasMember(eventPayload, "EnergyConsumed"),
            ["energy_consumed_present"] = TryDescribeMemberValue(eventPayload, "EnergyConsumed", out var energyConsumedValue),
            ["energy_consumed_value"] = energyConsumedValue,
            ["has_total_host_execution_duration_member"] = HasMember(eventPayload, "TotalHostExecutionDuration"),
            ["total_host_execution_duration_present"] = TryDescribeMemberValue(eventPayload, "TotalHostExecutionDuration", out var totalHostExecutionDurationValue),
            ["total_host_execution_duration_value"] = totalHostExecutionDurationValue,
            ["has_status_member"] = HasMember(eventPayload, "Status"),
            ["status_present"] = TryDescribeMemberValue(eventPayload, "Status", out var statusValue),
            ["status_value"] = statusValue,
            ["has_reducer_name_member"] = HasReducerNameMember(eventPayload),
            ["reducer_name_present"] = TryDescribeReducerName(eventPayload, out var reducerNameValue),
            ["reducer_name_value"] = reducerNameValue,
        };
    }

    private static Dictionary<string, object?> BuildObservationSignature(
        Dictionary<string, object?> rowContext,
        Dictionary<string, object?> reducerContext,
        string reducerContract)
    {
        return new Dictionary<string, object?>
        {
            ["reducer_contract"] = reducerContract,
            ["row_context_type"] = rowContext["context_type"],
            ["row_context_members"] = rowContext["context_members"],
            ["row_event_type"] = rowContext["event_type"],
            ["row_event_members"] = rowContext["event_members"],
            ["row_has_caller_identity_member"] = rowContext["has_caller_identity_member"],
            ["row_caller_identity_present"] = rowContext["caller_identity_present"],
            ["row_has_energy_consumed_member"] = rowContext["has_energy_consumed_member"],
            ["row_energy_consumed_present"] = rowContext["energy_consumed_present"],
            ["row_has_total_host_execution_duration_member"] = rowContext["has_total_host_execution_duration_member"],
            ["row_total_host_execution_duration_present"] = rowContext["total_host_execution_duration_present"],
            ["row_has_status_member"] = rowContext["has_status_member"],
            ["row_status_present"] = rowContext["status_present"],
            ["row_has_reducer_name_member"] = rowContext["has_reducer_name_member"],
            ["row_reducer_name_present"] = rowContext["reducer_name_present"],
            ["reducer_context_type"] = reducerContext["context_type"],
            ["reducer_context_members"] = reducerContext["context_members"],
            ["reducer_event_type"] = reducerContext["event_type"],
            ["reducer_event_members"] = reducerContext["event_members"],
            ["reducer_has_caller_identity_member"] = reducerContext["has_caller_identity_member"],
            ["reducer_caller_identity_present"] = reducerContext["caller_identity_present"],
            ["reducer_has_energy_consumed_member"] = reducerContext["has_energy_consumed_member"],
            ["reducer_energy_consumed_present"] = reducerContext["energy_consumed_present"],
            ["reducer_has_total_host_execution_duration_member"] = reducerContext["has_total_host_execution_duration_member"],
            ["reducer_total_host_execution_duration_present"] = reducerContext["total_host_execution_duration_present"],
            ["reducer_has_status_member"] = reducerContext["has_status_member"],
            ["reducer_status_present"] = reducerContext["status_present"],
            ["reducer_has_reducer_name_member"] = reducerContext["has_reducer_name_member"],
            ["reducer_reducer_name_present"] = reducerContext["reducer_name_present"],
        };
    }

    private static bool SignaturesEqual(Dictionary<string, object?> left, Dictionary<string, object?> right)
    {
        return JsonSerializer.Serialize(left) == JsonSerializer.Serialize(right);
    }

    private static string[] ListPublicMemberNames(object? target)
    {
        if (target == null)
            return Array.Empty<string>();

        var members = target.GetType()
            .GetMembers(BindingFlags.Instance | BindingFlags.Public)
            .Where(member =>
                member.MemberType == MemberTypes.Field ||
                (member.MemberType == MemberTypes.Property && member is PropertyInfo property && property.GetIndexParameters().Length == 0))
            .Select(member => member.Name)
            .Distinct(StringComparer.Ordinal)
            .OrderBy(static name => name, StringComparer.Ordinal)
            .ToArray();

        return members;
    }

    private static bool HasMember(object? target, string name) => TryReadMember(target, name, out _);

    private static bool HasReducerNameMember(object? target) =>
        HasMember(target, "ReducerName") || HasMember(target, "Reducer");

    private static bool TryDescribeReducerName(object? target, out string? value)
    {
        value = null;

        if (TryDescribeMemberValue(target, "ReducerName", out value))
            return true;

        if (!TryReadMember(target, "Reducer", out var reducerArgs) || reducerArgs == null)
            return false;

        value = DescribeReducerName(reducerArgs);
        return !string.IsNullOrEmpty(value);
    }

    private static string? DescribeReducerName(object reducerArgs)
    {
        if (reducerArgs is IReducerArgs typedReducerArgs)
            return typedReducerArgs.ReducerName;

        if (TryDescribeMemberValue(reducerArgs, "ReducerName", out var reducerName))
            return reducerName;

        return reducerArgs.GetType().Name;
    }

    private static bool TryDescribeMemberValue(object? target, string name, out string? value)
    {
        value = null;
        if (!TryReadMember(target, name, out var raw) || raw == null)
            return false;

        value = DescribeValue(raw);
        return true;
    }

    private static bool TryReadMember(object? target, string name, out object? value)
    {
        value = null;
        if (target == null)
            return false;

        var type = target.GetType();
        var property = type.GetProperty(name, BindingFlags.Instance | BindingFlags.Public);
        if (property != null && property.GetIndexParameters().Length == 0)
        {
            value = property.GetValue(target);
            return true;
        }

        var field = type.GetField(name, BindingFlags.Instance | BindingFlags.Public);
        if (field == null)
            return false;

        value = field.GetValue(target);
        return true;
    }

    private static string DescribeValue(object value)
    {
        return value switch
        {
            null => "",
            TimeSpan timeSpan => timeSpan.ToString("c", CultureInfo.InvariantCulture),
            _ => value.ToString() ?? value.GetType().Name,
        };
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

    private static ScenarioKind ParseScenario(string raw)
    {
        return raw.Trim().ToLowerInvariant() switch
        {
            "single_session" => ScenarioKind.SingleSession,
            "toggle_reconnect" => ScenarioKind.ToggleReconnect,
            _ => throw new InvalidOperationException(
                $"Unsupported SPACETIME_E2E_SCENARIO value '{raw}'. Expected single_session or toggle_reconnect."),
        };
    }

    private static bool ParseLightMode(string raw)
    {
        return raw.Trim().ToLowerInvariant() switch
        {
            "false" => false,
            "true" => true,
            _ => throw new InvalidOperationException(
                $"Unsupported SPACETIME_E2E_LIGHT_MODE value '{raw}'. Expected true or false."),
        };
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
            Console.WriteLine(EventPrefix + JsonSerializer.Serialize(payload));
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("LightModeSmokeRunner: failed to serialize event: " + ex.Message);
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

    private static string StepName(Phase phase) => phase switch
    {
        Phase.Connect => "connect",
        Phase.Subscribe => "subscribe",
        Phase.InvokeReducer => "invoke_reducer",
        Phase.ObserveRowChange => "observe_row_change",
        Phase.InvokeReducerSameSession => "invoke_reducer_same_session",
        Phase.ObserveRowChangeSameSession => "observe_row_change_same_session",
        Phase.DisconnectForReconnect => "disconnect_for_reconnect",
        Phase.Reconnect => "connect_reconnect",
        Phase.SubscribeReconnect => "subscribe_reconnect",
        Phase.InvokeReducerReconnect => "invoke_reducer_reconnect",
        Phase.ObserveRowChangeReconnect => "observe_row_change_reconnect",
        _ => "unknown",
    };
}

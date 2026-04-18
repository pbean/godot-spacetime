using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json;
using Godot;
using GodotSpacetime;
using GodotSpacetime.Connection;
using GodotSpacetime.Reducers;
using GodotSpacetime.Scenes;
using GodotSpacetime.Subscriptions;
using DefaultBindings = SpacetimeDB.Types;
using MultiBindings = SpacetimeDB.MultiModuleTypes;

namespace GodotSpacetime.IntegrationTests;

// Drives two independent SpacetimeClient instances against two deployments of
// the same smoke_test module compiled under different generated namespaces.
// The contract is enforced by
// tests/test_story_10_1_multi_module_connections_integration.py.
public partial class MultiModuleSmokeRunner : Node
{
    private const string EventPrefix = "E2E-EVENT ";
    private const string ClientAId = SpacetimeClient.DefaultConnectionId;
    private const string ClientBId = "AnalyticsClient";

    private enum Step
    {
        None,
        VerifyRowReceiverModuleSelection,
        ConnectClientA,
        ConnectClientB,
        LookupClients,
        SubscribeClientA,
        SubscribeClientB,
        InvokeClientA,
        ObserveClientA,
        DisconnectClientA,
        AssertClientBStillConnected,
        InvokeClientB,
        ObserveClientB,
        ReconnectClientA,
        ResubscribeClientA,
        Done,
    }

    private string _host = "";
    private string _moduleA = "";
    private string _moduleB = "";
    private string _valueA = "";
    private string _valueB = "";
    private double _stepTimeoutSeconds = 30.0;

    private SpacetimeClient? _clientA;
    private SpacetimeClient? _clientB;
    private RowReceiver? _receiverA;
    private RowReceiver? _receiverB;
    private Step _currentStep = Step.None;
    private double _stepStartedAt;
    private bool _finished;
    private bool _expectClientADisconnect;

    private string _currentExpectedValue = "";
    private string _currentObservedClientId = "";
    private bool _sawTypedTableHandle;
    private bool _sawGetRows;
    private bool _sawRowChangedEvent;
    private int _crossTalkCount;
    // Row-change events can be dispatched by the SDK BEFORE ReducerCallSucceeded for a
    // TransactionUpdate that carries both, so the runner may see the insert while it is
    // still in the InvokeClient phase. Buffer every matching insert by (clientId,value)
    // so StartObservation can replay the one it needs instead of timing out waiting for
    // a signal that already fired.
    private readonly HashSet<string> _observedInsertKeys = new();

    public override void _Ready()
    {
        try
        {
            _host = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_HOST") ?? "";
            _moduleA = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_MODULE_A") ?? "";
            _moduleB = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_MODULE_B") ?? "";
            _valueA = (System.Environment.GetEnvironmentVariable("SPACETIME_E2E_VALUE_A") ?? "").Trim();
            _valueB = (System.Environment.GetEnvironmentVariable("SPACETIME_E2E_VALUE_B") ?? "").Trim();

            var timeoutRaw = System.Environment.GetEnvironmentVariable("SPACETIME_E2E_STEP_TIMEOUT") ?? "30";
            if (!double.TryParse(timeoutRaw, NumberStyles.Float, CultureInfo.InvariantCulture, out var parsedTimeout))
                parsedTimeout = 30.0;
            _stepTimeoutSeconds = Math.Max(1.0, parsedTimeout);

            if (string.IsNullOrWhiteSpace(_host) ||
                string.IsNullOrWhiteSpace(_moduleA) ||
                string.IsNullOrWhiteSpace(_moduleB) ||
                string.IsNullOrWhiteSpace(_valueA) ||
                string.IsNullOrWhiteSpace(_valueB))
            {
                Console.Error.WriteLine(
                    "MultiModuleSmokeRunner: missing required env vars " +
                    "(SPACETIME_E2E_HOST, SPACETIME_E2E_MODULE_A, SPACETIME_E2E_MODULE_B, " +
                    "SPACETIME_E2E_VALUE_A, SPACETIME_E2E_VALUE_B).");
                GetTree().Quit(1);
                return;
            }

            var settingsA = new SpacetimeSettings
            {
                Host = NormalizeHost(_host.Trim()),
                Database = _moduleA.Trim(),
                GeneratedBindingsNamespace = SpacetimeSettings.DefaultGeneratedBindingsNamespace,
            };
            var settingsB = new SpacetimeSettings
            {
                Host = NormalizeHost(_host.Trim()),
                Database = _moduleB.Trim(),
                GeneratedBindingsNamespace = "SpacetimeDB.MultiModuleTypes",
            };

            _clientA = new SpacetimeClient
            {
                Name = "PrimaryClientNode",
                ConnectionId = ClientAId,
                Settings = settingsA,
            };
            _clientB = new SpacetimeClient
            {
                Name = "AnalyticsClientNode",
                ConnectionId = ClientBId,
                Settings = settingsB,
            };

            _clientA.ConnectionStateChanged += OnClientAConnectionStateChanged;
            _clientA.SubscriptionApplied += OnClientASubscriptionApplied;
            _clientA.SubscriptionFailed += OnSubscriptionFailed;
            _clientA.ReducerCallSucceeded += OnClientAReducerCallSucceeded;
            _clientA.ReducerCallFailed += OnReducerCallFailed;
            _clientA.RowChanged += OnClientARowChanged;

            _clientB.ConnectionStateChanged += OnClientBConnectionStateChanged;
            _clientB.SubscriptionApplied += OnClientBSubscriptionApplied;
            _clientB.SubscriptionFailed += OnSubscriptionFailed;
            _clientB.ReducerCallSucceeded += OnClientBReducerCallSucceeded;
            _clientB.ReducerCallFailed += OnReducerCallFailed;
            _clientB.RowChanged += OnClientBRowChanged;

            AddChild(_clientA);
            AddChild(_clientB);

            _receiverA = new RowReceiver { Name = "ReceiverA", ClientPath = _clientA.GetPath() };
            _receiverB = new RowReceiver { Name = "ReceiverB", ClientPath = _clientB.GetPath() };
            AddChild(_receiverA);
            AddChild(_receiverB);

            VerifyRowReceiverModuleSelection();
            if (_finished) return;
            StartStep(Step.ConnectClientA);
            _clientA.Connect();
        }
        catch (Exception ex)
        {
            EmitError("bootstrap", ex.GetType().Name + ": " + ex.Message);
            Finish(pass: false);
        }
    }

    public override void _ExitTree()
    {
        if (_clientA != null)
        {
            _clientA.ConnectionStateChanged -= OnClientAConnectionStateChanged;
            _clientA.SubscriptionApplied -= OnClientASubscriptionApplied;
            _clientA.SubscriptionFailed -= OnSubscriptionFailed;
            _clientA.ReducerCallSucceeded -= OnClientAReducerCallSucceeded;
            _clientA.ReducerCallFailed -= OnReducerCallFailed;
            _clientA.RowChanged -= OnClientARowChanged;
        }

        if (_clientB != null)
        {
            _clientB.ConnectionStateChanged -= OnClientBConnectionStateChanged;
            _clientB.SubscriptionApplied -= OnClientBSubscriptionApplied;
            _clientB.SubscriptionFailed -= OnSubscriptionFailed;
            _clientB.ReducerCallSucceeded -= OnClientBReducerCallSucceeded;
            _clientB.ReducerCallFailed -= OnReducerCallFailed;
            _clientB.RowChanged -= OnClientBRowChanged;
        }
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

    private void VerifyRowReceiverModuleSelection()
    {
        StartStep(Step.VerifyRowReceiverModuleSelection);

        var clientARemoteTablesType = _receiverA?.GetResolvedRemoteTablesTypeNameForInspection();
        var clientBRemoteTablesType = _receiverB?.GetResolvedRemoteTablesTypeNameForInspection();
        if (clientARemoteTablesType != "SpacetimeDB.Types.RemoteTables" ||
            clientBRemoteTablesType != "SpacetimeDB.MultiModuleTypes.RemoteTables")
        {
            EmitError(
                "verify_rowreceiver_module_selection",
                $"unexpected row receiver binding types: a={clientARemoteTablesType ?? "null"}, " +
                $"b={clientBRemoteTablesType ?? "null"}");
            Finish(pass: false);
            return;
        }

        var tableNames = ExtractTableNames(_receiverA);
        if (tableNames.Length == 0)
        {
            EmitError(
                "verify_rowreceiver_module_selection",
                "RowReceiver property list did not expose table names for the selected client path.");
            Finish(pass: false);
            return;
        }

        EmitStepOk("verify_rowreceiver_module_selection", new Dictionary<string, object?>
        {
            ["client_a_remote_tables_type"] = clientARemoteTablesType,
            ["client_b_remote_tables_type"] = clientBRemoteTablesType,
            ["table_names"] = tableNames,
        });
    }

    private void OnClientAConnectionStateChanged(ConnectionStatus status)
    {
        if (_finished || status == null || _clientA == null)
            return;

        if (_expectClientADisconnect && status.State == ConnectionState.Disconnected)
        {
            _expectClientADisconnect = false;
            EmitStepOk("disconnect_client_a", new Dictionary<string, object?>
            {
                ["client_id"] = ClientAId,
                ["state"] = status.State.ToString(),
                ["description"] = status.Description,
            });
            StartStep(Step.AssertClientBStillConnected);
            AssertClientBStillConnected();
            return;
        }

        if (status.State == ConnectionState.Connected)
        {
            switch (_currentStep)
            {
                case Step.ConnectClientA:
                    EmitStepOk("connect_client_a", new Dictionary<string, object?>
                    {
                        ["client_id"] = ClientAId,
                        ["database"] = _moduleA,
                        ["generated_namespace"] = _clientA.Settings?.ResolveGeneratedBindingsNamespace(),
                    });
                    StartStep(Step.ConnectClientB);
                    _clientB!.Connect();
                    return;
                case Step.ReconnectClientA:
                    EmitStepOk("reconnect_client_a", new Dictionary<string, object?>
                    {
                        ["client_id"] = ClientAId,
                        ["database"] = _moduleA,
                        ["generated_namespace"] = _clientA.Settings?.ResolveGeneratedBindingsNamespace(),
                    });
                    StartStep(Step.ResubscribeClientA);
                    SubscribeClientA();
                    return;
            }
        }

        if (!_expectClientADisconnect &&
            status.State == ConnectionState.Disconnected &&
            _currentStep is not Step.AssertClientBStillConnected and not Step.InvokeClientB and not Step.ObserveClientB)
        {
            EmitError(
                StepName(_currentStep),
                $"client A disconnected unexpectedly: {status.Description}");
            Finish(pass: false);
        }
    }

    private void OnClientBConnectionStateChanged(ConnectionStatus status)
    {
        if (_finished || status == null || _clientB == null)
            return;

        if (status.State == ConnectionState.Connected && _currentStep == Step.ConnectClientB)
        {
            EmitStepOk("connect_client_b", new Dictionary<string, object?>
            {
                ["client_id"] = ClientBId,
                ["database"] = _moduleB,
                ["generated_namespace"] = _clientB.Settings?.ResolveGeneratedBindingsNamespace(),
            });
            StartStep(Step.LookupClients);
            VerifyLookupClients();
            return;
        }

        if (status.State == ConnectionState.Disconnected)
        {
            EmitError(
                StepName(_currentStep),
                $"client B disconnected unexpectedly: {status.Description}");
            Finish(pass: false);
        }
    }

    private void VerifyLookupClients()
    {
        if (!SpacetimeClient.TryGetClient(ClientAId, out var resolvedClientA) ||
            !ReferenceEquals(resolvedClientA, _clientA))
        {
            EmitError("lookup_clients", $"TryGetClient failed to resolve {ClientAId}.");
            Finish(pass: false);
            return;
        }

        SpacetimeClient resolvedClientB;
        try
        {
            resolvedClientB = SpacetimeClient.GetClientOrThrow(ClientBId);
        }
        catch (Exception ex)
        {
            EmitError("lookup_clients", ex.Message);
            Finish(pass: false);
            return;
        }

        if (!ReferenceEquals(resolvedClientB, _clientB))
        {
            EmitError("lookup_clients", $"GetClientOrThrow resolved the wrong client for {ClientBId}.");
            Finish(pass: false);
            return;
        }

        EmitStepOk("lookup_clients", new Dictionary<string, object?>
        {
            ["resolved_ids"] = new[] { ClientAId, ClientBId },
        });

        StartStep(Step.SubscribeClientA);
        SubscribeClientA();
    }

    private void SubscribeClientA()
    {
        try
        {
            _clientA!.Subscribe(new[] { "SELECT * FROM smoke_test" });
        }
        catch (Exception ex)
        {
            EmitError("subscribe_client_a", ex.GetType().Name + ": " + ex.Message);
            Finish(pass: false);
        }
    }

    private void SubscribeClientB()
    {
        try
        {
            _clientB!.Subscribe(new[] { "SELECT * FROM smoke_test" });
        }
        catch (Exception ex)
        {
            EmitError("subscribe_client_b", ex.GetType().Name + ": " + ex.Message);
            Finish(pass: false);
        }
    }

    private void OnClientASubscriptionApplied(SubscriptionAppliedEvent appliedEvent)
    {
        if (_finished)
            return;

        switch (_currentStep)
        {
            case Step.SubscribeClientA:
                EmitStepOk("subscribe_client_a", new Dictionary<string, object?>
                {
                    ["client_id"] = ClientAId,
                    ["synchronized"] = new[] { "smoke_test" },
                });
                StartStep(Step.SubscribeClientB);
                SubscribeClientB();
                break;
            case Step.ResubscribeClientA:
                EmitStepOk("resubscribe_client_a", new Dictionary<string, object?>
                {
                    ["client_id"] = ClientAId,
                    ["synchronized"] = new[] { "smoke_test" },
                });
                Finish(pass: true);
                break;
        }
    }

    private void OnClientBSubscriptionApplied(SubscriptionAppliedEvent appliedEvent)
    {
        if (_finished || _currentStep != Step.SubscribeClientB)
            return;

        EmitStepOk("subscribe_client_b", new Dictionary<string, object?>
        {
            ["client_id"] = ClientBId,
            ["synchronized"] = new[] { "smoke_test" },
        });
        StartStep(Step.InvokeClientA);
        InvokeClientA();
    }

    private void InvokeClientA()
    {
        try
        {
            _clientA!.InvokeReducer(new DefaultBindings.Reducer.PingInsert(_valueA));
        }
        catch (Exception ex)
        {
            EmitError("invoke_client_a", ex.GetType().Name + ": " + ex.Message);
            Finish(pass: false);
        }
    }

    private void InvokeClientB()
    {
        try
        {
            _clientB!.InvokeReducer(new MultiBindings.Reducer.PingInsert(_valueB));
        }
        catch (Exception ex)
        {
            EmitError("invoke_client_b", ex.GetType().Name + ": " + ex.Message);
            Finish(pass: false);
        }
    }

    private void OnClientAReducerCallSucceeded(ReducerCallResult result)
    {
        if (_finished || result == null || result.ReducerName != "ping_insert")
            return;

        if (_currentStep != Step.InvokeClientA)
            return;

        EmitStepOk("invoke_client_a", new Dictionary<string, object?>
        {
            ["client_id"] = ClientAId,
            ["reducer"] = result.ReducerName,
            ["invocation_id"] = result.InvocationId,
        });
        StartObservation(Step.ObserveClientA, ClientAId, _valueA);
    }

    private void OnClientBReducerCallSucceeded(ReducerCallResult result)
    {
        if (_finished || result == null || result.ReducerName != "ping_insert")
            return;

        if (_currentStep != Step.InvokeClientB)
            return;

        EmitStepOk("invoke_client_b", new Dictionary<string, object?>
        {
            ["client_id"] = ClientBId,
            ["reducer"] = result.ReducerName,
            ["invocation_id"] = result.InvocationId,
        });
        StartObservation(Step.ObserveClientB, ClientBId, _valueB);
    }

    private void OnSubscriptionFailed(SubscriptionFailedEvent failedEvent)
    {
        if (_finished)
            return;

        EmitError(StepName(_currentStep), "SubscriptionFailed signal fired.");
        Finish(pass: false);
    }

    private void OnReducerCallFailed(ReducerCallError error)
    {
        if (_finished || error == null)
            return;

        EmitError(
            StepName(_currentStep),
            $"{error.ReducerName}: {error.ErrorMessage} ({error.FailureCategory})");
        Finish(pass: false);
    }

    private void StartObservation(Step step, string observedClientId, string expectedValue)
    {
        _currentObservedClientId = observedClientId;
        _currentExpectedValue = expectedValue;
        _sawTypedTableHandle = false;
        _sawGetRows = false;
        // Replay any RowChanged events that already fired for this (client, value)
        // pair. The SDK dispatches row-change callbacks ahead of the reducer-success
        // callback for the same TransactionUpdate, so by the time observation starts
        // the insert signal has typically already arrived and is recorded in
        // _observedInsertKeys; gating _sawRowChangedEvent on a future signal would
        // deadlock waiting for a signal that will not fire again.
        _sawRowChangedEvent = _observedInsertKeys.Contains(InsertKey(observedClientId, expectedValue));
        _crossTalkCount = 0;
        foreach (var key in _observedInsertKeys)
        {
            if (key.EndsWith("|" + expectedValue, StringComparison.Ordinal) &&
                !key.StartsWith(observedClientId + "|", StringComparison.Ordinal))
            {
                _crossTalkCount++;
            }
        }
        StartStep(step);
        CheckObservationViaTypedTableHandle();
        CheckObservationViaGetRows();
        TryCompleteObservation();
    }

    private void OnClientARowChanged(RowChangedEvent rowEvent) =>
        HandleRowChanged(ClientAId, rowEvent);

    private void OnClientBRowChanged(RowChangedEvent rowEvent) =>
        HandleRowChanged(ClientBId, rowEvent);

    private void HandleRowChanged(string clientId, RowChangedEvent rowEvent)
    {
        if (_finished || rowEvent == null)
            return;

        if (rowEvent.TableName != "SmokeTest" || rowEvent.ChangeType != RowChangeType.Insert)
            return;

        var observedValue = ExtractRowValue(rowEvent.NewRow);
        if (observedValue == null)
            return;

        _observedInsertKeys.Add(InsertKey(clientId, observedValue));

        if (_currentStep is not Step.ObserveClientA and not Step.ObserveClientB)
            return;

        if (observedValue != _currentExpectedValue)
            return;

        if (clientId == _currentObservedClientId)
            _sawRowChangedEvent = true;
        else
            _crossTalkCount++;

        CheckObservationViaTypedTableHandle();
        CheckObservationViaGetRows();
        TryCompleteObservation();
    }

    private static string InsertKey(string clientId, string value) => clientId + "|" + value;

    private void CheckObservationViaTypedTableHandle()
    {
        if (_sawTypedTableHandle)
            return;

        try
        {
            if (_currentObservedClientId == ClientAId)
            {
                var db = _clientA!.GetDb<DefaultBindings.RemoteTables>();
                if (db != null && ContainsValue(db.SmokeTest.Iter(), _currentExpectedValue))
                    _sawTypedTableHandle = true;
            }
            else if (_currentObservedClientId == ClientBId)
            {
                var db = _clientB!.GetDb<MultiBindings.RemoteTables>();
                if (db != null && ContainsValue(db.SmokeTest.Iter(), _currentExpectedValue))
                    _sawTypedTableHandle = true;
            }
        }
        catch (Exception ex)
        {
            EmitError(StepName(_currentStep), "typed table handle threw: " + ex.Message);
            Finish(pass: false);
        }
    }

    private void CheckObservationViaGetRows()
    {
        if (_sawGetRows)
            return;

        try
        {
            var rows = _currentObservedClientId == ClientAId
                ? _clientA!.GetRows("SmokeTest")
                : _clientB!.GetRows("SmokeTest");
            if (ContainsValue(rows, _currentExpectedValue))
                _sawGetRows = true;
        }
        catch (Exception ex)
        {
            EmitError(StepName(_currentStep), "GetRows threw: " + ex.Message);
            Finish(pass: false);
        }
    }

    private void TryCompleteObservation()
    {
        if (_finished || _currentStep is not Step.ObserveClientA and not Step.ObserveClientB)
            return;

        if (!_sawTypedTableHandle || !_sawGetRows || !_sawRowChangedEvent)
            return;

        if (_crossTalkCount != 0)
        {
            EmitError(
                StepName(_currentStep),
                $"unexpected cross-talk count {_crossTalkCount} while observing {_currentObservedClientId}.");
            Finish(pass: false);
            return;
        }

        var stepName = _currentObservedClientId == ClientAId ? "observe_client_a" : "observe_client_b";
        EmitStepOk(stepName, new Dictionary<string, object?>
        {
            ["client_id"] = _currentObservedClientId,
            ["value"] = _currentExpectedValue,
            ["cross_talk_count"] = _crossTalkCount,
            ["via"] = new[] { "typed_table_handle", "get_rows", "row_changed_event" },
        });

        if (_currentObservedClientId == ClientAId)
        {
            StartStep(Step.DisconnectClientA);
            _expectClientADisconnect = true;
            _clientA!.Disconnect();
        }
        else
        {
            StartStep(Step.ReconnectClientA);
            _clientA!.Connect();
        }
    }

    private void AssertClientBStillConnected()
    {
        if (_clientB?.CurrentStatus.State != ConnectionState.Connected)
        {
            EmitError(
                "assert_client_b_still_connected",
                $"client B state is {_clientB?.CurrentStatus.State.ToString() ?? "null"} instead of Connected.");
            Finish(pass: false);
            return;
        }

        EmitStepOk("assert_client_b_still_connected", new Dictionary<string, object?>
        {
            ["client_id"] = ClientBId,
            ["state"] = _clientB.CurrentStatus.State.ToString(),
        });

        StartStep(Step.InvokeClientB);
        InvokeClientB();
    }

    private static string[] ExtractTableNames(RowReceiver? receiver)
    {
        if (receiver == null)
            return Array.Empty<string>();

        foreach (var property in receiver._GetPropertyList())
        {
            if (!property.TryGetValue("name", out var nameValue) ||
                !string.Equals(nameValue.ToString(), "TableName", StringComparison.Ordinal))
            {
                continue;
            }

            if (!property.TryGetValue("hint_string", out var hintValue))
                return Array.Empty<string>();

            return (hintValue.ToString() ?? "")
                .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        }

        return Array.Empty<string>();
    }

    private static bool ContainsValue(IEnumerable<object> rows, string expectedValue)
    {
        foreach (var row in rows)
        {
            if (ExtractRowValue(row) == expectedValue)
                return true;
        }

        return false;
    }

    private static string? ExtractRowValue(object? row)
    {
        if (row == null)
            return null;

        if (row is DefaultBindings.SmokeTest typedDefault)
            return typedDefault.Value;

        if (row is MultiBindings.SmokeTest typedMulti)
            return typedMulti.Value;

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

    private void StartStep(Step step)
    {
        _currentStep = step;
        _stepStartedAt = Time.GetTicksMsec() / 1000.0;
    }

    private static string StepName(Step step) => step switch
    {
        Step.VerifyRowReceiverModuleSelection => "verify_rowreceiver_module_selection",
        Step.ConnectClientA => "connect_client_a",
        Step.ConnectClientB => "connect_client_b",
        Step.LookupClients => "lookup_clients",
        Step.SubscribeClientA => "subscribe_client_a",
        Step.SubscribeClientB => "subscribe_client_b",
        Step.InvokeClientA => "invoke_client_a",
        Step.ObserveClientA => "observe_client_a",
        Step.DisconnectClientA => "disconnect_client_a",
        Step.AssertClientBStillConnected => "assert_client_b_still_connected",
        Step.InvokeClientB => "invoke_client_b",
        Step.ObserveClientB => "observe_client_b",
        Step.ReconnectClientA => "reconnect_client_a",
        Step.ResubscribeClientA => "resubscribe_client_a",
        Step.Done => "done",
        _ => "unknown",
    };

    private static void EmitStepOk(string name, Dictionary<string, object?> payload)
    {
        payload["event"] = "step";
        payload["name"] = name;
        payload["status"] = "ok";
        Console.WriteLine(EventPrefix + JsonSerializer.Serialize(payload));
    }

    private static void EmitError(string step, string reason)
    {
        Console.WriteLine(EventPrefix + JsonSerializer.Serialize(new Dictionary<string, object?>
        {
            ["event"] = "step",
            ["name"] = step,
            ["status"] = "error",
            ["reason"] = reason,
        }));
    }

    private void Finish(bool pass)
    {
        if (_finished)
            return;

        _finished = true;
        _currentStep = Step.Done;
        Console.WriteLine(EventPrefix + JsonSerializer.Serialize(new Dictionary<string, object?>
        {
            ["event"] = "done",
            ["status"] = pass ? "pass" : "fail",
        }));
        GetTree().Quit(pass ? 0 : 1);
    }
}

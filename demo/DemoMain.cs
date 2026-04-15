using System.Linq;
using Godot;
using GodotSpacetime;
using GodotSpacetime.Connection;
using GodotSpacetime.Reducers;
using GodotSpacetime.Runtime.Auth;
using GodotSpacetime.Subscriptions;
using SpacetimeDB.Types;

namespace GodotSpacetime.Demo;

/// <summary>Demo scene extended through Story 5.2 — wires auth token persistence, subscription to smoke_test, and row-change observation. Story 5.3 — wires reducer invocation (Ping) and result handling via ReducerCallSucceeded / ReducerCallFailed signals.</summary>
public partial class DemoMain : Node
{
    private SpacetimeClient? _client;
    private GodotSpacetime.Subscriptions.SubscriptionHandle? _subscriptionHandle;

    public override void _Ready()
    {
        _client = GetNode<SpacetimeClient>("/root/SpacetimeClient");

        _client.ConnectionStateChanged -= OnConnectionStateChanged;
        _client.ConnectionStateChanged += OnConnectionStateChanged;

        _client.ConnectionOpened -= OnConnectionOpened;
        _client.ConnectionOpened += OnConnectionOpened;

        _client.ConnectionClosed -= OnConnectionClosed;
        _client.ConnectionClosed += OnConnectionClosed;

        _client.SubscriptionApplied -= OnSubscriptionApplied;
        _client.SubscriptionApplied += OnSubscriptionApplied;

        _client.SubscriptionFailed -= OnSubscriptionFailed;
        _client.SubscriptionFailed += OnSubscriptionFailed;

        _client.RowChanged -= OnRowChanged;
        _client.RowChanged += OnRowChanged;

        _client.ReducerCallSucceeded -= OnReducerCallSucceeded;
        _client.ReducerCallSucceeded += OnReducerCallSucceeded;

        _client.ReducerCallFailed -= OnReducerCallFailed;
        _client.ReducerCallFailed += OnReducerCallFailed;

        if (_client.Settings != null)
            _client.Settings.TokenStore = new ProjectSettingsTokenStore();

        _client.Connect();
    }

    public override void _ExitTree()
    {
        if (_client != null)
        {
            _client.ConnectionStateChanged -= OnConnectionStateChanged;
            _client.ConnectionOpened -= OnConnectionOpened;
            _client.ConnectionClosed -= OnConnectionClosed;
            _client.SubscriptionApplied -= OnSubscriptionApplied;
            _client.SubscriptionFailed -= OnSubscriptionFailed;
            _client.RowChanged -= OnRowChanged;
            _client.ReducerCallSucceeded -= OnReducerCallSucceeded;
            _client.ReducerCallFailed -= OnReducerCallFailed;
        }

        if (_subscriptionHandle != null && _subscriptionHandle.Status == SubscriptionStatus.Active)
            _client?.Unsubscribe(_subscriptionHandle);

        _subscriptionHandle = null;
    }

    private void OnConnectionStateChanged(ConnectionStatus status)
    {
        GD.Print($"[Demo] Connection state: {status.Description}");

        if (status.State == ConnectionState.Connected &&
            (_subscriptionHandle == null || _subscriptionHandle.Status != SubscriptionStatus.Active))
        {
            _subscriptionHandle = _client!.Subscribe(new[] { "SELECT * FROM smoke_test" });
            GD.Print("[Demo] Subscribed to smoke_test — awaiting initial sync");
        }
    }

    private void OnConnectionOpened(ConnectionOpenedEvent e)
    {
        GD.Print($"[Demo] Session identity: {(string.IsNullOrEmpty(e.Identity) ? "(new — token will be stored)" : e.Identity)}");
    }

    private void OnConnectionClosed(ConnectionClosedEvent e)
    {
        _subscriptionHandle = null;
    }

    private void OnSubscriptionApplied(SubscriptionAppliedEvent e)
    {
        if (_subscriptionHandle != e.Handle)
            return;

        var rows = _client!.GetRows("SmokeTest").ToList();
        GD.Print($"[Demo] Subscription applied — {rows.Count} row(s) in smoke_test");
        _client!.InvokeReducer(new Reducer.Ping());
        GD.Print("[Demo] Ping reducer invoked — awaiting server acknowledgement");
    }

    private void OnSubscriptionFailed(SubscriptionFailedEvent e)
    {
        if (_subscriptionHandle == e.Handle)
            _subscriptionHandle = null;

        GD.Print($"[Demo] Subscription failed: {e.ErrorMessage}");
    }

    private void OnRowChanged(RowChangedEvent e)
    {
        GD.Print($"[Demo] Row changed — table: {e.TableName}, type: {e.ChangeType}");
    }

    private void OnReducerCallSucceeded(ReducerCallResult result)
    {
        GD.Print($"[Demo] Reducer '{result.ReducerName}' succeeded (id: {result.InvocationId})");
    }

    private void OnReducerCallFailed(ReducerCallError error)
    {
        GD.Print($"[Demo] Reducer '{error.ReducerName}' failed — {error.FailureCategory}: {error.ErrorMessage} | guidance: {error.RecoveryGuidance}");
    }
}

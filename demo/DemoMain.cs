using System.Linq;
using Godot;
using GodotSpacetime;
using GodotSpacetime.Connection;
using GodotSpacetime.Runtime.Auth;
using GodotSpacetime.Subscriptions;

namespace GodotSpacetime.Demo;

/// <summary>Demo scene extended through Story 5.2 — wires auth token persistence, subscription to smoke_test, and row-change observation. Story 5.3 adds reducer interaction.</summary>
public partial class DemoMain : Node
{
    private SpacetimeClient? _client;
    private SubscriptionHandle? _subscriptionHandle;

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
}

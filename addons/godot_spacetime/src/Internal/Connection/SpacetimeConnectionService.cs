using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using GodotSpacetime.Auth;
using GodotSpacetime.Connection;
using GodotSpacetime.Runtime.Cache;
using GodotSpacetime.Runtime.Platform.DotNet;
using GodotSpacetime.Subscriptions;
using GodotSpacetime.Runtime.Subscriptions;

namespace GodotSpacetime.Runtime.Connection;

internal sealed class SpacetimeConnectionService : IConnectionEventSink, ISubscriptionEventSink, IRowChangeEventSink
{
    private readonly ConnectionStateMachine _stateMachine = new();
    private readonly ReconnectPolicy _reconnectPolicy = new();
    private readonly SpacetimeSdkConnectionAdapter _adapter = new();
    private string _host = string.Empty;
    private string _database = string.Empty;
    private ITokenStore? _tokenStore;
    private bool _credentialsProvided;
    private bool _restoredFromStore;
    private readonly SpacetimeSdkSubscriptionAdapter _subscriptionAdapter = new();
    private readonly SubscriptionRegistry _subscriptionRegistry = new();
    private readonly CacheViewAdapter _cacheViewAdapter = new();
    private readonly SpacetimeSdkRowCallbackAdapter _rowCallbackAdapter = new();

    public SpacetimeConnectionService()
    {
        _stateMachine.StateChanged += status => OnStateChanged?.Invoke(status);
    }

    public event Action<ConnectionStatus>? OnStateChanged;

    public event Action<ConnectionOpenedEvent>? OnConnectionOpened;

    public event Action<SubscriptionAppliedEvent>? OnSubscriptionApplied;

    public event Action<RowChangedEvent>? OnRowChanged;

    public ConnectionStatus CurrentStatus => _stateMachine.CurrentStatus;

    public void Connect(SpacetimeSettings settings)
    {
        ArgumentNullException.ThrowIfNull(settings);
        ValidateSettings(settings);

        if (CurrentStatus.State != ConnectionState.Disconnected)
            Disconnect("DISCONNECTED — closing the previous session before reconnecting.");

        _host = settings.Host.Trim();
        _database = settings.Database.Trim();
        _tokenStore = settings.TokenStore;
        var restoredCredentials = false;

        // Story 2.3: restore a previous session from the token store when no explicit credentials are set
        if (settings.TokenStore != null && string.IsNullOrWhiteSpace(settings.Credentials))
        {
            try
            {
                var stored = settings.TokenStore.GetTokenAsync().GetAwaiter().GetResult();
                if (!string.IsNullOrWhiteSpace(stored))
                {
                    settings.Credentials = stored;
                    restoredCredentials = true;
                }
            }
            catch (Exception)
            {
                // Token restoration failure is non-fatal — proceed without credentials
            }
        }

        _credentialsProvided = !string.IsNullOrWhiteSpace(settings.Credentials);
        _restoredFromStore = restoredCredentials;   // ← track source of credentials for failure routing
        _reconnectPolicy.Reset();

        _stateMachine.Transition(ConnectionState.Connecting, $"CONNECTING — opening a session to {_host}/{_database}");

        try
        {
            _adapter.Open(settings, this);
        }
        catch (Exception ex)
        {
            ResetDisconnectedSessionState();
            _stateMachine.Transition(ConnectionState.Disconnected, $"DISCONNECTED — failed to start the connection: {ex.Message}");
            throw;
        }
        finally
        {
            // Restored tokens are injected only for this connect attempt so clearing the token store
            // still resets future connects when the same settings resource is reused.
            if (restoredCredentials)
                settings.Credentials = null;
        }
    }

    public void Disconnect()
    {
        Disconnect("DISCONNECTED — not connected to SpacetimeDB");
    }

    public SubscriptionHandle Subscribe(string[] querySqls)
    {
        if (CurrentStatus.State != ConnectionState.Connected)
            throw new InvalidOperationException(
                "Subscribe() requires an active Connected session. " +
                "Call Connect() and wait for ConnectionState.Connected before applying subscriptions.");

        var connection = _adapter.Connection
            ?? throw new InvalidOperationException(
                "Not connected — no active IDbConnection. Call Connect() first.");

        var handle = new SubscriptionHandle();
        _subscriptionRegistry.Register(handle);

        try
        {
            _subscriptionAdapter.Subscribe(connection, querySqls, this, handle);
            return handle;
        }
        catch
        {
            _subscriptionRegistry.Unregister(handle.HandleId);
            throw;
        }
    }

    public IEnumerable<object> GetRows(string tableName) => _cacheViewAdapter.GetRows(tableName);

    public void FrameTick()
    {
        if (CurrentStatus.State == ConnectionState.Disconnected)
            return;

        _adapter.FrameTick();
    }

    void IConnectionEventSink.OnConnected(string identity, string token)
    {
        _reconnectPolicy.Reset();
        _cacheViewAdapter.SetDb(_adapter.GetDb());   // wire cache view on connect
        var db = _adapter.GetDb();                   // wire row callbacks
        if (db != null)
            _rowCallbackAdapter.RegisterCallbacks(db, this);
        if (_tokenStore != null)
        {
            // Optional token persistence must never break a successful connection.
            try
            {
                _ = _tokenStore.StoreTokenAsync(token).ContinueWith(
                    static completedTask => _ = completedTask.Exception,
                    CancellationToken.None,
                    TaskContinuationOptions.OnlyOnFaulted | TaskContinuationOptions.ExecuteSynchronously,
                    TaskScheduler.Default
                );
            }
            catch (Exception)
            {
            }
        }

        var authState = _credentialsProvided ? ConnectionAuthState.TokenRestored : ConnectionAuthState.None;

        if (CurrentStatus.State != ConnectionState.Connected)
        {
            var description = CurrentStatus.State == ConnectionState.Degraded
                ? "CONNECTED — active session established after recovery"
                : _credentialsProvided
                    ? "CONNECTED — authenticated session established"
                    : "CONNECTED — active session established";
            _stateMachine.Transition(ConnectionState.Connected, description, authState);
        }

        OnConnectionOpened?.Invoke(
            new ConnectionOpenedEvent
            {
                Host = _host,
                Database = _database,
                Identity = identity,
                ConnectedAt = DateTimeOffset.UtcNow,
            }
        );
    }

    void IConnectionEventSink.OnConnectError(Exception error)
    {
        ClearCacheView();

        if (CurrentStatus.State == ConnectionState.Connecting)
        {
            ResetDisconnectedSessionState();
            if (_restoredFromStore)
            {
                _stateMachine.Transition(
                    ConnectionState.Disconnected,
                    $"DISCONNECTED — stored token was rejected: {error.Message}",
                    ConnectionAuthState.TokenExpired
                );
            }
            else if (_credentialsProvided)
            {
                _stateMachine.Transition(
                    ConnectionState.Disconnected,
                    $"DISCONNECTED — authentication failed: {error.Message}",
                    ConnectionAuthState.AuthFailed
                );
            }
            else
            {
                _stateMachine.Transition(
                    ConnectionState.Disconnected,
                    $"DISCONNECTED — failed to connect: {error.Message}"
                );
            }
            return;
        }

        HandleDisconnectError(error);
    }

    void IConnectionEventSink.OnDisconnected(Exception? error)
    {
        if (error == null)
        {
            Disconnect("DISCONNECTED — not connected to SpacetimeDB");
            return;
        }

        HandleDisconnectError(error);
    }

    void ISubscriptionEventSink.OnSubscriptionApplied(SubscriptionHandle handle)
    {
        OnSubscriptionApplied?.Invoke(new SubscriptionAppliedEvent(handle));
    }

    void ISubscriptionEventSink.OnSubscriptionError(SubscriptionHandle handle, Exception error)
    {
        // Subscription failure recovery is implemented in Story 3.5.
        // The error is observable via the SpacetimeDB SDK log output at the Platform/DotNet boundary.
    }

    void IRowChangeEventSink.OnRowInserted(string tableName, object row)
    {
        OnRowChanged?.Invoke(new RowChangedEvent(tableName, RowChangeType.Insert, null, row));
    }

    void IRowChangeEventSink.OnRowDeleted(string tableName, object row)
    {
        OnRowChanged?.Invoke(new RowChangedEvent(tableName, RowChangeType.Delete, row, null));
    }

    void IRowChangeEventSink.OnRowUpdated(string tableName, object oldRow, object newRow)
    {
        OnRowChanged?.Invoke(new RowChangedEvent(tableName, RowChangeType.Update, oldRow, newRow));
    }

    private void HandleDisconnectError(Exception error)
    {
        ClearCacheView();

        if (CurrentStatus.State == ConnectionState.Connected && _reconnectPolicy.TryBeginRetry(out var attemptNumber, out var delay))
        {
            _stateMachine.Transition(
                ConnectionState.Degraded,
                $"DEGRADED — session experiencing issues; reconnecting (attempt {attemptNumber}/{_reconnectPolicy.MaxAttempts}, backoff {delay.TotalSeconds:0.#}s): {error.Message}"
            );
            return;
        }

        ResetDisconnectedSessionState();
        _stateMachine.Transition(ConnectionState.Disconnected, $"DISCONNECTED — connection lost: {error.Message}");
    }

    private void Disconnect(string description)
    {
        ResetDisconnectedSessionState();

        if (CurrentStatus.State != ConnectionState.Disconnected)
            _stateMachine.Transition(ConnectionState.Disconnected, description);
    }

    private void ClearCacheView() => _cacheViewAdapter.SetDb(null);

    private void ResetDisconnectedSessionState()
    {
        _subscriptionRegistry.Clear();
        ClearCacheView();
        _adapter.Close();
        _reconnectPolicy.Reset();
    }

    private static void ValidateSettings(SpacetimeSettings settings)
    {
        if (string.IsNullOrWhiteSpace(settings.Host))
        {
            throw new ArgumentException(
                "Host is required before connecting.",
                nameof(SpacetimeSettings.Host)
            );
        }

        if (string.IsNullOrWhiteSpace(settings.Database))
        {
            throw new ArgumentException(
                "Database is required before connecting.",
                nameof(SpacetimeSettings.Database)
            );
        }
    }
}

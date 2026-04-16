using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using GodotSpacetime.Auth;
using GodotSpacetime.Connection;
using GodotSpacetime.Queries;
using GodotSpacetime.Reducers;
using GodotSpacetime.Runtime.Cache;
using GodotSpacetime.Runtime.Platform.DotNet;
using GodotSpacetime.Subscriptions;
using GodotSpacetime.Runtime.Reducers;
using GodotSpacetime.Runtime.Subscriptions;

namespace GodotSpacetime.Runtime.Connection;

internal sealed class SpacetimeConnectionService : IConnectionEventSink, IConnectionTelemetrySink, ISubscriptionEventSink, IRowChangeEventSink, IReducerEventSink
{
    private readonly ConnectionStateMachine _stateMachine = new();
    private readonly ReconnectPolicy _reconnectPolicy = new();
    private readonly SpacetimeSdkConnectionAdapter _adapter = new();
    private readonly ConnectionTelemetryCollector _telemetryCollector = new();
    private string _host = string.Empty;
    private string _database = string.Empty;
    private ITokenStore? _tokenStore;
    private bool _credentialsProvided;
    private bool _restoredFromStore;
    private bool _isTearingDownConnection;
    private MessageCompressionMode _activeCompressionMode = MessageCompressionMode.None;
    private readonly SpacetimeSdkSubscriptionAdapter _subscriptionAdapter = new();
    private readonly SubscriptionRegistry _subscriptionRegistry = new();
    private readonly CacheViewAdapter _cacheViewAdapter = new();
    private readonly SpacetimeSdkRowCallbackAdapter _rowCallbackAdapter = new();
    private readonly SpacetimeSdkReducerAdapter _reducerAdapter = new();
    private readonly SpacetimeSdkQueryAdapter _queryAdapter = new();
    private readonly ReducerInvoker _reducerInvoker;

    /// <summary>
    /// Maps newHandleId → oldHandleId for in-flight overlap-first subscription replacements.
    /// When the new subscription's OnSubscriptionApplied fires, the old subscription is closed.
    /// When the new subscription errors, the old subscription is left untouched.
    /// </summary>
    private readonly Dictionary<Guid, Guid> _pendingReplacements = new();

    public SpacetimeConnectionService()
    {
        _reducerInvoker = new ReducerInvoker(_reducerAdapter);
        _stateMachine.StateChanged += status => OnStateChanged?.Invoke(status);
    }

    public event Action<ConnectionStatus>? OnStateChanged;

    public event Action<ConnectionOpenedEvent>? OnConnectionOpened;

    public event Action<ConnectionClosedEvent>? OnConnectionClosed;

    public event Action<SubscriptionAppliedEvent>? OnSubscriptionApplied;

    public event Action<SubscriptionFailedEvent>? OnSubscriptionFailed;

    public event Action<RowChangedEvent>? OnRowChanged;

    public event Action<ReducerCallResult>? OnReducerCallSucceeded;

    public event Action<ReducerCallError>? OnReducerCallFailed;

    public ConnectionStatus CurrentStatus => _stateMachine.CurrentStatus;

    public ConnectionTelemetryStats CurrentTelemetry
    {
        get
        {
            var trackerCounts = _adapter.ReadTrackerCounts();
            _telemetryCollector.UpdateTrackerCounts(trackerCounts.MessagesSent, trackerCounts.MessagesReceived);
            return _telemetryCollector.CurrentTelemetry;
        }
    }

    internal bool TelemetryBytesSentProven => _telemetryCollector.HasProvenOutboundBytes;

    internal string TelemetryBytesSentSource => _telemetryCollector.BytesSentSource;

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
        _activeCompressionMode = SpacetimeSdkConnectionAdapter.GetEffectiveCompressionMode(settings.CompressionMode);

        _stateMachine.Transition(
            ConnectionState.Connecting,
            $"CONNECTING — opening a session to {_host}/{_database}",
            activeCompressionMode: _activeCompressionMode);

        try
        {
            _adapter.Open(settings, this);
        }
        catch (Exception ex)
        {
            RunConnectionTeardown(() =>
            {
                ResetDisconnectedSessionState();
                _stateMachine.Transition(
                    ConnectionState.Disconnected,
                    $"DISCONNECTED — failed to start the connection: {ex.Message}",
                    activeCompressionMode: _activeCompressionMode
                );
            });
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
            var sdkSub = _subscriptionAdapter.Subscribe(connection, querySqls, this, handle);
            _subscriptionRegistry.UpdateSdkSubscription(handle.HandleId, sdkSub);
            _telemetryCollector.RecordOutboundMessage(_subscriptionAdapter.MeasureSubscribePayloadBytes(querySqls));
            return handle;
        }
        catch
        {
            _subscriptionRegistry.Unregister(handle.HandleId);
            throw;
        }
    }

    /// <summary>
    /// Closes a previously applied subscription scope.
    /// Safe to call when not connected — the handle is marked <c>Closed</c> and removed from the registry
    /// regardless, but the SDK-level close is only attempted while connected.
    /// Idempotent: calling with an already-<c>Closed</c> handle is a no-op.
    /// </summary>
    public void Unsubscribe(SubscriptionHandle handle)
    {
        ArgumentNullException.ThrowIfNull(handle);

        if (handle.Status == SubscriptionStatus.Closed)
            return;  // idempotent

        RemovePendingReplacementReferences(handle.HandleId);

        if (CurrentStatus.State == ConnectionState.Connected &&
            _subscriptionRegistry.TryGetEntry(handle.HandleId, out var entry))
        {
            if (_subscriptionAdapter.TryUnsubscribe(entry.SdkSubscription))
                _telemetryCollector.RecordOutboundMessage(_subscriptionAdapter.MeasureUnsubscribePayloadBytes());
        }

        handle.Close();
        _subscriptionRegistry.Unregister(handle.HandleId);
    }

    /// <summary>
    /// Replaces an active subscription with a new query set using overlap-first semantics.
    /// The old subscription remains authoritative until the new subscription is confirmed applied.
    /// If the new subscription errors before being applied, the old subscription is NOT closed.
    /// </summary>
    /// <param name="oldHandle">The currently active subscription handle to replace.</param>
    /// <param name="newQueries">The new SQL query set for the replacement subscription.</param>
    /// <returns>A new <see cref="SubscriptionHandle"/> for the in-flight replacement subscription.</returns>
    public SubscriptionHandle ReplaceSubscription(SubscriptionHandle oldHandle, string[] newQueries)
    {
        ArgumentNullException.ThrowIfNull(oldHandle);
        ArgumentNullException.ThrowIfNull(newQueries);

        if (CurrentStatus.State != ConnectionState.Connected)
            throw new InvalidOperationException(
                "ReplaceSubscription() requires an active Connected session.");

        if (oldHandle.Status != SubscriptionStatus.Active)
            throw new InvalidOperationException(
                "ReplaceSubscription() requires an Active subscription handle. " +
                $"The provided handle has status: {oldHandle.Status}.");

        if (HasPendingReplacementInFlight(oldHandle.HandleId))
            throw new InvalidOperationException(
                "ReplaceSubscription() requires a currently authoritative handle without another " +
                "replacement already in flight.");

        var connection = _adapter.Connection
            ?? throw new InvalidOperationException(
                "Not connected — no active IDbConnection.");

        var newHandle = new SubscriptionHandle();
        _subscriptionRegistry.Register(newHandle);

        // Wire the overlap-first replacement hook: when newHandle is applied, close oldHandle
        _pendingReplacements[newHandle.HandleId] = oldHandle.HandleId;

        try
        {
            var sdkSub = _subscriptionAdapter.Subscribe(connection, newQueries, this, newHandle);
            _subscriptionRegistry.UpdateSdkSubscription(newHandle.HandleId, sdkSub);
            _telemetryCollector.RecordOutboundMessage(_subscriptionAdapter.MeasureSubscribePayloadBytes(newQueries));
            return newHandle;
        }
        catch
        {
            _pendingReplacements.Remove(newHandle.HandleId);
            _subscriptionRegistry.Unregister(newHandle.HandleId);
            throw;
        }
    }

    public TDb? GetDb<TDb>() where TDb : class => _cacheViewAdapter.GetDb<TDb>();

    public IEnumerable<object> GetRows(string tableName) => _cacheViewAdapter.GetRows(tableName);

    public Task<TRow[]> QueryAsync<TRow>(string sqlClause, TimeSpan? timeout = null)
        where TRow : class
    {
        if (string.IsNullOrWhiteSpace(sqlClause))
            throw new ArgumentException("QueryAsync() requires a non-empty SQL clause.", nameof(sqlClause));

        if (CurrentStatus.State != ConnectionState.Connected)
            throw new InvalidOperationException(
                "QueryAsync() requires an active Connected session. " +
                "Call Connect() and wait for ConnectionState.Connected before issuing one-off queries.");

        var remoteTables = _adapter.GetDb()
            ?? throw new InvalidOperationException(
                "QueryAsync() requires an active generated RemoteTables session. " +
                "This is a programming fault — ensure the connection is fully established before querying.");

        var queryTask = _queryAdapter.QueryAsync<TRow>(remoteTables, sqlClause, timeout);
        _telemetryCollector.RecordOutboundMessage(_queryAdapter.MeasureQueryPayloadBytes(sqlClause));
        return queryTask;
    }

    public void InvokeReducer(object reducerArgs)
    {
        if (CurrentStatus.State != ConnectionState.Connected)
            throw new InvalidOperationException(
                "InvokeReducer() requires an active Connected session. " +
                "Call Connect() and wait for ConnectionState.Connected before invoking reducers.");

        var payloadBytes = _reducerAdapter.MeasurePayloadBytes(reducerArgs);
        _reducerInvoker.Invoke(reducerArgs);
        _telemetryCollector.RecordOutboundMessage(payloadBytes);
    }

    public void FrameTick()
    {
        if (CurrentStatus.State == ConnectionState.Disconnected)
            return;

        _adapter.FrameTick();
    }

    void IConnectionEventSink.OnConnected(string identity, string token)
    {
        _reconnectPolicy.Reset();
        _telemetryCollector.StartSession();
        _cacheViewAdapter.SetDb(_adapter.GetDb());   // wire cache view on connect
        _reducerAdapter.SetConnection(_adapter.Connection);  // wire reducer adapter on connect
        _reducerAdapter.RegisterCallbacks(this);             // wire reducer result callbacks
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

        // Once the server accepts the token, the "restored from store" distinction is no longer
        // relevant for failure classification. A subsequent Degraded→Disconnected is a network
        // issue, not a token-expiry event.
        _restoredFromStore = false;

        if (CurrentStatus.State != ConnectionState.Connected)
        {
            var description = CurrentStatus.State == ConnectionState.Degraded
                ? "CONNECTED — active session established after recovery"
                : _credentialsProvided
                    ? "CONNECTED — authenticated session established"
                    : "CONNECTED — active session established";
            _stateMachine.Transition(
                ConnectionState.Connected,
                description,
                authState,
                _activeCompressionMode);
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
            RunConnectionTeardown(() =>
            {
                ResetDisconnectedSessionState();
                if (_restoredFromStore)
                {
                    _stateMachine.Transition(
                        ConnectionState.Disconnected,
                        $"DISCONNECTED — stored token was rejected: {error.Message}",
                        ConnectionAuthState.TokenExpired,
                        _activeCompressionMode
                    );
                    return;
                }

                if (_credentialsProvided)
                {
                    var authState = IsLikelyAuthError(error)
                        ? ConnectionAuthState.AuthFailed
                        : ConnectionAuthState.ConnectFailed;
                    var label = authState == ConnectionAuthState.AuthFailed
                        ? "authentication failed"
                        : "connection failed (credentials were provided but the cause is ambiguous)";
                    _stateMachine.Transition(
                        ConnectionState.Disconnected,
                        $"DISCONNECTED — {label}: {error.Message}",
                        authState,
                        _activeCompressionMode
                    );
                    return;
                }

                _stateMachine.Transition(
                    ConnectionState.Disconnected,
                    $"DISCONNECTED — failed to connect: {error.Message}",
                    activeCompressionMode: _activeCompressionMode
                );
            });
            return;
        }

        HandleDisconnectError(error);
    }

    void IConnectionEventSink.OnDisconnected(Exception? error)
    {
        if (_isTearingDownConnection || CurrentStatus.State == ConnectionState.Disconnected)
            return;

        if (error == null)
        {
            Disconnect("DISCONNECTED — not connected to SpacetimeDB");
            return;
        }

        HandleDisconnectError(error);
    }

    void ISubscriptionEventSink.OnSubscriptionApplied(SubscriptionHandle handle)
    {
        // Overlap-first replacement: if this is a pending replacement, close the old subscription now
        if (_pendingReplacements.TryGetValue(handle.HandleId, out var oldHandleId))
        {
            _pendingReplacements.Remove(handle.HandleId);

            if (_subscriptionRegistry.TryGetEntry(oldHandleId, out var oldEntry))
            {
                if (_subscriptionAdapter.TryUnsubscribe(oldEntry.SdkSubscription))
                    _telemetryCollector.RecordOutboundMessage(_subscriptionAdapter.MeasureUnsubscribePayloadBytes());
                oldEntry.Handle.Supersede();
                _subscriptionRegistry.Unregister(oldHandleId);
            }
        }

        OnSubscriptionApplied?.Invoke(new SubscriptionAppliedEvent(handle));
    }

    void ISubscriptionEventSink.OnSubscriptionError(SubscriptionHandle handle, Exception error)
    {
        // Remove pending replacement entry WITHOUT touching old handle — old remains active (AC: 5)
        RemovePendingReplacementReferences(handle.HandleId);

        if (_subscriptionRegistry.TryGetEntry(handle.HandleId, out var entry))
            _subscriptionAdapter.TryUnsubscribe(entry.SdkSubscription);

        _subscriptionRegistry.Unregister(handle.HandleId);
        handle.Close();
        OnSubscriptionFailed?.Invoke(new SubscriptionFailedEvent(handle, error));
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

    void IReducerEventSink.OnReducerCallSucceeded(string reducerName, string invocationId, DateTimeOffset calledAt)
    {
        _telemetryCollector.RecordReducerRoundTrip(calledAt, DateTimeOffset.UtcNow);
        OnReducerCallSucceeded?.Invoke(new ReducerCallResult(reducerName, invocationId, calledAt));
    }

    void IReducerEventSink.OnReducerCallFailed(
        string reducerName,
        string invocationId,
        DateTimeOffset calledAt,
        string errorMessage,
        ReducerFailureCategory failureCategory,
        string recoveryGuidance)
    {
        _telemetryCollector.RecordReducerRoundTrip(calledAt, DateTimeOffset.UtcNow);
        OnReducerCallFailed?.Invoke(new ReducerCallError(
            reducerName,
            invocationId,
            calledAt,
            errorMessage,
            failureCategory,
            recoveryGuidance));
    }

    private void HandleDisconnectError(Exception error)
    {
        ClearCacheView();

        if (CurrentStatus.State == ConnectionState.Connected && _reconnectPolicy.TryBeginRetry(out var attemptNumber, out var delay))
        {
            _stateMachine.Transition(
                ConnectionState.Degraded,
                $"DEGRADED — session experiencing issues; reconnecting (attempt {attemptNumber}/{_reconnectPolicy.MaxAttempts}, backoff {delay.TotalSeconds:0.#}s): {error.Message}",
                activeCompressionMode: _activeCompressionMode
            );
            return;
            // NO ConnectionClosed here — session is degraded, not ended
        }

        var disconnectAuthState = ClassifyDisconnectAuthState(error);
        RunConnectionTeardown(() =>
        {
            ResetDisconnectedSessionState();
            _stateMachine.Transition(
                ConnectionState.Disconnected,
                $"DISCONNECTED — connection lost: {error.Message}",
                disconnectAuthState,
                _activeCompressionMode
            );
        });
        OnConnectionClosed?.Invoke(new ConnectionClosedEvent
        {
            CloseReason = ConnectionCloseReason.Error,
            ErrorMessage = error.Message,
            ClosedAt = DateTimeOffset.UtcNow,
        });
    }

    private void Disconnect(string description)
    {
        var prevState = CurrentStatus.State;
        RunConnectionTeardown(() =>
        {
            ResetDisconnectedSessionState();
            if (CurrentStatus.State != ConnectionState.Disconnected)
                _stateMachine.Transition(ConnectionState.Disconnected, description, activeCompressionMode: _activeCompressionMode);
        });

        // Fire ConnectionClosed only for live sessions (Connected or Degraded).
        // The prevState check prevents false positives for Connecting→Disconnected failures.
        // Teardown reentrancy is handled by RunConnectionTeardown + the OnDisconnected guard.
        if (prevState is ConnectionState.Connected or ConnectionState.Degraded)
            OnConnectionClosed?.Invoke(new ConnectionClosedEvent
            {
                CloseReason = ConnectionCloseReason.Clean,
                ClosedAt = DateTimeOffset.UtcNow,
            });
    }

    private void ClearCacheView() => _cacheViewAdapter.SetDb(null);

    private void ResetDisconnectedSessionState()
    {
        _subscriptionRegistry.Clear();
        _pendingReplacements.Clear();
        ClearCacheView();
        _rowCallbackAdapter.ClearRegistration();
        _adapter.Close();
        _reducerAdapter.ClearConnection();
        _reconnectPolicy.Reset();
        _activeCompressionMode = MessageCompressionMode.None;
        _telemetryCollector.Reset();
    }

    void IConnectionTelemetrySink.OnInboundMessageReceived(int byteCount)
    {
        _telemetryCollector.RecordInboundMessage(byteCount);
    }

    private bool HasPendingReplacementInFlight(Guid handleId)
    {
        if (_pendingReplacements.ContainsKey(handleId))
            return true;

        foreach (var pendingOldHandleId in _pendingReplacements.Values)
        {
            if (pendingOldHandleId == handleId)
                return true;
        }

        return false;
    }

    private void RemovePendingReplacementReferences(Guid handleId)
    {
        _pendingReplacements.Remove(handleId);

        List<Guid>? pendingHandlesToRemove = null;
        foreach (var pair in _pendingReplacements)
        {
            if (pair.Value != handleId)
                continue;

            pendingHandlesToRemove ??= new List<Guid>();
            pendingHandlesToRemove.Add(pair.Key);
        }

        if (pendingHandlesToRemove == null)
            return;

        foreach (var pendingHandleId in pendingHandlesToRemove)
            _pendingReplacements.Remove(pendingHandleId);
    }

    private void RunConnectionTeardown(Action teardown)
    {
        var wasTearingDownConnection = _isTearingDownConnection;
        _isTearingDownConnection = true;
        try
        {
            teardown();
        }
        finally
        {
            _isTearingDownConnection = wasTearingDownConnection;
        }
    }

    private ConnectionAuthState ClassifyDisconnectAuthState(Exception error)
    {
        if (!_credentialsProvided)
            return ConnectionAuthState.None;

        if (_restoredFromStore)
            return ConnectionAuthState.TokenExpired;

        return IsLikelyAuthError(error)
            ? ConnectionAuthState.AuthFailed
            : ConnectionAuthState.ConnectFailed;
    }

    private static bool IsLikelyAuthError(Exception error)
    {
        for (var ex = error; ex != null; ex = ex.InnerException)
        {
            if (ex is HttpRequestException httpEx &&
                httpEx.StatusCode is HttpStatusCode.Unauthorized or HttpStatusCode.Forbidden)
                return true;
        }

        return false;
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

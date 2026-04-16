using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Godot;
using GodotSpacetime.Connection;
using GodotSpacetime.Queries;
using GodotSpacetime.Reducers;
using GodotSpacetime.Runtime.Connection;
using GodotSpacetime.Runtime.Events;
using GodotSpacetime.Subscriptions;

namespace GodotSpacetime;

/// <summary>
/// The top-level Godot-facing service boundary for the GodotSpacetime SDK.
///
/// Register this Node as an autoload in your <c>project.godot</c> to make it available
/// from any scene. Configure it with a <see cref="SpacetimeSettings"/> resource to point
/// it at your SpacetimeDB instance.
///
/// Concept vocabulary for all public SDK types is defined in
/// <c>docs/runtime-boundaries.md</c>. The intended workflow is:
/// <list type="bullet">
///   <item>Configure <see cref="SpacetimeSettings"/> (Host, Database)</item>
///   <item>Call Connect() — watch ConnectionState events for lifecycle transitions</item>
///   <item>Apply subscriptions — receive SubscriptionAppliedEvent when cache is ready, or SubscriptionFailedEvent when a request is rejected or later errors</item>
///   <item>Read cache via GetDb&lt;TDb&gt;() for direct typed table handles or GetRows() as a compatibility fallback — invoke reducers as needed</item>
///   <item>Issue one-off remote reads via QueryAsync&lt;TRow&gt;() after Connect() when gameplay needs typed server data without creating or mutating a subscription-backed cache slice</item>
/// </list>
/// </summary>
public partial class SpacetimeClient : Node
{
    public const string DefaultConnectionId = "SpacetimeClient";

    private static readonly StringName MessagesSentMonitorId = new("GodotSpacetime/Connection/MessagesSent");
    private static readonly StringName MessagesReceivedMonitorId = new("GodotSpacetime/Connection/MessagesReceived");
    private static readonly StringName BytesSentMonitorId = new("GodotSpacetime/Connection/BytesSent");
    private static readonly StringName BytesReceivedMonitorId = new("GodotSpacetime/Connection/BytesReceived");
    private static readonly StringName UptimeSecondsMonitorId = new("GodotSpacetime/Connection/UptimeSeconds");
    private static readonly StringName LastReducerRoundTripMonitorId = new("GodotSpacetime/Reducers/LastRoundTripMilliseconds");
    private static readonly object LiveClientsGate = new();
    private static readonly Dictionary<string, SpacetimeClient> LiveClients = new(StringComparer.Ordinal);
    private readonly SpacetimeConnectionService _connectionService = new();
    private ConnectionStatus _currentStatus = new(ConnectionState.Disconnected, "DISCONNECTED — not connected to SpacetimeDB");
    private GodotSignalAdapter? _signalAdapter;
    private string? _registeredConnectionId;

    [Signal]
    public delegate void ConnectionStateChangedEventHandler(ConnectionStatus status);

    [Signal]
    public delegate void ConnectionOpenedEventHandler(ConnectionOpenedEvent e);

    /// <summary>
    /// Emitted when a live connection session ends.
    /// Fires after <c>ConnectionStateChanged</c> transitions to <c>Disconnected</c>.
    /// <c>ConnectionCloseReason.Clean</c>: explicit <c>Disconnect()</c> or clean server-side close.
    /// <c>ConnectionCloseReason.Error</c>: session lost due to network or protocol error after being established.
    /// Does NOT fire for failed connect attempts — <c>ConnectionStateChanged</c> covers those via Disconnected state.
    /// </summary>
    [Signal]
    public delegate void ConnectionClosedEventHandler(ConnectionClosedEvent e);

    [Signal]
    public delegate void SubscriptionAppliedEventHandler(SubscriptionAppliedEvent e);

    [Signal]
    public delegate void SubscriptionFailedEventHandler(SubscriptionFailedEvent e);

    [Signal]
    public delegate void RowChangedEventHandler(RowChangedEvent e);

    /// <summary>
    /// Emitted when the server confirms a reducer invocation as committed.
    /// Arrives asynchronously — the signal fires in a later frame than <c>InvokeReducer()</c> was called,
    /// after <c>FrameTick</c> delivers the queued server message.
    /// Inspect <c>ReducerCallResult.InvocationId</c> to correlate the outcome to a specific reducer call.
    /// <c>GodotSignalAdapter</c> deferred dispatch ensures this fires on the main thread.
    /// </summary>
    [Signal]
    public delegate void ReducerCallSucceededEventHandler(ReducerCallResult result);

    /// <summary>
    /// Emitted when a reducer invocation is rejected or fails on the server.
    /// Arrives asynchronously — the signal fires in a later frame than <c>InvokeReducer()</c> was called.
    /// Inspect <c>ReducerCallError.InvocationId</c> to correlate the failure and
    /// <c>ReducerCallError.RecoveryGuidance</c> to branch on retry vs. user feedback paths.
    /// </summary>
    [Signal]
    public delegate void ReducerCallFailedEventHandler(ReducerCallError error);

    [Export]
    public SpacetimeSettings? Settings { get; set; }

    [Export]
    public string ConnectionId { get; set; } = DefaultConnectionId;

    public ConnectionStatus CurrentStatus => _currentStatus;

    public ConnectionTelemetryStats CurrentTelemetry => _connectionService.CurrentTelemetry;

    internal bool TelemetryBytesSentProven => _connectionService.TelemetryBytesSentProven;

    internal string TelemetryBytesSentSource => _connectionService.TelemetryBytesSentSource;

    public static bool TryGetClient(string connectionId, out SpacetimeClient? client)
    {
        var normalizedConnectionId = NormalizeConnectionId(connectionId);
        lock (LiveClientsGate)
            return LiveClients.TryGetValue(normalizedConnectionId, out client);
    }

    public static SpacetimeClient GetClientOrThrow(string connectionId)
    {
        if (TryGetClient(connectionId, out var client) && client != null)
            return client;

        var normalizedConnectionId = NormalizeConnectionId(connectionId);
        throw new InvalidOperationException(
            $"No live SpacetimeClient is registered with ConnectionId '{normalizedConnectionId}'.");
    }

    public override void _EnterTree()
    {
        RegisterLiveClient();
        _signalAdapter ??= new GodotSignalAdapter(this);
        if (OwnsPerformanceMonitors())
            RegisterPerformanceMonitors();
        _connectionService.OnStateChanged += HandleStateChanged;
        _connectionService.OnConnectionOpened += HandleConnectionOpened;
        _connectionService.OnConnectionClosed += HandleConnectionClosed;
        _connectionService.OnSubscriptionApplied += HandleSubscriptionApplied;
        _connectionService.OnSubscriptionFailed += HandleSubscriptionFailed;
        _connectionService.OnRowChanged += HandleRowChanged;
        _connectionService.OnReducerCallSucceeded += HandleReducerCallSucceeded;
        _connectionService.OnReducerCallFailed += HandleReducerCallFailed;
    }

    public override void _ExitTree()
    {
        _connectionService.OnStateChanged -= HandleStateChanged;
        _connectionService.OnConnectionOpened -= HandleConnectionOpened;
        _connectionService.OnConnectionClosed -= HandleConnectionClosed;
        _connectionService.OnSubscriptionApplied -= HandleSubscriptionApplied;
        _connectionService.OnSubscriptionFailed -= HandleSubscriptionFailed;
        _connectionService.OnRowChanged -= HandleRowChanged;
        _connectionService.OnReducerCallSucceeded -= HandleReducerCallSucceeded;
        _connectionService.OnReducerCallFailed -= HandleReducerCallFailed;
        if (OwnsPerformanceMonitors())
            RemovePerformanceMonitors();
        UnregisterLiveClient();
    }

    public void Connect()
    {
        if (Settings == null)
        {
            PublishValidationFailure("Assign a SpacetimeSettings resource before connecting.");
            return;
        }

        try
        {
            _connectionService.Connect(Settings);
        }
        catch (ArgumentException ex)
        {
            PublishValidationFailure(ex.Message);
        }
        catch (InvalidOperationException ex)
        {
            PublishValidationFailure(ex.Message);
        }
    }

    public void Disconnect()
    {
        _connectionService.Disconnect();
    }

    public SubscriptionHandle Subscribe(string[] querySqls)
    {
        return _connectionService.Subscribe(querySqls);
    }

    /// <summary>
    /// Closes a previously applied subscription scope.
    /// Safe to call when not connected — the handle is marked Closed regardless.
    /// Idempotent: calling with an already-Closed handle is a no-op.
    /// </summary>
    public void Unsubscribe(SubscriptionHandle handle)
    {
        try
        {
            _connectionService.Unsubscribe(handle);
        }
        catch (ArgumentException ex)
        {
            PublishValidationFailure(ex.Message);
        }
    }

    /// <summary>
    /// Replaces an active subscription with a new query set using overlap-first semantics.
    /// The old subscription remains authoritative until the new subscription is confirmed applied.
    /// If the replacement fails, the SubscriptionFailed signal fires for the new handle while the
    /// old subscription remains authoritative. Returns the new handle; the SubscriptionApplied
    /// signal fires when the replacement is live.
    /// </summary>
    public SubscriptionHandle? ReplaceSubscription(SubscriptionHandle oldHandle, string[] newQueries)
    {
        try
        {
            return _connectionService.ReplaceSubscription(oldHandle, newQueries);
        }
        catch (ArgumentException ex)
        {
            PublishValidationFailure(ex.Message);
            return null;
        }
        catch (InvalidOperationException ex)
        {
            PublishValidationFailure(ex.Message);
            return null;
        }
    }

    /// <summary>
    /// Returns the active generated cache view for direct typed table-handle reads.
    /// Call after the <c>SubscriptionApplied</c> signal fires and keep reads on the main-thread path
    /// already used by this SDK's lifecycle signals and <c>_Process()</c> loop.
    /// Returns <c>null</c> when no synchronized cache is active yet.
    /// This method does not expose raw <c>IDbConnection</c>; it returns only the generated cache view.
    /// </summary>
    public TDb? GetDb<TDb>() where TDb : class =>
        _connectionService.GetDb<TDb>();

    /// <summary>
    /// Returns the rows currently cached for the specified table.
    /// Use <c>GetDb&lt;TDb&gt;()</c> when consumer code can reference the generated <c>RemoteTables</c> type directly;
    /// keep <c>GetRows()</c> for backward-compatible table-name-based reads.
    /// Call after the <c>SubscriptionApplied</c> signal fires, then cast each row to the generated table type.
    /// </summary>
    public IEnumerable<object> GetRows(string tableName) =>
        _connectionService.GetRows(tableName);

    /// <summary>
    /// Executes a one-off remote query against the active generated table selected by <typeparamref name="TRow"/>.
    /// Use this after <c>ConnectionState.Connected</c> is reached when gameplay needs typed server data
    /// without creating a subscription or mutating the local cache returned by <c>GetDb&lt;TDb&gt;()</c> / <c>GetRows()</c>.
    /// The public signature stays typed by generated row class and does not expose raw
    /// <c>IDbConnection</c>, <c>DbConnection</c>, or <c>RemoteTableHandleBase&lt;,&gt;</c> types.
    /// Blank SQL, disconnected state, and unsupported row types remain explicit programming-fault exceptions.
    /// Recoverable runtime failures surface as <see cref="OneOffQueryError"/>.
    /// When <paramref name="timeout"/> is omitted, the SDK applies a default timeout so the query cannot await forever.
    /// </summary>
    public Task<TRow[]> QueryAsync<TRow>(string sqlClause, TimeSpan? timeout = null)
        where TRow : class =>
        _connectionService.QueryAsync<TRow>(sqlClause, timeout);

    /// <summary>
    /// Invokes a SpacetimeDB reducer through the supported generated reducer path.
    /// Pass a generated <c>IReducerArgs</c> instance from the module's generated bindings
    /// (e.g. the generated <c>Reducer.Ping</c> type for a <c>ping</c> reducer).
    /// The invocation is routed through <c>ReducerInvoker</c> → <c>SpacetimeSdkReducerAdapter</c> →
    /// the runtime SDK call.
    /// Must be called after <c>ConnectionState.Connected</c> is reached.
    /// Programming faults such as wrong connection state, <c>null</c> args, or a non-<c>IReducerArgs</c>
    /// object are caught and surfaced via <c>ConnectionStateChanged</c> plus <c>GD.PushError</c>.
    /// These faults do not raise <c>ReducerCallFailed</c>; reserve reducer result handlers for
    /// server-acknowledged outcomes.
    /// </summary>
    public void InvokeReducer(object reducerArgs)
    {
        try
        {
            _connectionService.InvokeReducer(reducerArgs);
        }
        catch (ArgumentNullException ex)
        {
            PublishValidationFailure(ex.Message);
        }
        catch (ArgumentException ex)
        {
            PublishValidationFailure(ex.Message);
        }
        catch (InvalidOperationException ex)
        {
            PublishValidationFailure(ex.Message);
        }
    }

    public override void _Process(double delta)
    {
        if (_currentStatus.State == ConnectionState.Disconnected)
            return;

        _connectionService.FrameTick();
    }

    private void RegisterPerformanceMonitors()
    {
        EnsurePerformanceMonitor(MessagesSentMonitorId, Callable.From<double>(GetMessagesSentMonitor));
        EnsurePerformanceMonitor(MessagesReceivedMonitorId, Callable.From<double>(GetMessagesReceivedMonitor));
        EnsurePerformanceMonitor(BytesSentMonitorId, Callable.From<double>(GetBytesSentMonitor));
        EnsurePerformanceMonitor(BytesReceivedMonitorId, Callable.From<double>(GetBytesReceivedMonitor));
        EnsurePerformanceMonitor(UptimeSecondsMonitorId, Callable.From<double>(GetUptimeSecondsMonitor));
        EnsurePerformanceMonitor(LastReducerRoundTripMonitorId, Callable.From<double>(GetLastReducerRoundTripMonitor));
    }

    private void RemovePerformanceMonitors()
    {
        RemovePerformanceMonitor(MessagesSentMonitorId);
        RemovePerformanceMonitor(MessagesReceivedMonitorId);
        RemovePerformanceMonitor(BytesSentMonitorId);
        RemovePerformanceMonitor(BytesReceivedMonitorId);
        RemovePerformanceMonitor(UptimeSecondsMonitorId);
        RemovePerformanceMonitor(LastReducerRoundTripMonitorId);
    }

    private static void EnsurePerformanceMonitor(StringName monitorId, Callable callable)
    {
        if (!Performance.HasCustomMonitor(monitorId))
            Performance.AddCustomMonitor(monitorId, callable);

        // Probe once to verify the monitor callable is queryable after registration.
        _ = Performance.GetCustomMonitor(monitorId);
    }

    private static void RemovePerformanceMonitor(StringName monitorId)
    {
        if (!Performance.HasCustomMonitor(monitorId))
            return;

        Performance.RemoveCustomMonitor(monitorId);
    }

    private double GetMessagesSentMonitor() => Math.Max(0, CurrentTelemetry.MessagesSent);

    private double GetMessagesReceivedMonitor() => Math.Max(0, CurrentTelemetry.MessagesReceived);

    private double GetBytesSentMonitor() => Math.Max(0, CurrentTelemetry.BytesSent);

    private double GetBytesReceivedMonitor() => Math.Max(0, CurrentTelemetry.BytesReceived);

    private double GetUptimeSecondsMonitor() => Math.Max(0, CurrentTelemetry.ConnectionUptimeSeconds);

    private double GetLastReducerRoundTripMonitor() => Math.Max(0, CurrentTelemetry.LastReducerRoundTripMilliseconds);

    private void PublishValidationFailure(string message)
    {
        HandleStateChanged(new ConnectionStatus(ConnectionState.Disconnected, message));
        GD.PushError(message);
    }

    private void HandleStateChanged(ConnectionStatus status)
    {
        _currentStatus = status;

        if (_signalAdapter == null)
        {
            EmitSignal(SignalName.ConnectionStateChanged, status);
            return;
        }

        _signalAdapter.Dispatch(() => EmitSignal(SignalName.ConnectionStateChanged, status));
    }

    private void HandleConnectionOpened(ConnectionOpenedEvent openedEvent)
    {
        if (_signalAdapter == null)
        {
            EmitSignal(SignalName.ConnectionOpened, openedEvent);
            return;
        }

        _signalAdapter.Dispatch(() => EmitSignal(SignalName.ConnectionOpened, openedEvent));
    }

    private void HandleConnectionClosed(ConnectionClosedEvent e)
    {
        if (_signalAdapter == null)
        {
            EmitSignal(SignalName.ConnectionClosed, e);
            return;
        }

        _signalAdapter.Dispatch(() => EmitSignal(SignalName.ConnectionClosed, e));
    }

    private void HandleSubscriptionApplied(SubscriptionAppliedEvent appliedEvent)
    {
        if (_signalAdapter == null)
        {
            EmitSignal(SignalName.SubscriptionApplied, appliedEvent);
            return;
        }

        _signalAdapter.Dispatch(() => EmitSignal(SignalName.SubscriptionApplied, appliedEvent));
    }

    private void HandleSubscriptionFailed(SubscriptionFailedEvent failedEvent)
    {
        if (_signalAdapter == null)
        {
            EmitSignal(SignalName.SubscriptionFailed, failedEvent);
            return;
        }

        _signalAdapter.Dispatch(() => EmitSignal(SignalName.SubscriptionFailed, failedEvent));
    }

    private void HandleRowChanged(RowChangedEvent rowChangedEvent)
    {
        if (_signalAdapter == null)
        {
            EmitSignal(SignalName.RowChanged, rowChangedEvent);
            return;
        }

        _signalAdapter.Dispatch(() => EmitSignal(SignalName.RowChanged, rowChangedEvent));
    }

    private void HandleReducerCallSucceeded(ReducerCallResult result)
    {
        if (_signalAdapter == null)
        {
            EmitSignal(SignalName.ReducerCallSucceeded, result);
            return;
        }

        _signalAdapter.Dispatch(() => EmitSignal(SignalName.ReducerCallSucceeded, result));
    }

    private void HandleReducerCallFailed(ReducerCallError error)
    {
        if (_signalAdapter == null)
        {
            EmitSignal(SignalName.ReducerCallFailed, error);
            return;
        }

        _signalAdapter.Dispatch(() => EmitSignal(SignalName.ReducerCallFailed, error));
    }

    private void RegisterLiveClient()
    {
        var normalizedConnectionId = NormalizeConnectionId(ConnectionId);

        lock (LiveClientsGate)
        {
            if (LiveClients.TryGetValue(normalizedConnectionId, out var existingClient) &&
                !ReferenceEquals(existingClient, this))
            {
                throw new InvalidOperationException(
                    $"A SpacetimeClient with ConnectionId '{normalizedConnectionId}' is already registered.");
            }

            LiveClients[normalizedConnectionId] = this;
        }

        _registeredConnectionId = normalizedConnectionId;
    }

    private void UnregisterLiveClient()
    {
        var normalizedConnectionId = _registeredConnectionId;
        _registeredConnectionId = null;
        if (normalizedConnectionId == null)
            return;

        lock (LiveClientsGate)
        {
            if (LiveClients.TryGetValue(normalizedConnectionId, out var existingClient) &&
                ReferenceEquals(existingClient, this))
            {
                LiveClients.Remove(normalizedConnectionId);
            }
        }
    }

    private bool OwnsPerformanceMonitors() =>
        _registeredConnectionId != null &&
        string.Equals(_registeredConnectionId, DefaultConnectionId, StringComparison.Ordinal);

    private static string NormalizeConnectionId(string? connectionId) =>
        string.IsNullOrWhiteSpace(connectionId) ? DefaultConnectionId : connectionId.Trim();
}

using System;
using System.Collections.Generic;
using Godot;
using GodotSpacetime.Connection;
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
///   <item>Read cache via GetRows() and cast rows to generated binding types — invoke reducers as needed</item>
/// </list>
/// </summary>
public partial class SpacetimeClient : Node
{
    private readonly SpacetimeConnectionService _connectionService = new();
    private ConnectionStatus _currentStatus = new(ConnectionState.Disconnected, "DISCONNECTED — not connected to SpacetimeDB");
    private GodotSignalAdapter? _signalAdapter;

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

    public ConnectionStatus CurrentStatus => _currentStatus;

    public override void _EnterTree()
    {
        _signalAdapter ??= new GodotSignalAdapter(this);
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
    /// Returns the rows currently cached for the specified table.
    /// Call after the <c>SubscriptionApplied</c> signal fires, then cast each row to the generated table type.
    /// </summary>
    public IEnumerable<object> GetRows(string tableName) =>
        _connectionService.GetRows(tableName);

    /// <summary>
    /// Invokes a SpacetimeDB reducer through the supported generated reducer path.
    /// Pass a generated <c>IReducerArgs</c> instance from the module's generated bindings
    /// (e.g. the generated <c>Reducer.Ping</c> type for a <c>ping</c> reducer).
    /// The invocation is routed through <c>ReducerInvoker</c> → <c>SpacetimeSdkReducerAdapter</c> →
    /// the runtime SDK call.
    /// Must be called after <c>ConnectionState.Connected</c> is reached.
    /// Fires <c>ConnectionStateChanged</c> with a validation error if called in the wrong state
    /// or with an invalid reducer argument object.
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
}

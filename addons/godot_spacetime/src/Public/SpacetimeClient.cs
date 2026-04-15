using System;
using System.Collections.Generic;
using Godot;
using GodotSpacetime.Connection;
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
///   <item>Apply subscriptions — receive SubscriptionAppliedEvent when cache is ready</item>
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

    [Signal]
    public delegate void SubscriptionAppliedEventHandler(SubscriptionAppliedEvent e);

    [Export]
    public SpacetimeSettings? Settings { get; set; }

    public ConnectionStatus CurrentStatus => _currentStatus;

    public override void _EnterTree()
    {
        _signalAdapter ??= new GodotSignalAdapter(this);
        _connectionService.OnStateChanged += HandleStateChanged;
        _connectionService.OnConnectionOpened += HandleConnectionOpened;
        _connectionService.OnSubscriptionApplied += HandleSubscriptionApplied;
    }

    public override void _ExitTree()
    {
        _connectionService.OnStateChanged -= HandleStateChanged;
        _connectionService.OnConnectionOpened -= HandleConnectionOpened;
        _connectionService.OnSubscriptionApplied -= HandleSubscriptionApplied;
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
    /// Returns the rows currently cached for the specified table.
    /// Call after the <c>SubscriptionApplied</c> signal fires, then cast each row to the generated table type.
    /// </summary>
    public IEnumerable<object> GetRows(string tableName) =>
        _connectionService.GetRows(tableName);

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

    private void HandleSubscriptionApplied(SubscriptionAppliedEvent appliedEvent)
    {
        if (_signalAdapter == null)
        {
            EmitSignal(SignalName.SubscriptionApplied, appliedEvent);
            return;
        }

        _signalAdapter.Dispatch(() => EmitSignal(SignalName.SubscriptionApplied, appliedEvent));
    }
}

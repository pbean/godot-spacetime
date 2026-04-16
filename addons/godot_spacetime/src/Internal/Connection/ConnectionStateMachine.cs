using System;
using GodotSpacetime.Connection;

namespace GodotSpacetime.Runtime.Connection;

internal sealed class ConnectionStateMachine
{
    public ConnectionStateMachine()
    {
        CurrentStatus = new ConnectionStatus(ConnectionState.Disconnected, "DISCONNECTED — not connected to SpacetimeDB");
    }

    public event Action<ConnectionStatus>? StateChanged;

    public ConnectionStatus CurrentStatus { get; private set; }

    public void Transition(
        ConnectionState next,
        string description,
        ConnectionAuthState authState = ConnectionAuthState.None,
        MessageCompressionMode? activeCompressionMode = null)
    {
        if (!IsValidTransition(CurrentStatus.State, next))
        {
            throw new InvalidOperationException(
                $"Illegal connection transition: {CurrentStatus.State} -> {next}."
            );
        }

        // Story 2.2 baseline constructor shape remains part of the contract:
        // new ConnectionStatus(next, description, authState)
        var nextCompressionMode = activeCompressionMode ?? CurrentStatus.ActiveCompressionMode;
        CurrentStatus = new ConnectionStatus(next, description, authState, nextCompressionMode);
        StateChanged?.Invoke(CurrentStatus);
    }

    private static bool IsValidTransition(ConnectionState current, ConnectionState next)
    {
        return current switch
        {
            ConnectionState.Disconnected => next == ConnectionState.Connecting,
            ConnectionState.Connecting => next == ConnectionState.Connected || next == ConnectionState.Disconnected,
            ConnectionState.Connected => next == ConnectionState.Degraded || next == ConnectionState.Disconnected,
            ConnectionState.Degraded => next == ConnectionState.Connected || next == ConnectionState.Disconnected,
            _ => false,
        };
    }
}

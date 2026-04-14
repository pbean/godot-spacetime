using Godot;

namespace GodotSpacetime.Connection;

/// <summary>
/// A point-in-time snapshot of the connection lifecycle, pairing a <see cref="ConnectionState"/>
/// with a human-readable description for logging and UI display.
/// </summary>
public partial class ConnectionStatus : RefCounted
{
    public ConnectionStatus()
    {
    }

    public ConnectionStatus(ConnectionState state, string description, ConnectionAuthState authState = ConnectionAuthState.None)
    {
        State = state;
        Description = description;
        AuthState = authState;
    }

    public ConnectionState State { get; set; }

    public string Description { get; set; } = string.Empty;

    public ConnectionAuthState AuthState { get; set; }
}

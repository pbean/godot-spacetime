namespace GodotSpacetime.Connection;

/// <summary>
/// The lifecycle state of a GodotSpacetime connection.
/// </summary>
public enum ConnectionState
{
    /// <summary>No active connection. Initial state before Connect() is called, or terminal state after a clean disconnect.</summary>
    Disconnected,

    /// <summary>A connection attempt is in progress.</summary>
    Connecting,

    /// <summary>A live session is established. Subscriptions may be applied in this state.</summary>
    Connected,

    /// <summary>The session is experiencing trouble but has not fully disconnected. Recovery is attempted automatically.</summary>
    Degraded,
}

namespace GodotSpacetime.Connection;

/// <summary>
/// Indicates why a live connection session ended.
/// Carried by <c>ConnectionClosedEvent</c> to let gameplay code distinguish
/// intentional disconnects from unexpected losses.
/// </summary>
public enum ConnectionCloseReason
{
    /// <summary>
    /// The session ended cleanly: either <c>SpacetimeClient.Disconnect()</c> was called explicitly,
    /// or the server closed the connection gracefully. No error occurred.
    /// </summary>
    Clean,

    /// <summary>
    /// The session was lost due to a network or protocol error after the connection was established.
    /// Inspect <c>ConnectionClosedEvent.ErrorMessage</c> for the failure detail.
    /// </summary>
    Error,
}

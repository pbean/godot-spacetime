using System;
using Godot;

namespace GodotSpacetime.Connection;

/// <summary>
/// Event payload raised when a live connection session ends.
/// Corresponds to the <c>connection.closed</c> SDK domain event; symmetric with <c>ConnectionOpenedEvent</c>.
/// Fires after <c>ConnectionStateChanged</c> transitions to <c>Disconnected</c>.
/// Does NOT fire for failed connect attempts (never reached <c>Connected</c>);
/// <c>ConnectionStateChanged</c> covers those via the <c>Disconnected</c> state.
/// </summary>
public partial class ConnectionClosedEvent : RefCounted
{
    /// <summary>
    /// Whether the session ended cleanly or due to an error.
    /// <c>Clean</c>: explicit <c>Disconnect()</c> or server-side graceful close.
    /// <c>Error</c>: session lost due to network or protocol error after being established.
    /// </summary>
    public ConnectionCloseReason CloseReason { get; set; }

    /// <summary>
    /// Human-readable error detail when <c>CloseReason</c> is <c>Error</c>.
    /// Empty string for <c>Clean</c> closes.
    /// </summary>
    public string ErrorMessage { get; set; } = string.Empty;

    /// <summary>UTC timestamp at which the SDK recorded the close event.</summary>
    public DateTimeOffset ClosedAt { get; set; }
}

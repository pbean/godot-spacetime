using System;
using Godot;
using GodotSpacetime;

namespace GodotSpacetime.Connection;

/// <summary>
/// Event payload raised when a connection session is successfully opened.
/// Corresponds to the <c>connection.opened</c> SDK domain event.
/// </summary>
public partial class ConnectionOpenedEvent : RefCounted
{
    public string Host { get; set; } = string.Empty;

    public string Database { get; set; } = string.Empty;

    /// <summary>Server-assigned identity string for the authenticated session. Empty for anonymous connections.</summary>
    public string Identity { get; set; } = string.Empty;

    /// <summary>
    /// Typed form of the same identity exposed by <see cref="Identity"/>.
    /// <c>default(Identity)</c> for anonymous connections or when no identity was captured.
    /// </summary>
    public Identity IdentityValue { get; set; } = default;

    public DateTimeOffset ConnectedAt { get; set; }
}

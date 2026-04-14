using System;
using Godot;

namespace GodotSpacetime.Connection;

/// <summary>
/// Event payload raised when a connection session is successfully opened.
/// Corresponds to the <c>connection.opened</c> SDK domain event.
/// </summary>
public partial class ConnectionOpenedEvent : RefCounted
{
    public string Host { get; set; } = string.Empty;

    public string Database { get; set; } = string.Empty;

    public DateTimeOffset ConnectedAt { get; set; }
}

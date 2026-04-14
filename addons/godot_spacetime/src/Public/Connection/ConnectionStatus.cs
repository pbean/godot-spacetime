namespace GodotSpacetime.Connection;

/// <summary>
/// A point-in-time snapshot of the connection lifecycle, pairing a <see cref="ConnectionState"/>
/// with a human-readable description for logging and UI display.
/// </summary>
public record ConnectionStatus(ConnectionState State, string Description);

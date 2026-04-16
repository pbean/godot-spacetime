namespace GodotSpacetime.Connection;

/// <summary>
/// Runtime-neutral compression preference for a SpacetimeDB connection.
/// </summary>
public enum MessageCompressionMode
{
    None,
    Gzip,
    Brotli,
}

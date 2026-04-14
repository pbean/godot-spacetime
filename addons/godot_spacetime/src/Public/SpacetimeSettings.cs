using Godot;
using GodotSpacetime.Auth;

namespace GodotSpacetime;

/// <summary>
/// Godot Resource holding configuration for a SpacetimeDB connection.
/// Create an instance in the Godot editor and assign it to <see cref="SpacetimeClient"/>.
/// </summary>
[GlobalClass]
public partial class SpacetimeSettings : Resource
{
    /// <summary>The SpacetimeDB server address (e.g., "localhost:3000").</summary>
    [Export]
    public string Host { get; set; } = string.Empty;

    /// <summary>The target database name on the server.</summary>
    [Export]
    public string Database { get; set; } = string.Empty;

    /// <summary>
    /// Optional token store for persisting session tokens between connections.
    /// If null (the default), tokens are not persisted when the process exits.
    /// Assign a <see cref="ITokenStore"/> implementation to enable opt-in session persistence.
    /// Built-in options: <c>MemoryTokenStore</c> (in-memory, non-persistent) or
    /// <c>ProjectSettingsTokenStore</c> (persists to Godot ProjectSettings).
    /// </summary>
    public ITokenStore? TokenStore { get; set; }
}

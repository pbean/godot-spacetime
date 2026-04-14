using Godot;

namespace GodotSpacetime;

/// <summary>
/// Godot Resource holding configuration for a SpacetimeDB connection.
/// Create an instance in the Godot editor and assign it to <see cref="SpacetimeClient"/>.
/// Additional settings (auth, logging) are added in later stories.
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
}

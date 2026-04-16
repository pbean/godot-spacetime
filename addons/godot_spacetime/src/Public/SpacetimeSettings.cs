using Godot;
using GodotSpacetime.Auth;
using GodotSpacetime.Connection;

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
    /// Optional wire-message compression preference.
    /// Defaults to <see cref="MessageCompressionMode.None"/> so existing projects
    /// keep their current behavior until compression is explicitly enabled.
    /// </summary>
    [Export]
    public MessageCompressionMode CompressionMode { get; set; } = MessageCompressionMode.None;

    /// <summary>
    /// Optional opt-in light-mode preference for server updates.
    /// Defaults to <c>false</c> so existing projects keep the full runtime behavior
    /// unless light mode is explicitly enabled before connecting.
    /// Changing this setting does not mutate an already-active session; the new
    /// value only takes effect the next time a connection is opened.
    /// </summary>
    [Export]
    public bool LightMode { get; set; } = false;

    /// <summary>
    /// Optional credentials token for authenticated sessions.
    /// When set, this value is passed to <c>WithToken()</c> on the SpacetimeDB connection builder,
    /// connecting as an identified user rather than an anonymous transport.
    /// If null or empty (the default), the connection opens anonymously and the server assigns a new identity.
    /// Story 2.3 adds automatic pre-connect restoration from <see cref="TokenStore"/>.
    /// Token values are never logged raw — use <c>TokenRedactor</c> for diagnostic output.
    /// </summary>
    public string? Credentials { get; set; }

    /// <summary>
    /// Optional token store for persisting session tokens between connections.
    /// If null (the default), tokens are not persisted when the process exits.
    /// Assign a <see cref="ITokenStore"/> implementation to enable opt-in session persistence.
    /// Built-in options: <c>MemoryTokenStore</c> (in-memory, non-persistent) or
    /// <c>ProjectSettingsTokenStore</c> (persists to Godot ProjectSettings).
    /// </summary>
    public ITokenStore? TokenStore { get; set; }
}

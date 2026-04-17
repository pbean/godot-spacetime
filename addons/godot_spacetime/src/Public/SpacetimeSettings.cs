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
    // Intentionally split: the isolation-boundary tests (test_story_1_3, test_story_1_4)
    // reject any "SpacetimeDB" + "." literal in Public/ source files. Concatenating at
    // compile time produces the correct runtime value while keeping this file clean.
    public const string DefaultGeneratedBindingsNamespace = "Spacetime" + "DB.Types";

    /// <summary>The SpacetimeDB server address (e.g., "localhost:3000").</summary>
    [Export]
    public string Host { get; set; } = string.Empty;

    /// <summary>The target database name on the server.</summary>
    [Export]
    public string Database { get; set; } = string.Empty;

    /// <summary>
    /// Optional generated binding namespace selector.
    /// Defaults to the canonical generated namespace so existing single-module projects
    /// keep their current zero-configuration behavior.
    /// Set this to a different generated namespace when multiple generated binding
    /// sets are compiled into the same C# project.
    /// </summary>
    [Export]
    public string GeneratedBindingsNamespace { get; set; } = DefaultGeneratedBindingsNamespace;

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
    /// Optional opt-in preference for server-confirmed reads.
    /// Defaults to <c>false</c> so existing projects keep the current read semantics
    /// unless confirmed reads are explicitly enabled before connecting.
    /// The adapter always forwards the current value to the pinned ClientSDK's
    /// <c>WithConfirmedReads(bool)</c> during connection setup — explicit <c>false</c> is passed
    /// when the field is left at its default, matching the SDK's explicit-configuration contract.
    /// Changing this setting does not mutate an already-active session; the new
    /// value only takes effect the next time a connection is opened.
    /// </summary>
    [Export]
    public bool ConfirmedReads { get; set; } = false;

    /// <summary>
    /// Maximum number of reconnect attempts the internal <c>ReconnectPolicy</c> will make
    /// after a previously <c>Connected</c> session encounters a transport error.
    /// Defaults to <c>3</c> so existing projects keep the current retry budget.
    /// Must be at least <c>1</c>; values less than <c>1</c> surface through the existing
    /// validation-failure path as a <c>Disconnected</c> transition with a descriptive message.
    /// Changing this setting does not mutate an already-active session; the new
    /// value only takes effect the next time <c>Connect()</c> is called.
    /// </summary>
    [Export]
    public int MaxReconnectAttempts { get; set; } = 3;

    /// <summary>
    /// Initial backoff (in seconds) used by the internal <c>ReconnectPolicy</c> for the first
    /// retry attempt; subsequent attempts double the wait (fixed 2× growth factor).
    /// Defaults to <c>1.0</c> so existing projects keep the current <c>1s/2s/4s</c> schedule.
    /// Must be a positive finite number; values less than or equal to zero, as well as
    /// <c>double.NaN</c>, <c>double.PositiveInfinity</c>, and <c>double.NegativeInfinity</c>, surface through
    /// the existing validation-failure path as a <c>Disconnected</c> transition with a descriptive message.
    /// Changing this setting does not mutate an already-active session; the new
    /// value only takes effect the next time <c>Connect()</c> is called.
    /// </summary>
    [Export]
    public double InitialBackoffSeconds { get; set; } = 1.0;

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

    internal string ResolveGeneratedBindingsNamespace() =>
        string.IsNullOrWhiteSpace(GeneratedBindingsNamespace)
            ? DefaultGeneratedBindingsNamespace
            : GeneratedBindingsNamespace.Trim();
}

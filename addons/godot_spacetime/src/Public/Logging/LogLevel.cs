namespace GodotSpacetime.Logging;

/// <summary>
/// Severity of an SDK log entry. The three values map one-for-one to the
/// <c>Godot.GD</c> methods that SDK runtime call sites historically used
/// (<c>GD.Print</c>, <c>GD.PushWarning</c>, <c>GD.PushError</c>), so the
/// default <see cref="GodotConsoleLogSink"/> is byte-lossless against the
/// pre-G6 behavior.
/// </summary>
public enum LogLevel
{
    /// <summary>Informational message routed to the Godot console output.</summary>
    Info,

    /// <summary>Warning routed to the Godot console's debugger warning stream.</summary>
    Warning,

    /// <summary>Error routed to the Godot console's debugger error stream.</summary>
    Error,
}

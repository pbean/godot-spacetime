namespace GodotSpacetime.Logging;

/// <summary>
/// Destination for SDK log entries emitted via <see cref="SpacetimeLog"/>.
/// Apps assign a custom implementation to <see cref="SpacetimeSettings.LogSink"/>
/// (or directly to <see cref="SpacetimeLog.Sink"/>) to route SDK output to a
/// custom destination — typical targets include Sentry, a file sink, or a
/// level-filtering middleware sink that forwards to <see cref="GodotConsoleLogSink"/>.
/// The default <see cref="GodotConsoleLogSink"/> writes to the Godot console
/// exactly as the pre-G6 <c>GD.Print</c>/<c>GD.PushWarning</c>/<c>GD.PushError</c>
/// calls did.
/// </summary>
public interface ILogSink
{
    /// <summary>
    /// Handle one SDK log entry. Implementations should never throw; a faulty
    /// sink must not take down the SDK runtime call site.
    /// </summary>
    /// <param name="level">Severity of the entry.</param>
    /// <param name="category">SDK subsystem that emitted the entry.</param>
    /// <param name="message">Human-readable log message.</param>
    /// <param name="exception">Optional exception associated with the entry.
    /// Passed through so error-tracking sinks (Sentry, Crashlytics) can capture
    /// the stack trace without the caller formatting it into <paramref name="message"/>.</param>
    void Write(LogLevel level, LogCategory category, string message, System.Exception? exception = null);
}

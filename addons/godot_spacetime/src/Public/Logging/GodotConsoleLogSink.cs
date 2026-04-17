using Godot;

namespace GodotSpacetime.Logging;

/// <summary>
/// Default <see cref="ILogSink"/> that forwards SDK entries to the Godot console:
/// <c>Info → GD.Print</c>, <c>Warning → GD.PushWarning</c>, <c>Error → GD.PushError</c>.
/// The category is prefixed as <c>[Category] message</c>; when an exception is
/// supplied, its full <c>ToString()</c> representation is appended so the
/// Godot debugger receives the stack trace.
/// </summary>
public sealed class GodotConsoleLogSink : ILogSink
{
    /// <summary>
    /// Process-wide default instance used by <see cref="SpacetimeLog"/> when no
    /// custom sink has been installed via <see cref="SpacetimeSettings.LogSink"/>.
    /// </summary>
    public static readonly GodotConsoleLogSink Instance = new();

    /// <inheritdoc />
    public void Write(LogLevel level, LogCategory category, string message, System.Exception? exception = null)
    {
        var formatted = $"[{category}] {message}";
        if (exception != null)
            formatted = $"{formatted}\n{exception}";

        switch (level)
        {
            case LogLevel.Info:
                GD.Print(formatted);
                break;
            case LogLevel.Warning:
                GD.PushWarning(formatted);
                break;
            case LogLevel.Error:
                GD.PushError(formatted);
                break;
            default:
                // Unknown / future LogLevel values route to GD.Print so the entry is never
                // silently dropped. Keeping the contract "every call reaches the console".
                GD.Print(formatted);
                break;
        }
    }
}

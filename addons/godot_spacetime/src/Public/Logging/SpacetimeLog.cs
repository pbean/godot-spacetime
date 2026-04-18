namespace GodotSpacetime.Logging;

/// <summary>
/// Static facade the SDK writes log entries through. Apps configure the
/// destination by assigning <see cref="Sink"/> (directly, or indirectly via
/// <see cref="SpacetimeSettings.LogSink"/> which <see cref="SpacetimeClient"/>
/// installs on entering the tree).
///
/// When multiple <see cref="SpacetimeClient"/> nodes with different
/// <see cref="SpacetimeSettings.LogSink"/> values enter the tree, the last one
/// wins — apps that need per-client routing should compose their own
/// dispatching <see cref="ILogSink"/> that inspects each message and forwards.
///
/// No-teardown contract: <see cref="SpacetimeClient._ExitTree"/> does not
/// restore the previously-active sink. A sink installed by a client that
/// later exits the tree remains the process-wide default until another client
/// replaces it or the app clears <see cref="Sink"/> explicitly.
/// </summary>
public static class SpacetimeLog
{
    private static volatile ILogSink _sink = GodotConsoleLogSink.Instance;

    /// <summary>
    /// Active log destination. Defaults to <see cref="GodotConsoleLogSink.Instance"/>
    /// so unconfigured projects keep the pre-G6 console behavior exactly.
    /// Assigning <c>null</c> reverts to <see cref="GodotConsoleLogSink.Instance"/>;
    /// the facade is never left without a sink.
    /// </summary>
    public static ILogSink Sink
    {
        get => _sink;
        set => _sink = value ?? GodotConsoleLogSink.Instance;
    }

    /// <summary>Emit an informational entry through the active <see cref="Sink"/>.</summary>
    public static void Info(LogCategory category, string message, System.Exception? exception = null) =>
        SafeWrite(LogLevel.Info, category, message, exception);

    /// <summary>Emit a warning entry through the active <see cref="Sink"/>.</summary>
    public static void Warning(LogCategory category, string message, System.Exception? exception = null) =>
        SafeWrite(LogLevel.Warning, category, message, exception);

    /// <summary>Emit an error entry through the active <see cref="Sink"/>.</summary>
    public static void Error(LogCategory category, string message, System.Exception? exception = null) =>
        SafeWrite(LogLevel.Error, category, message, exception);

    // Honor the ILogSink.Write XML contract ("a faulty sink must not take down the SDK
    // runtime call site") by catching any exception the custom sink raises and falling
    // back to the default GodotConsoleLogSink. The fallback surfaces the sink failure
    // too, so silent loss of diagnostics is not possible.
    private static void SafeWrite(LogLevel level, LogCategory category, string message, System.Exception? exception)
    {
        var sink = _sink;
        try
        {
            sink.Write(level, category, message, exception);
        }
        catch (System.Exception sinkException)
        {
            if (!ReferenceEquals(sink, GodotConsoleLogSink.Instance))
            {
                GodotConsoleLogSink.Instance.Write(level, category, message, exception);
                GodotConsoleLogSink.Instance.Write(
                    LogLevel.Error,
                    category,
                    $"SpacetimeLog: custom ILogSink threw during Write; fell back to GodotConsoleLogSink. Sink={sink.GetType().FullName}",
                    sinkException);
            }
        }
    }
}

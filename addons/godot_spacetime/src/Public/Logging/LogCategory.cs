namespace GodotSpacetime.Logging;

/// <summary>
/// SDK log subsystem categories. Used to tag and filter log output from the GodotSpacetime SDK.
/// </summary>
public enum LogCategory
{
    /// <summary>Connection lifecycle events (state transitions, open, close).</summary>
    Connection,

    /// <summary>Token store operations and session identity events.</summary>
    Auth,

    /// <summary>Subscription apply, remove, and error events.</summary>
    Subscription,

    /// <summary>Reducer call dispatch and result handling.</summary>
    Reducer,

    /// <summary>Generated binding load and schema validation events.</summary>
    Codegen,
}

namespace GodotSpacetime.Reducers;

/// <summary>
/// Categorizes the failure mode of a reducer invocation.
/// Use this to branch gameplay error handling after a <c>ReducerCallFailed</c> event.
/// </summary>
public enum ReducerFailureCategory
{
    /// <summary>
    /// The server rejected the reducer due to a logic error or constraint violation.
    /// Check server logs or module logic. Retrying with the same arguments is unlikely to succeed.
    /// </summary>
    Failed,

    /// <summary>
    /// The server ran out of energy and could not execute the reducer.
    /// Back off and retry after a delay, or inform the player that the action is temporarily unavailable.
    /// </summary>
    OutOfEnergy,

    /// <summary>
    /// The status could not be determined.
    /// Handle defensively; do not retry automatically without additional context.
    /// </summary>
    Unknown,
}

namespace GodotSpacetime.Queries;

/// <summary>
/// Categorizes recoverable one-off query failure modes for gameplay error handling.
/// </summary>
public enum OneOffQueryFailureCategory
{
    /// <summary>
    /// The SQL clause was malformed or the server rejected the query shape.
    /// Fix the clause before retrying.
    /// </summary>
    InvalidQuery,

    /// <summary>
    /// The SDK-level timeout elapsed before the server returned a query result.
    /// Retry with a longer timeout only after confirming the query is expected to be slow.
    /// </summary>
    TimedOut,

    /// <summary>
    /// The server failed the query for a recoverable runtime reason that is not a client programming fault.
    /// </summary>
    Failed,

    /// <summary>
    /// The failure could not be classified safely from the upstream runtime error.
    /// Handle defensively and capture diagnostics before retrying.
    /// </summary>
    Unknown,
}

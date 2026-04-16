using System;

namespace GodotSpacetime.Queries;

/// <summary>
/// Thrown when a one-off query reaches the server but fails for a recoverable runtime reason.
/// Programming faults such as disconnected state, blank SQL, or unsupported row types remain explicit exceptions.
/// </summary>
public sealed class OneOffQueryError : Exception
{
    public Type RequestedRowType { get; }

    public string TargetTable { get; }

    public string SqlClause { get; }

    public OneOffQueryFailureCategory FailureCategory { get; }

    public string ErrorMessage { get; }

    public string RecoveryGuidance { get; }

    public DateTimeOffset RequestedAt { get; }

    public DateTimeOffset FailedAt { get; }

    internal OneOffQueryError(
        Type requestedRowType,
        string targetTable,
        string sqlClause,
        DateTimeOffset requestedAt,
        string errorMessage,
        OneOffQueryFailureCategory failureCategory,
        string recoveryGuidance,
        Exception? innerException = null)
        : base(errorMessage, innerException)
    {
        RequestedRowType = requestedRowType;
        TargetTable = targetTable;
        SqlClause = sqlClause;
        RequestedAt = requestedAt;
        ErrorMessage = errorMessage;
        FailureCategory = failureCategory;
        RecoveryGuidance = recoveryGuidance;
        FailedAt = DateTimeOffset.UtcNow;
    }
}

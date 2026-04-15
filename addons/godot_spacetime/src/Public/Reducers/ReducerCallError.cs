using System;
using Godot;

namespace GodotSpacetime.Reducers;

/// <summary>
/// Raised when a reducer invocation is rejected or fails on the server.
/// <c>FailureCategory</c> and <c>RecoveryGuidance</c> guide whether gameplay code should retry
/// or inform the user, while <c>InvocationId</c> distinguishes the specific invocation instance.
/// Instances are created by the SDK only; the internal constructor prevents external construction.
/// </summary>
public partial class ReducerCallError : RefCounted
{
    /// <summary>Identifies which reducer failed.</summary>
    public string ReducerName { get; }

    /// <summary>Opaque SDK-generated identifier for the specific reducer invocation instance.</summary>
    public string InvocationId { get; }

    /// <summary>Human-readable failure description from the server.</summary>
    public string ErrorMessage { get; }

    /// <summary>Failure category for branching logic in gameplay error handling.</summary>
    public ReducerFailureCategory FailureCategory { get; }

    /// <summary>User-safe retry or feedback guidance derived from the failure category.</summary>
    public string RecoveryGuidance { get; }

    /// <summary>UTC timestamp recorded when the reducer invocation was accepted by the SDK.</summary>
    public DateTimeOffset CalledAt { get; }

    /// <summary>UTC timestamp recorded when the failure was received by the SDK.</summary>
    public DateTimeOffset FailedAt { get; }

    internal ReducerCallError(
        string reducerName,
        string invocationId,
        DateTimeOffset calledAt,
        string errorMessage,
        ReducerFailureCategory failureCategory,
        string recoveryGuidance)
    {
        ReducerName = reducerName;
        InvocationId = invocationId;
        CalledAt = calledAt;
        ErrorMessage = errorMessage;
        FailureCategory = failureCategory;
        RecoveryGuidance = recoveryGuidance;
        FailedAt = DateTimeOffset.UtcNow;
    }
}

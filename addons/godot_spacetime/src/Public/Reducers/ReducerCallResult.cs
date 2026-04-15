using System;
using Godot;

namespace GodotSpacetime.Reducers;

/// <summary>
/// Raised when the server acknowledges a reducer invocation as committed.
/// <c>ReducerName</c> identifies which reducer completed successfully and <c>InvocationId</c>
/// distinguishes the specific invocation instance the outcome belongs to.
/// Instances are created by the SDK only; the internal constructor prevents external construction.
/// </summary>
public partial class ReducerCallResult : RefCounted
{
    /// <summary>Identifies which reducer produced this result.</summary>
    public string ReducerName { get; }

    /// <summary>Opaque SDK-generated identifier for the specific reducer invocation instance.</summary>
    public string InvocationId { get; }

    /// <summary>UTC timestamp recorded when the reducer invocation was accepted by the SDK.</summary>
    public DateTimeOffset CalledAt { get; }

    /// <summary>UTC timestamp recorded when the success result was surfaced by the SDK.</summary>
    public DateTimeOffset CompletedAt { get; }

    internal ReducerCallResult(string reducerName, string invocationId, DateTimeOffset calledAt)
    {
        ReducerName = reducerName;
        InvocationId = invocationId;
        CalledAt = calledAt;
        CompletedAt = DateTimeOffset.UtcNow;
    }
}

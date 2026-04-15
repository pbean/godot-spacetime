using System;
using System.Collections.Generic;
using System.Linq.Expressions;
using System.Reflection;
using System.Runtime.CompilerServices;
using GodotSpacetime.Reducers;
using SpacetimeDB;

namespace GodotSpacetime.Runtime.Platform.DotNet;

internal interface IReducerEventSink
{
    void OnReducerCallSucceeded(string reducerName, string invocationId, DateTimeOffset calledAt);
    void OnReducerCallFailed(
        string reducerName,
        string invocationId,
        DateTimeOffset calledAt,
        string errorMessage,
        ReducerFailureCategory failureCategory,
        string recoveryGuidance);
}

/// <summary>
/// Adapter for the SpacetimeDB .NET ClientSDK reducer invocation layer.
///
/// This class is the ONLY location in the codebase where <c>SpacetimeDB.ClientSDK</c>
/// reducer types may be referenced directly. All higher-level internal services
/// and all public SDK surfaces depend on the <c>GodotSpacetime.*</c> contracts rather
/// than on <c>SpacetimeDB.*</c> types.
///
/// See <c>docs/runtime-boundaries.md</c> — "Internal/Platform/DotNet/ — The Runtime
/// Isolation Zone" for the architectural justification.
/// </summary>
internal sealed class SpacetimeSdkReducerAdapter
{
    private IDbConnection? _dbConnection;
    private readonly ConditionalWeakTable<object, RegistrationMarker> _registeredReducers = new();
    private readonly object _pendingInvocationsGate = new();
    private readonly Dictionary<string, List<PendingReducerInvocation>> _pendingInvocations = new(StringComparer.Ordinal);

    private sealed class RegistrationMarker;

    private sealed class PendingReducerInvocation
    {
        internal PendingReducerInvocation(string invocationId, DateTimeOffset calledAt)
        {
            InvocationId = invocationId;
            CalledAt = calledAt;
        }

        internal string InvocationId { get; }

        internal DateTimeOffset CalledAt { get; }
    }

    internal void SetConnection(IDbConnection? connection)
    {
        _dbConnection = connection;
    }

    internal void Invoke(object reducerArgs)
    {
        if (_dbConnection == null)
            throw new InvalidOperationException(
                "SpacetimeSdkReducerAdapter.Invoke requires an active DbConnection. " +
                "This is a programming fault — ensure ConnectionState.Connected is reached before invoking reducers.");

        if (reducerArgs is not IReducerArgs reducer)
            throw new ArgumentException(
                $"reducerArgs must implement SpacetimeDB.IReducerArgs, got {reducerArgs?.GetType().FullName ?? "null"}.",
                nameof(reducerArgs));

        var pendingInvocation = TrackPendingInvocation(reducer.ReducerName);

        // InternalCallReducer<T>(T args) must see the concrete generated reducer type, not IReducerArgs.
        dynamic typedReducerArgs = reducerArgs;
        try
        {
            _dbConnection.InternalCallReducer(typedReducerArgs);
        }
        catch
        {
            RemovePendingInvocation(reducer.ReducerName, pendingInvocation.InvocationId);
            throw;
        }
    }

    /// <summary>
    /// Wires per-reducer result callbacks into the SDK's <c>RemoteReducers</c> object.
    /// Call immediately after <c>OnConnected</c> fires with the live connection.
    /// Idempotent — the <c>ConditionalWeakTable</c> guard prevents double-registration
    /// when the same <c>Reducers</c> instance survives a Degraded→Connected recovery.
    /// No explicit unregistration is needed; registered delegates are collected with the
    /// closed connection's <c>Reducers</c> object once GC roots are cleared.
    /// </summary>
    internal void RegisterCallbacks(IReducerEventSink sink)
    {
        ArgumentNullException.ThrowIfNull(sink);

        if (_dbConnection == null)
            return;

        // SpacetimeDB 2.1.0 exposes Reducers as a public field, not a property.
        var reducers = _dbConnection.GetType()
            .GetField("Reducers", BindingFlags.Public | BindingFlags.Instance)
            ?.GetValue(_dbConnection);

        if (reducers == null)
            return;

        // Idempotency guard: prevents double-registration on Degraded→Connected recovery.
        if (!_registeredReducers.TryGetValue(reducers, out _))
            _registeredReducers.Add(reducers, new RegistrationMarker());
        else
            return;

        foreach (var evt in reducers.GetType().GetEvents(BindingFlags.Public | BindingFlags.Instance))
            TryWireReducerEvent(this, reducers, evt, sink);
    }

    private static void TryWireReducerEvent(
        SpacetimeSdkReducerAdapter adapter,
        object reducers,
        EventInfo evt,
        IReducerEventSink sink)
    {
        var invoke = evt.EventHandlerType?.GetMethod("Invoke");
        if (invoke == null) return;

        var parameters = invoke.GetParameters();

        // Only wire events with exactly 1 parameter — this naturally excludes
        // InternalOnUnhandledReducerError (2 params: ReducerEventContext, Exception)
        // and provides defense-in-depth against future SDK version changes.
        if (parameters.Length != 1) return;

        var ctxParam = Expression.Parameter(parameters[0].ParameterType, "ctx");
        var adapterConst = Expression.Constant(adapter);
        var sinkConst = Expression.Constant(sink);
        var ctxAsObject = Expression.Convert(ctxParam, typeof(object));

        var extractMethod = typeof(SpacetimeSdkReducerAdapter).GetMethod(
            nameof(ExtractAndDispatch),
            BindingFlags.NonPublic | BindingFlags.Instance)!;

        var body = Expression.Call(adapterConst, extractMethod, sinkConst, ctxAsObject);
        var lambda = Expression.Lambda(evt.EventHandlerType!, body, ctxParam).Compile();
        evt.AddEventHandler(reducers, lambda);
    }

    private void ExtractAndDispatch(IReducerEventSink sink, object ctx)
    {
        // ReducerEventContext.Event is a public readonly FIELD (not property).
        // Confirmed from demo/generated/smoke_test/SpacetimeDBClient.g.cs:121.
        var reducerEvent = ctx.GetType().GetField("Event")?.GetValue(ctx);
        if (reducerEvent == null)
        {
            var fallbackInvocation = CreateFallbackInvocation();
            sink.OnReducerCallFailed(
                "unknown",
                fallbackInvocation.InvocationId,
                fallbackInvocation.CalledAt,
                "Reducer event context unavailable",
                ReducerFailureCategory.Unknown,
                GetRecoveryGuidance(ReducerFailureCategory.Unknown));
            return;
        }

        // ReducerEvent<R>.Reducer is a PROPERTY holding the reducer args.
        var reducerArgsObj = reducerEvent.GetType().GetProperty("Reducer")?.GetValue(reducerEvent);
        var reducerName = (reducerArgsObj as IReducerArgs)?.ReducerName ?? "unknown";
        var pendingInvocation = TakePendingInvocation(reducerName);

        // Extract status — SpacetimeDB.Status is available via using SpacetimeDB; above.
        var status = reducerEvent.GetType().GetProperty("Status")?.GetValue(reducerEvent) as Status;
        if (status == null)
        {
            sink.OnReducerCallFailed(
                reducerName,
                pendingInvocation.InvocationId,
                pendingInvocation.CalledAt,
                "Status unavailable",
                ReducerFailureCategory.Unknown,
                GetRecoveryGuidance(ReducerFailureCategory.Unknown));
            return;
        }

        switch (status)
        {
            case Status.Committed:
                sink.OnReducerCallSucceeded(reducerName, pendingInvocation.InvocationId, pendingInvocation.CalledAt);
                break;
            case Status.Failed failed:
                sink.OnReducerCallFailed(
                    reducerName,
                    pendingInvocation.InvocationId,
                    pendingInvocation.CalledAt,
                    failed.Failed_ ?? "Reducer failed",
                    ReducerFailureCategory.Failed,
                    GetRecoveryGuidance(ReducerFailureCategory.Failed));
                break;
            case Status.OutOfEnergy:
                sink.OnReducerCallFailed(
                    reducerName,
                    pendingInvocation.InvocationId,
                    pendingInvocation.CalledAt,
                    "Out of energy — reducer not executed",
                    ReducerFailureCategory.OutOfEnergy,
                    GetRecoveryGuidance(ReducerFailureCategory.OutOfEnergy));
                break;
            default:
                sink.OnReducerCallFailed(
                    reducerName,
                    pendingInvocation.InvocationId,
                    pendingInvocation.CalledAt,
                    $"Unexpected reducer status: {status.GetType().Name}",
                    ReducerFailureCategory.Unknown,
                    GetRecoveryGuidance(ReducerFailureCategory.Unknown));
                break;
        }
    }

    internal void ClearConnection()
    {
        _dbConnection = null;
        lock (_pendingInvocationsGate)
            _pendingInvocations.Clear();
    }

    private PendingReducerInvocation TrackPendingInvocation(string reducerName)
    {
        var pendingInvocation = new PendingReducerInvocation(Guid.NewGuid().ToString("N"), DateTimeOffset.UtcNow);

        lock (_pendingInvocationsGate)
        {
            if (!_pendingInvocations.TryGetValue(reducerName, out var invocations))
            {
                invocations = new List<PendingReducerInvocation>();
                _pendingInvocations[reducerName] = invocations;
            }

            invocations.Add(pendingInvocation);
        }

        return pendingInvocation;
    }

    private PendingReducerInvocation TakePendingInvocation(string reducerName)
    {
        lock (_pendingInvocationsGate)
        {
            if (!_pendingInvocations.TryGetValue(reducerName, out var invocations) || invocations.Count == 0)
                return CreateFallbackInvocation();

            var pendingInvocation = invocations[0];
            invocations.RemoveAt(0);

            if (invocations.Count == 0)
                _pendingInvocations.Remove(reducerName);

            return pendingInvocation;
        }
    }

    private void RemovePendingInvocation(string reducerName, string invocationId)
    {
        lock (_pendingInvocationsGate)
        {
            if (!_pendingInvocations.TryGetValue(reducerName, out var invocations))
                return;

            var pendingIndex = invocations.FindIndex(pending => pending.InvocationId == invocationId);
            if (pendingIndex < 0)
                return;

            invocations.RemoveAt(pendingIndex);
            if (invocations.Count == 0)
                _pendingInvocations.Remove(reducerName);
        }
    }

    private static PendingReducerInvocation CreateFallbackInvocation() =>
        new($"untracked-{Guid.NewGuid():N}", DateTimeOffset.UtcNow);

    private static string GetRecoveryGuidance(ReducerFailureCategory failureCategory) =>
        failureCategory switch
        {
            ReducerFailureCategory.Failed =>
                "Check the reducer inputs or server-side rules before retrying or showing a player-facing error.",
            ReducerFailureCategory.OutOfEnergy =>
                "Back off and retry later, or tell the player the action is temporarily unavailable.",
            _ =>
                "Do not retry automatically. Surface a safe generic error and capture diagnostics for follow-up.",
        };
}

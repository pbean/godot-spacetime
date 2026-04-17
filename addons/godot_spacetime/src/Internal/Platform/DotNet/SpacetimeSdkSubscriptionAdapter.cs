using System;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;
using GodotSpacetime.Logging;
using GodotSpacetime.Subscriptions;
using SpacetimeDB;

namespace GodotSpacetime.Runtime.Platform.DotNet;

internal interface ISubscriptionEventSink
{
    void OnSubscriptionApplied(SubscriptionHandle handle);
    void OnSubscriptionError(SubscriptionHandle handle, Exception error);
}

/// <summary>
/// Adapter for the SpacetimeDB .NET ClientSDK subscription layer.
///
/// This class is the ONLY location in the codebase where SpacetimeDB.ClientSDK
/// subscription types may be referenced directly. All higher-level internal services
/// and all public SDK surfaces depend on the GodotSpacetime.* contracts rather
/// than on SpacetimeDB.* types.
///
/// See docs/runtime-boundaries.md — "Internal/Platform/DotNet/ — The Runtime
/// Isolation Zone" for the architectural justification.
/// </summary>
internal sealed class SpacetimeSdkSubscriptionAdapter
{
    private readonly SpacetimeSdkTelemetrySerializer _telemetrySerializer = new();

    /// <summary>
    /// Applies a subscription to the given connection for the specified SQL queries.
    /// Wires the SDK subscription applied and error callbacks to <paramref name="sink"/>.
    /// Returns the SDK subscription object (if the SDK returns one), or null.
    /// The caller should store this object and pass it to <see cref="TryUnsubscribe"/> to close the subscription.
    /// </summary>
    internal object? Subscribe(
        IDbConnection connection,
        string[] querySqls,
        ISubscriptionEventSink sink,
        SubscriptionHandle handle)
    {
        ArgumentNullException.ThrowIfNull(connection);
        ArgumentNullException.ThrowIfNull(querySqls);
        ArgumentNullException.ThrowIfNull(sink);
        ArgumentNullException.ThrowIfNull(handle);

        var builderMethod = connection.GetType()
            .GetMethod("SubscriptionBuilder", BindingFlags.Public | BindingFlags.Instance)
            ?? throw new InvalidOperationException(
                "Generated DbConnection must expose a public SubscriptionBuilder() method. " +
                "Ensure bindings are generated and compiled before calling Subscribe().");

        var builder = builderMethod.Invoke(connection, null)
            ?? throw new InvalidOperationException("SubscriptionBuilder() returned null.");

        builder = InvokeWithDelegate(builder, "OnApplied", CreateAppliedCallback(builder, handle, sink));
        builder = InvokeWithDelegate(builder, "OnError", CreateErrorCallback(builder, handle, sink));

        var subscribeMethod = builder.GetType()
            .GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .FirstOrDefault(m =>
                m.Name == "Subscribe" &&
                m.GetParameters().Length == 1 &&
                m.GetParameters()[0].ParameterType == typeof(string[]))
            ?? throw new InvalidOperationException(
                "Generated SubscriptionBuilder must expose a Subscribe(string[]) method.");

        // Capture the return value — the SDK may return a lifecycle object that supports Unsubscribe/Close.
        // If the SDK's Subscribe returns void, Invoke() returns null — TryUnsubscribe handles null gracefully.
        return subscribeMethod.Invoke(builder, new object[] { querySqls });
    }

    /// <summary>
    /// Attempts to close a previously-returned SDK subscription object by invoking its
    /// <c>Unsubscribe()</c> or <c>Close()</c> method via reflection.
    /// </summary>
    /// <param name="sdkSubscription">
    /// The object returned by <see cref="Subscribe"/>. May be null if the SDK does not return
    /// a lifecycle object, in which case this method returns <c>false</c> (graceful degradation).
    /// </param>
    /// <returns>
    /// <c>true</c> if an <c>Unsubscribe</c> or <c>Close</c> method was found and invoked;
    /// <c>false</c> otherwise (null input, no matching method, or the invocation fails).
    /// </returns>
    internal bool TryUnsubscribe(object? sdkSubscription)
    {
        if (sdkSubscription == null)
            return false;

        var type = sdkSubscription.GetType();

        // Try Unsubscribe() first, then Close()
        var method = type.GetMethod("Unsubscribe", BindingFlags.Public | BindingFlags.Instance, null, Type.EmptyTypes, null)
            ?? type.GetMethod("Close", BindingFlags.Public | BindingFlags.Instance, null, Type.EmptyTypes, null);

        if (method == null)
            return false;

        try
        {
            method.Invoke(sdkSubscription, null);
            return true;
        }
        catch (Exception)
        {
            // SDK close is best-effort so the caller can still mark the handle terminal
            // and clean up local bookkeeping even when the reflected method fails.
            return false;
        }
    }

    /// <summary>
    /// Attempts to wire a one-shot completion callback to the SDK's
    /// <c>UnsubscribeThen(Action&lt;T&gt;)</c> method via reflection. The returned
    /// <see cref="Action"/> is invoked once the SDK surfaces the ended event.
    /// </summary>
    /// <param name="sdkSubscription">
    /// The object returned by <see cref="Subscribe"/>. May be null if the SDK does not
    /// return a lifecycle object, in which case this method returns <c>false</c>.
    /// </param>
    /// <param name="onEnded">
    /// Callback fired once the SDK confirms the subscription has ended. Must not be null.
    /// </param>
    /// <returns>
    /// <c>true</c> if the SDK's <c>UnsubscribeThen(Action&lt;T&gt;)</c> method was found
    /// and invoked successfully; <c>false</c> otherwise (null input, missing method, or
    /// the invocation throws). Callers that receive <c>false</c> should dispatch
    /// <paramref name="onEnded"/> inline as a graceful fall-back.
    /// </returns>
    internal bool TryUnsubscribeThen(object? sdkSubscription, Action onEnded)
    {
        if (sdkSubscription == null)
            return false;

        ArgumentNullException.ThrowIfNull(onEnded);

        var type = sdkSubscription.GetType();

        var method = type.GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .FirstOrDefault(m =>
                m.Name == "UnsubscribeThen"
                && m.GetParameters().Length == 1
                && m.GetParameters()[0].ParameterType.IsGenericType
                && m.GetParameters()[0].ParameterType.GetGenericTypeDefinition() == typeof(Action<>));

        if (method == null)
        {
            SpacetimeLog.Warning(
                LogCategory.Subscription,
                $"TryUnsubscribeThen: {type.FullName} does not expose an UnsubscribeThen(Action<T>) method; " +
                "callers fall back to the parameterless Unsubscribe path and inline completion dispatch.");
            return false;
        }

        var delegateType = method.GetParameters()[0].ParameterType;
        var ctxType = delegateType.GetGenericArguments()[0];
        var ctxParam = Expression.Parameter(ctxType, "ctx");
        var invokeOnEnded = Expression.Invoke(Expression.Constant(onEnded));
        var sdkDelegate = Expression.Lambda(delegateType, invokeOnEnded, ctxParam).Compile();

        try
        {
            method.Invoke(sdkSubscription, new object[] { sdkDelegate });
            return true;
        }
        catch (Exception ex)
        {
            SpacetimeLog.Warning(
                LogCategory.Subscription,
                $"TryUnsubscribeThen: SDK UnsubscribeThen invocation failed on {type.FullName}; " +
                "callers fall back to inline completion dispatch.",
                ex);
            return false;
        }
    }

    internal long MeasureSubscribePayloadBytes(string[] querySqls) =>
        _telemetrySerializer.MeasureSubscribePayloadBytes(querySqls);

    internal long MeasureUnsubscribePayloadBytes() =>
        _telemetrySerializer.MeasureUnsubscribePayloadBytes();

    private static object InvokeWithDelegate(object builder, string methodName, Delegate callback)
    {
        var method = builder.GetType()
            .GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .FirstOrDefault(m => m.Name == methodName && m.GetParameters().Length == 1)
            ?? throw new InvalidOperationException(
                $"Generated SubscriptionBuilder must expose {methodName}(callback) method.");

        return method.Invoke(builder, new object[] { callback })
            ?? throw new InvalidOperationException(
                $"SubscriptionBuilder.{methodName}() returned null.");
    }

    private static Delegate CreateAppliedCallback(
        object builder,
        SubscriptionHandle handle,
        ISubscriptionEventSink sink)
    {
        var onAppliedMethod = builder.GetType()
            .GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .FirstOrDefault(m => m.Name == "OnApplied" && m.GetParameters().Length == 1)
            ?? throw new InvalidOperationException(
                "Generated SubscriptionBuilder must expose OnApplied(callback) method.");

        var delegateType = onAppliedMethod.GetParameters()[0].ParameterType;
        var genericArgs = delegateType.GetGenericArguments();

        if (genericArgs.Length != 1)
            throw new InvalidOperationException(
                "OnApplied callback must be Action<T> with one context type parameter.");

        var contextParam = Expression.Parameter(genericArgs[0], "ctx");
        var sinkConst = Expression.Constant(sink);
        var handleConst = Expression.Constant(handle);
        var appliedMethod = typeof(ISubscriptionEventSink)
            .GetMethod(nameof(ISubscriptionEventSink.OnSubscriptionApplied))!;
        var body = Expression.Call(sinkConst, appliedMethod, handleConst);

        return Expression.Lambda(delegateType, body, contextParam).Compile();
    }

    private static Delegate CreateErrorCallback(
        object builder,
        SubscriptionHandle handle,
        ISubscriptionEventSink sink)
    {
        var onErrorMethod = builder.GetType()
            .GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .FirstOrDefault(m => m.Name == "OnError" && m.GetParameters().Length == 1)
            ?? throw new InvalidOperationException(
                "Generated SubscriptionBuilder must expose OnError(callback) method.");

        var delegateType = onErrorMethod.GetParameters()[0].ParameterType;
        var genericArgs = delegateType.GetGenericArguments();

        if (genericArgs.Length != 2)
            throw new InvalidOperationException(
                "OnError callback must be Action<TContext, Exception> with two type parameters.");

        var contextParam = Expression.Parameter(genericArgs[0], "ctx");
        var exceptionParam = Expression.Parameter(genericArgs[1], "ex");
        var sinkConst = Expression.Constant(sink);
        var handleConst = Expression.Constant(handle);
        var errorMethod = typeof(ISubscriptionEventSink)
            .GetMethod(nameof(ISubscriptionEventSink.OnSubscriptionError))!;
        var body = Expression.Call(sinkConst, errorMethod, handleConst, exceptionParam);

        return Expression.Lambda(delegateType, body, contextParam, exceptionParam).Compile();
    }
}

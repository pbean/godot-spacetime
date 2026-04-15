using System;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;
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
    /// <summary>
    /// Applies a subscription to the given connection for the specified SQL queries.
    /// Wires the SDK subscription applied and error callbacks to <paramref name="sink"/>.
    /// </summary>
    internal void Subscribe(
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

        subscribeMethod.Invoke(builder, new object[] { querySqls });
    }

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

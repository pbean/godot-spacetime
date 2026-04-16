using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;
using GodotSpacetime.Connection;
using SpacetimeDB;

namespace GodotSpacetime.Runtime.Platform.DotNet;

internal interface IConnectionEventSink
{
    void OnConnected(string identity, string token);

    void OnConnectError(Exception error);

    void OnDisconnected(Exception? error);
}

/// <summary>
/// Adapter for the SpacetimeDB .NET ClientSDK connection layer.
///
/// This class is the ONLY location in the codebase where <c>SpacetimeDB.ClientSDK</c>
/// types may be referenced directly. All higher-level internal services and all public
/// SDK surfaces depend on the <c>GodotSpacetime.*</c> contracts rather than on
/// <c>SpacetimeDB.*</c> types.
///
/// See <c>docs/runtime-boundaries.md</c> — "Internal/Platform/DotNet/ — The Runtime
/// Isolation Zone" for the architectural justification.
/// </summary>
internal sealed class SpacetimeSdkConnectionAdapter
{
    private IDbConnection? _dbConnection;

    /// <summary>
    /// Provides access to the active <c>IDbConnection</c> for sibling adapters in the
    /// <c>Internal/Platform/DotNet/</c> isolation zone (e.g., <c>SpacetimeSdkSubscriptionAdapter</c>).
    /// Returns <c>null</c> when not connected.
    /// </summary>
    internal IDbConnection? Connection => _dbConnection;

    /// <summary>
    /// Gets the generated <c>RemoteTables</c> object (the <c>Db</c> property of the active
    /// <c>IDbConnection</c>) for use by the <c>CacheViewAdapter</c>.
    /// Returns <c>null</c> when not connected or when the generated <c>DbConnection</c> type
    /// does not expose a <c>Db</c> property.
    /// </summary>
    internal object? GetDb() =>
        _dbConnection?.GetType()
            .GetProperty("Db", BindingFlags.Public | BindingFlags.Instance)
            ?.GetValue(_dbConnection);

    public void Open(SpacetimeSettings settings, IConnectionEventSink sink)
    {
        ArgumentNullException.ThrowIfNull(settings);
        ArgumentNullException.ThrowIfNull(sink);

        Close();

        // The generated bindings expose the concrete DbConnection type and its DbConnection.Builder() entrypoint.
        // Builder() is inherited from DbConnectionBase<>, so FlattenHierarchy must be set on the reflection
        // lookup — without it GetMethod ignores static members declared on the base class.
        var dbConnectionType = ResolveGeneratedDbConnectionType();
        var builderMethod = dbConnectionType.GetMethod(
                "Builder",
                BindingFlags.Public | BindingFlags.Static | BindingFlags.FlattenHierarchy)
            ?? throw new InvalidOperationException("Generated DbConnection type must expose a public Builder() method.");
        var builder = builderMethod.Invoke(null, null)
            ?? throw new InvalidOperationException("Generated DbConnection.Builder() returned null.");

        builder = InvokeMethod(builder, "WithUri", NormalizeUri(settings.Host));
        builder = InvokeMethod(builder, "WithDatabaseName", settings.Database);
        builder = InvokeMethod(builder, "WithCompression", MapCompressionMode(settings.CompressionMode));

        // Story 2.2: inject credentials token when provided
        if (!string.IsNullOrWhiteSpace(settings.Credentials))
            builder = InvokeMethod(builder, "WithToken", settings.Credentials);

        builder = InvokeMethod(builder, "OnConnect", CreateConnectCallback(builder, sink));
        builder = InvokeMethod(builder, "OnConnectError", CreateConnectErrorCallback(builder, sink));
        builder = InvokeMethod(builder, "OnDisconnect", CreateDisconnectCallback(builder, sink));
        _dbConnection = (IDbConnection?)InvokeMethod(builder, "Build")
            ?? throw new InvalidOperationException("Generated DbConnection.Builder().Build() did not return an IDbConnection.");
    }

    public void FrameTick()
    {
        _dbConnection?.FrameTick();
    }

    public void Close()
    {
        var connection = _dbConnection;
        _dbConnection = null;
        connection?.Disconnect();
    }

    internal static MessageCompressionMode GetEffectiveCompressionMode(MessageCompressionMode requestedCompressionMode)
    {
        // The pinned 2.1.x client runtime currently canonicalizes Brotli requests to Gzip.
        return requestedCompressionMode switch
        {
            MessageCompressionMode.Brotli => MessageCompressionMode.Gzip,
            _ => requestedCompressionMode,
        };
    }

    private static string NormalizeUri(string host)
    {
        var trimmedHost = host.Trim();
        if (trimmedHost.StartsWith("ws://", StringComparison.OrdinalIgnoreCase)
            || trimmedHost.StartsWith("wss://", StringComparison.OrdinalIgnoreCase))
        {
            return trimmedHost;
        }

        return $"wss://{trimmedHost}";
    }

    private static SpacetimeDB.Compression MapCompressionMode(MessageCompressionMode compressionMode)
    {
        return compressionMode switch
        {
            MessageCompressionMode.None => SpacetimeDB.Compression.None,
            MessageCompressionMode.Gzip => SpacetimeDB.Compression.Gzip,
            MessageCompressionMode.Brotli => SpacetimeDB.Compression.Brotli,
            _ => throw new ArgumentOutOfRangeException(nameof(compressionMode), compressionMode, "Unsupported compression mode."),
        };
    }

    private static object InvokeMethod(object target, string methodName, params object[] args)
    {
        var method = target.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .FirstOrDefault(candidate => candidate.Name == methodName && candidate.GetParameters().Length == args.Length)
            ?? throw new InvalidOperationException($"Unable to find method '{methodName}' on generated connection builder.");

        return method.Invoke(target, args)
            ?? throw new InvalidOperationException($"Generated connection builder method '{methodName}' returned null.");
    }

    // SDK UPGRADE GUARD — `OnConnect` delegate shape assumption
    //
    // Built against `SpacetimeDB.ClientSDK 2.1.0`, whose generated `OnConnect` callback is
    // `Action<IDbConnection, Identity, string>` — parameter 0 is the connection, parameter 1 is
    // the identity struct, and the final parameter is the token string.
    //
    // This method hard-codes those positional assumptions (`parameterExpressions[1]` for identity,
    // `[^1]` for token). If a future SDK release reorders or inserts parameters, the lambda will
    // either throw at invocation time or silently bind the wrong argument — no build-time signal.
    //
    // When upgrading the SDK, re-verify the generated `OnConnect` delegate signature and update
    // both indices here and the matching test in
    // `tests/test_story_1_4_adapter_boundary.py` (isolation-boundary contract).
    private static Delegate CreateConnectCallback(object builder, IConnectionEventSink sink)
    {
        var delegateType = GetCallbackType(builder, "OnConnect");
        var invoke = delegateType.GetMethod("Invoke")
            ?? throw new InvalidOperationException("Generated OnConnect callback is missing an Invoke method.");
        var parameters = invoke.GetParameters();
        var parameterExpressions = CreateParameters(parameters);
        var sinkExpression = Expression.Constant(sink);

        // param[1] = SpacetimeDB.Identity struct; call ToString() to cross the isolation boundary
        var identityExpression = parameterExpressions[1];
        var toStringMethod = identityExpression.Type.GetMethod("ToString", Type.EmptyTypes)
            ?? typeof(object).GetMethod("ToString", Type.EmptyTypes)!;
        var identityStringExpression = Expression.Call(identityExpression, toStringMethod);

        // param[^1] = string token (last parameter) — see SDK UPGRADE GUARD above
        var tokenExpression = parameterExpressions[^1];

        var body = Expression.Call(
            sinkExpression,
            typeof(IConnectionEventSink).GetMethod(nameof(IConnectionEventSink.OnConnected))!,
            identityStringExpression,
            tokenExpression
        );

        return Expression.Lambda(delegateType, body, parameterExpressions).Compile();
    }

    private static Delegate CreateConnectErrorCallback(object builder, IConnectionEventSink sink)
    {
        var delegateType = GetCallbackType(builder, "OnConnectError");
        var invoke = delegateType.GetMethod("Invoke")
            ?? throw new InvalidOperationException("Generated OnConnectError callback is missing an Invoke method.");
        var parameterExpressions = CreateParameters(invoke.GetParameters());
        var sinkExpression = Expression.Constant(sink);
        var body = Expression.Call(
            sinkExpression,
            typeof(IConnectionEventSink).GetMethod(nameof(IConnectionEventSink.OnConnectError))!,
            parameterExpressions[0]
        );

        return Expression.Lambda(delegateType, body, parameterExpressions).Compile();
    }

    private static Delegate CreateDisconnectCallback(object builder, IConnectionEventSink sink)
    {
        var delegateType = GetCallbackType(builder, "OnDisconnect");
        var invoke = delegateType.GetMethod("Invoke")
            ?? throw new InvalidOperationException("Generated OnDisconnect callback is missing an Invoke method.");
        var parameterExpressions = CreateParameters(invoke.GetParameters());
        var sinkExpression = Expression.Constant(sink);
        var errorExpression = parameterExpressions[^1];
        var body = Expression.Call(
            sinkExpression,
            typeof(IConnectionEventSink).GetMethod(nameof(IConnectionEventSink.OnDisconnected))!,
            errorExpression
        );

        return Expression.Lambda(delegateType, body, parameterExpressions).Compile();
    }

    private static Type GetCallbackType(object builder, string methodName)
    {
        var callbackMethod = builder.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .FirstOrDefault(candidate => candidate.Name == methodName && candidate.GetParameters().Length == 1)
            ?? throw new InvalidOperationException($"Unable to find generated builder callback method '{methodName}'.");

        return callbackMethod.GetParameters()[0].ParameterType;
    }

    private static ParameterExpression[] CreateParameters(IReadOnlyList<ParameterInfo> parameters)
    {
        var expressions = new ParameterExpression[parameters.Count];
        for (var index = 0; index < parameters.Count; index++)
            expressions[index] = Expression.Parameter(parameters[index].ParameterType, parameters[index].Name);

        return expressions;
    }

    private static Type ResolveGeneratedDbConnectionType()
    {
        foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
        {
            var directType = assembly.GetType("SpacetimeDB.Types.DbConnection", throwOnError: false);
            if (IsGeneratedDbConnectionType(directType))
                return directType!;

            foreach (var candidate in SafeGetTypes(assembly))
            {
                if (IsGeneratedDbConnectionType(candidate))
                    return candidate;
            }
        }

        throw new InvalidOperationException(
            "Generated bindings are required before connecting. Compile a module that exposes a DbConnection type with Builder()."
        );
    }

    private static bool IsGeneratedDbConnectionType(Type? candidate)
    {
        return candidate != null
            && candidate.Name == "DbConnection"
            && typeof(IDbConnection).IsAssignableFrom(candidate)
            && candidate.GetMethod(
                "Builder",
                BindingFlags.Public | BindingFlags.Static | BindingFlags.FlattenHierarchy) != null;
    }

    private static IEnumerable<Type> SafeGetTypes(Assembly assembly)
    {
        try
        {
            return assembly.GetTypes();
        }
        catch (ReflectionTypeLoadException ex)
        {
            return ex.Types.Where(type => type != null)!;
        }
    }
}

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

internal interface IConnectionTelemetrySink
{
    void OnInboundMessageReceived(int byteCount);
}

/// <summary>
/// Flattened, runtime-neutral reading for a single SpacetimeDB <c>NetworkRequestTracker</c>.
/// All SDK-tuple/nullable unwrapping happens inside <see cref="SpacetimeSdkConnectionAdapter"/>
/// before the reading crosses into the collector, so this struct carries only scalars.
/// A <c>readonly struct</c> keeps the caller-supplied buffer value-typed and allocation-free.
/// </summary>
internal readonly struct CategoryTrackerReading
{
    internal CategoryTrackerReading(
        double minMs,
        double maxMs,
        double allTimeMinMs,
        double allTimeMaxMs,
        long sampleCount,
        long pendingRequests)
    {
        MinMs = minMs;
        MaxMs = maxMs;
        AllTimeMinMs = allTimeMinMs;
        AllTimeMaxMs = allTimeMaxMs;
        SampleCount = sampleCount;
        PendingRequests = pendingRequests;
    }

    internal double MinMs { get; }

    internal double MaxMs { get; }

    internal double AllTimeMinMs { get; }

    internal double AllTimeMaxMs { get; }

    internal long SampleCount { get; }

    internal long PendingRequests { get; }
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
    /// <summary>
    /// Number of category trackers surfaced by <see cref="TryReadCategoryTelemetry"/>, matching
    /// the 9 public <c>CategoryTelemetry</c> properties on <c>ConnectionTelemetryStats</c>.
    /// </summary>
    internal const int CategoryTrackerCount = 9;

    /// <summary>
    /// Rolling latency window (seconds) handed to <c>NetworkRequestTracker.GetMinMaxTimes(int)</c>.
    /// Reuses the same 1-second window the per-second rate path uses.
    /// </summary>
    private const int WindowSeconds = 1;

    private IDbConnection? _dbConnection;
    private object? _telemetryWebSocket;
    private Delegate? _inboundMessageHandler;

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
        var dbConnectionType = GeneratedBindingTypeResolver.ResolveDbConnectionType(
            settings.ResolveGeneratedBindingsNamespace());
        var builderMethod = dbConnectionType.GetMethod(
                "Builder",
                BindingFlags.Public | BindingFlags.Static | BindingFlags.FlattenHierarchy)
            ?? throw new InvalidOperationException("Generated DbConnection type must expose a public Builder() method.");
        var builder = builderMethod.Invoke(null, null)
            ?? throw new InvalidOperationException("Generated DbConnection.Builder() returned null.");

        builder = InvokeMethod(builder, "WithUri", NormalizeUri(settings.Host));
        builder = InvokeMethod(builder, "WithDatabaseName", settings.Database);
        builder = InvokeMethod(builder, "WithCompression", MapCompressionMode(settings.CompressionMode));
        builder = InvokeMethod(builder, "WithLightMode", settings.LightMode);
        builder = InvokeMethod(builder, "WithConfirmedReads", settings.ConfirmedReads);

        // Story 2.2: inject credentials token when provided
        if (!string.IsNullOrWhiteSpace(settings.Credentials))
            builder = InvokeMethod(builder, "WithToken", settings.Credentials);

        builder = InvokeMethod(builder, "OnConnect", CreateConnectCallback(builder, sink));
        builder = InvokeMethod(builder, "OnConnectError", CreateConnectErrorCallback(builder, sink));
        builder = InvokeMethod(builder, "OnDisconnect", CreateDisconnectCallback(builder, sink));
        _dbConnection = (IDbConnection?)InvokeMethod(builder, "Build")
            ?? throw new InvalidOperationException("Generated DbConnection.Builder().Build() did not return an IDbConnection.");

        if (sink is IConnectionTelemetrySink telemetrySink)
            AttachTelemetryHooks(telemetrySink);
    }

    public void FrameTick()
    {
        _dbConnection?.FrameTick();
    }

    public void Close()
    {
        DetachTelemetryHooks();
        var connection = _dbConnection;
        _dbConnection = null;
        connection?.Disconnect();
    }

    internal bool TryReadTrackerCounts(out (long MessagesSent, long MessagesReceived) trackerCounts)
    {
        var stats = TryGetStats();
        if (stats == null)
        {
            trackerCounts = default;
            return false;
        }

        var outboundMessages =
            GetTrackedRequestCount(stats.SubscriptionRequestTracker) +
            GetTrackedRequestCount(stats.ReducerRequestTracker) +
            GetTrackedRequestCount(stats.OneOffRequestTracker) +
            GetTrackedRequestCount(stats.ProcedureRequestTracker);

        var inboundMessages = stats.ParseMessageTracker?.GetSampleCount() ?? 0;
        trackerCounts = (outboundMessages, inboundMessages);
        return true;
    }

    /// <summary>
    /// Reads all 9 <c>NetworkRequestTracker</c>s in a fixed documented order and flattens each
    /// tracker's windowed/all-time latency tuples and counts into the caller-supplied
    /// preallocated <paramref name="buffer"/> (length <see cref="CategoryTrackerCount"/>). This
    /// is the ONLY place the SDK tuple/nullable shapes are unwrapped — see Design Notes in the
    /// g3/g4 observability spec for the empirically-confirmed shape:
    /// <c>GetMinMaxTimes(int)</c> returns <c>((min,label),(max,label))?</c> and
    /// <c>AllTimeMin</c>/<c>AllTimeMax</c> return <c>(TimeSpan,label)?</c>; the trailing label is
    /// SDK-internal and discarded. A <c>null</c> (idle/empty window, or pre-first-sample all-time)
    /// coalesces to <c>0.0</c>.
    ///
    /// Returns <c>false</c> and leaves <paramref name="buffer"/> untouched when no live session
    /// exposes <c>stats</c>. Allocation-free: it only writes into the supplied buffer.
    ///
    /// Fixed order (index → category): 0 Reducers, 1 Procedures, 2 Subscriptions, 3 OneOffQueries,
    /// 4 AllReducers, 5 ParseMessageQueue, 6 ParseMessage, 7 ApplyMessageQueue, 8 ApplyMessage.
    /// </summary>
    internal bool TryReadCategoryTelemetry(CategoryTrackerReading[] buffer)
    {
        ArgumentNullException.ThrowIfNull(buffer);

        // Runtime guard for the fixed-order coupling: this method writes indices [0..CategoryTrackerCount-1].
        // CategoryTrackerCount is the single source of truth shared with the collector's _categories
        // array length (asserted equal there). A too-small buffer is a programming fault, surfaced
        // loudly here rather than as a torn/partial write (2026-05-28 amendment, finding 3).
        if (buffer.Length < CategoryTrackerCount)
        {
            throw new ArgumentException(
                $"Category telemetry buffer must hold at least {CategoryTrackerCount} readings; got {buffer.Length}.",
                nameof(buffer));
        }

        var stats = TryGetStats();
        if (stats == null)
            return false;

        buffer[0] = ReadTracker(stats.ReducerRequestTracker);
        buffer[1] = ReadTracker(stats.ProcedureRequestTracker);
        buffer[2] = ReadTracker(stats.SubscriptionRequestTracker);
        buffer[3] = ReadTracker(stats.OneOffRequestTracker);
        buffer[4] = ReadTracker(stats.AllReducersTracker);
        buffer[5] = ReadTracker(stats.ParseMessageQueueTracker);
        buffer[6] = ReadTracker(stats.ParseMessageTracker);
        buffer[7] = ReadTracker(stats.ApplyMessageQueueTracker);
        buffer[8] = ReadTracker(stats.ApplyMessageTracker);
        return true;
    }

    private static CategoryTrackerReading ReadTracker(NetworkRequestTracker? tracker)
    {
        if (tracker == null)
            return default;

        // GetMinMaxTimes(int) → ((min: TimeSpan, label: string), (max: TimeSpan, label: string))?
        // AllTimeMin/AllTimeMax → (TimeSpan, label: string)?  — labels discarded at the boundary.
        // Every latency scalar is floored to 0.0: null (idle/empty window) coalesces to 0.0, and a
        // non-positive/non-finite TimeSpan (e.g. a backward clock adjustment on the SDK side) is
        // clamped to 0.0 by FloorLatencyMs. This keeps the public CurrentTelemetry.<Category>.*Ms
        // scalars on the same 0.0 floor as the sibling RecordReducerRoundTrip path
        // (LastReducerRoundTripMilliseconds clamps `elapsed < 0 ? 0`) and the Math.Max(0, ...)
        // Performance-monitor callables, so the public surface never disagrees with the monitors.
        var window = tracker.GetMinMaxTimes(WindowSeconds);
        var minMs = FloorLatencyMs(window?.Item1.Item1.TotalMilliseconds ?? 0.0);
        var maxMs = FloorLatencyMs(window?.Item2.Item1.TotalMilliseconds ?? 0.0);
        var allTimeMinMs = FloorLatencyMs(tracker.AllTimeMin?.Item1.TotalMilliseconds ?? 0.0);
        var allTimeMaxMs = FloorLatencyMs(tracker.AllTimeMax?.Item1.TotalMilliseconds ?? 0.0);

        return new CategoryTrackerReading(
            minMs,
            maxMs,
            allTimeMinMs,
            allTimeMaxMs,
            tracker.GetSampleCount(),
            tracker.GetRequestsAwaitingResponse());
    }

    // Clamps a raw tracker latency (in ms) to the documented 0.0 floor: NaN/Infinity and negative
    // durations (a non-monotonic clock between request start and completion on the SDK side) are
    // mapped to 0.0. Allocation-free; keeps the flattened scalars finite and non-negative before
    // they cross the isolation boundary into ConnectionTelemetryStats / the public surface.
    private static double FloorLatencyMs(double milliseconds) =>
        double.IsFinite(milliseconds) && milliseconds > 0.0 ? milliseconds : 0.0;

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

    private void AttachTelemetryHooks(IConnectionTelemetrySink telemetrySink)
    {
        if (_dbConnection == null)
            return;

        var webSocketField = _dbConnection.GetType().GetField(
            "webSocket",
            BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.FlattenHierarchy);
        var webSocket = webSocketField?.GetValue(_dbConnection);
        if (webSocket == null)
            return;

        var onMessageEvent = webSocket.GetType().GetEvent(
            "OnMessage",
            BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        var delegateType = onMessageEvent?.EventHandlerType;
        if (delegateType == null)
            return;

        var callback = CreateInboundMessageCallback(delegateType, telemetrySink);
        if (callback == null)
            return;

        onMessageEvent!.AddEventHandler(webSocket, callback);
        _telemetryWebSocket = webSocket;
        _inboundMessageHandler = callback;
    }

    private void DetachTelemetryHooks()
    {
        if (_telemetryWebSocket == null || _inboundMessageHandler == null)
            return;

        var onMessageEvent = _telemetryWebSocket.GetType().GetEvent(
            "OnMessage",
            BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        onMessageEvent?.RemoveEventHandler(_telemetryWebSocket, _inboundMessageHandler);
        _telemetryWebSocket = null;
        _inboundMessageHandler = null;
    }

    private static Delegate? CreateInboundMessageCallback(Type delegateType, IConnectionTelemetrySink telemetrySink)
    {
        var invoke = delegateType.GetMethod("Invoke");
        if (invoke == null)
            return null;

        var parameters = invoke.GetParameters();
        if (parameters.Length == 0 || parameters[0].ParameterType != typeof(byte[]))
            return null;

        var parameterExpressions = CreateParameters(parameters);
        var telemetrySinkExpression = Expression.Constant(telemetrySink);
        var byteCountExpression = Expression.ArrayLength(parameterExpressions[0]);
        var body = Expression.Call(
            telemetrySinkExpression,
            typeof(IConnectionTelemetrySink).GetMethod(nameof(IConnectionTelemetrySink.OnInboundMessageReceived))!,
            byteCountExpression);

        return Expression.Lambda(delegateType, body, parameterExpressions).Compile();
    }

    private Stats? TryGetStats()
    {
        if (_dbConnection == null)
            return null;

        var statsField = _dbConnection.GetType().GetField(
            "stats",
            BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.FlattenHierarchy);
        return statsField?.GetValue(_dbConnection) as Stats;
    }

    private static long GetTrackedRequestCount(NetworkRequestTracker? tracker)
    {
        if (tracker == null)
            return 0;

        return tracker.GetSampleCount() + tracker.GetRequestsAwaitingResponse();
    }
}

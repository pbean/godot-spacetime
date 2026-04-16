using System;
using System.Collections.Generic;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using GodotSpacetime.Queries;
using SpacetimeDB;

namespace GodotSpacetime.Runtime.Platform.DotNet;

/// <summary>
/// Adapter for the SpacetimeDB .NET ClientSDK one-off query layer.
///
/// This class is the ONLY location in the codebase where <c>SpacetimeDB.ClientSDK</c>
/// query types may be referenced directly. All higher-level internal services and all
/// public SDK surfaces depend on <c>GodotSpacetime.*</c> contracts rather than on
/// <c>SpacetimeDB.*</c> types.
/// </summary>
internal sealed class SpacetimeSdkQueryAdapter
{
    private static readonly TimeSpan DefaultTimeout = TimeSpan.FromSeconds(30);
    // These static lookups are verified against the pinned SpacetimeDB.ClientSDK 2.1.0 package.
    // If the SDK is upgraded and renames these members, class initialization throws
    // TypeInitializationException wrapping the InvalidOperationException below — check the
    // inner exception message for the specific missing member name and the SDK changelog.
    private static readonly MethodInfo ClientTableTypeGetter = typeof(IRemoteTableHandle).GetMethod(
        "get_ClientTableType",
        BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)
        ?? throw new InvalidOperationException(
            "SpacetimeDB.ClientSDK IRemoteTableHandle.ClientTableType getter not found. " +
            "Verify the pinned SDK version exposes this property on IRemoteTableHandle.");
    private static readonly MethodInfo RemoteTableNameGetter = typeof(IRemoteTableHandle).GetMethod(
        "get_RemoteTableName",
        BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)
        ?? throw new InvalidOperationException(
            "SpacetimeDB.ClientSDK IRemoteTableHandle.RemoteTableName getter not found. " +
            "Verify the pinned SDK version exposes this property on IRemoteTableHandle.");

    internal Task<TRow[]> QueryAsync<TRow>(object remoteTables, string sqlClause, TimeSpan? timeout = null)
        where TRow : class
    {
        ArgumentNullException.ThrowIfNull(remoteTables);

        if (string.IsNullOrWhiteSpace(sqlClause))
            throw new ArgumentException("QueryAsync() requires a non-empty SQL clause.", nameof(sqlClause));

        if (timeout.HasValue && timeout.Value <= TimeSpan.Zero)
            throw new ArgumentException(
                "QueryAsync() timeout must be greater than zero when provided.",
                nameof(timeout));

        var requestedAt = DateTimeOffset.UtcNow;
        var target = ResolveTarget<TRow>(remoteTables);

        Task<TRow[]> queryTask;
        try
        {
            queryTask = InvokeRemoteQuery<TRow>(target.Handle, sqlClause);
        }
        catch (TargetInvocationException ex) when (ex.InnerException != null)
        {
            throw CreateRecoverableQueryError(
                typeof(TRow),
                target.TableName,
                sqlClause,
                requestedAt,
                ex.InnerException);
        }

        return AwaitQueryAsync(
            queryTask,
            typeof(TRow),
            target.TableName,
            sqlClause,
            requestedAt,
            timeout ?? DefaultTimeout);
    }

    private static async Task<TRow[]> AwaitQueryAsync<TRow>(
        Task<TRow[]> queryTask,
        Type requestedRowType,
        string tableName,
        string sqlClause,
        DateTimeOffset requestedAt,
        TimeSpan timeout)
        where TRow : class
    {
        var timeoutTask = Task.Delay(timeout);
        var completedTask = await Task.WhenAny(queryTask, timeoutTask).ConfigureAwait(false);
        if (completedTask != queryTask)
        {
            _ = queryTask.ContinueWith(
                static completed => _ = completed.Exception,
                CancellationToken.None,
                TaskContinuationOptions.OnlyOnFaulted | TaskContinuationOptions.ExecuteSynchronously,
                TaskScheduler.Default);

            throw new OneOffQueryError(
                requestedRowType,
                tableName,
                sqlClause,
                requestedAt,
                $"One-off query against '{tableName}' timed out after {timeout.TotalSeconds:0.###} seconds.",
                OneOffQueryFailureCategory.TimedOut,
                GetRecoveryGuidance(OneOffQueryFailureCategory.TimedOut));
        }

        try
        {
            return await queryTask.ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            throw CreateRecoverableQueryError(
                requestedRowType,
                tableName,
                sqlClause,
                requestedAt,
                ex);
        }
    }

    private static QueryTarget ResolveTarget<TRow>(object remoteTables)
        where TRow : class
    {
        var requestedRowType = typeof(TRow);
        // Enumerate once and reuse for both the primary ClientTableType pass and the fallback
        // generic-argument pass, avoiding a second full reflection scan on every query call.
        var candidates = EnumerateCandidates(remoteTables);

        foreach (var candidate in candidates)
        {
            if (TryGetClientTableType(candidate.Handle, out var clientTableType) &&
                clientTableType == requestedRowType)
            {
                return new QueryTarget(candidate.Handle, TryGetRemoteTableName(candidate.Handle) ?? candidate.MemberName);
            }
        }

        foreach (var candidate in candidates)
        {
            if (TryGetFallbackRowType(candidate.Handle, out var fallbackRowType) &&
                fallbackRowType == requestedRowType)
            {
                return new QueryTarget(candidate.Handle, TryGetRemoteTableName(candidate.Handle) ?? candidate.MemberName);
            }
        }

        throw new InvalidOperationException(
            $"QueryAsync<{requestedRowType.Name}>() does not support row type " +
            $"'{requestedRowType.FullName ?? requestedRowType.Name}'. " +
            "Use a generated row type from the active module bindings.");
    }

    private static Task<TRow[]> InvokeRemoteQuery<TRow>(object handle, string sqlClause)
        where TRow : class
    {
        var remoteQueryMethod = handle.GetType().GetMethod(
            "RemoteQuery",
            BindingFlags.Public | BindingFlags.Instance,
            [typeof(string)]);

        if (remoteQueryMethod == null)
        {
            throw new InvalidOperationException(
                $"Generated table handle '{handle.GetType().FullName ?? handle.GetType().Name}' " +
                "does not expose RemoteQuery(string).");
        }

        var result = remoteQueryMethod.Invoke(handle, [sqlClause]);
        if (result is Task<TRow[]> typedTask)
            return typedTask;

        throw new InvalidOperationException(
            $"Generated table handle '{handle.GetType().FullName ?? handle.GetType().Name}' " +
            $"returned an unexpected RemoteQuery result type '{result?.GetType().FullName ?? "null"}'.");
    }

    private static IReadOnlyList<QueryCandidate> EnumerateCandidates(object remoteTables)
    {
        var candidates = new List<QueryCandidate>();
        var remoteTablesType = remoteTables.GetType();

        foreach (var field in remoteTablesType.GetFields(BindingFlags.Public | BindingFlags.Instance))
        {
            var value = field.GetValue(remoteTables);
            if (value == null || !HasRemoteQueryMethod(value))
                continue;

            candidates.Add(new QueryCandidate(field.Name, value));
        }

        foreach (var property in remoteTablesType.GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            if (property.GetIndexParameters().Length != 0)
                continue;

            object? value;
            try
            {
                value = property.GetValue(remoteTables);
            }
            catch
            {
                continue;
            }

            if (value == null || !HasRemoteQueryMethod(value))
                continue;

            candidates.Add(new QueryCandidate(property.Name, value));
        }

        return candidates;
    }

    private static bool HasRemoteQueryMethod(object handle) =>
        handle.GetType().GetMethod(
            "RemoteQuery",
            BindingFlags.Public | BindingFlags.Instance,
            [typeof(string)]) != null;

    private static bool TryGetClientTableType(object handle, out Type? clientTableType)
    {
        clientTableType = null;
        if (!typeof(IRemoteTableHandle).IsAssignableFrom(handle.GetType()))
            return false;

        clientTableType = ClientTableTypeGetter.Invoke(handle, null) as Type;
        return clientTableType != null;
    }

    private static string? TryGetRemoteTableName(object handle)
    {
        if (!typeof(IRemoteTableHandle).IsAssignableFrom(handle.GetType()))
            return null;

        return RemoteTableNameGetter.Invoke(handle, null) as string;
    }

    private static bool TryGetFallbackRowType(object handle, out Type? rowType)
    {
        rowType = null;
        for (var current = handle.GetType(); current != null; current = current.BaseType)
        {
            if (!current.IsGenericType)
                continue;

            var definition = current.GetGenericTypeDefinition();
            if (definition.Name is not ("RemoteTableHandle`2" or "RemoteTableHandleBase`2"))
                continue;

            var genericArguments = current.GetGenericArguments();
            if (genericArguments.Length == 2)
            {
                rowType = genericArguments[1];
                return true;
            }
        }

        return false;
    }

    private static OneOffQueryError CreateRecoverableQueryError(
        Type requestedRowType,
        string tableName,
        string sqlClause,
        DateTimeOffset requestedAt,
        Exception failure)
    {
        var rootFailure = UnwrapFailure(failure);
        var failureCategory = ClassifyFailure(rootFailure);
        var errorMessage = string.IsNullOrWhiteSpace(rootFailure.Message)
            ? $"One-off query against '{tableName}' failed with {rootFailure.GetType().Name}."
            : rootFailure.Message;

        return new OneOffQueryError(
            requestedRowType,
            tableName,
            sqlClause,
            requestedAt,
            errorMessage,
            failureCategory,
            GetRecoveryGuidance(failureCategory),
            rootFailure);
    }

    private static Exception UnwrapFailure(Exception failure)
    {
        var current = failure;
        while (true)
        {
            if (current is TargetInvocationException targetInvocation && targetInvocation.InnerException != null)
            {
                current = targetInvocation.InnerException;
                continue;
            }

            if (current is AggregateException aggregate && aggregate.InnerExceptions.Count == 1)
            {
                current = aggregate.InnerExceptions[0];
                continue;
            }

            return current;
        }
    }

    private static OneOffQueryFailureCategory ClassifyFailure(Exception failure)
    {
        if (failure is TimeoutException or OperationCanceledException or TaskCanceledException)
            return OneOffQueryFailureCategory.TimedOut;

        var detail = FlattenFailureText(failure);
        if (ContainsAny(detail, "timed out", "timeout", "deadline exceeded"))
            return OneOffQueryFailureCategory.TimedOut;

        if (ContainsAny(
                detail,
                "syntax error",
                "parse error",
                "parser error",
                "invalid sql",
                "unsupported sql",
                "unexpected token",
                "unknown column",
                "unknown table",
                "bad query"))
        {
            return OneOffQueryFailureCategory.InvalidQuery;
        }

        return string.IsNullOrWhiteSpace(detail)
            ? OneOffQueryFailureCategory.Unknown
            : OneOffQueryFailureCategory.Failed;
    }

    private static string FlattenFailureText(Exception failure)
    {
        var messages = new List<string>();
        for (var current = failure; current != null; current = current.InnerException)
        {
            if (!string.IsNullOrWhiteSpace(current.Message))
                messages.Add(current.Message);
        }

        return string.Join(" | ", messages);
    }

    private static bool ContainsAny(string detail, params string[] needles)
    {
        foreach (var needle in needles)
        {
            if (detail.Contains(needle, StringComparison.OrdinalIgnoreCase))
                return true;
        }

        return false;
    }

    private static string GetRecoveryGuidance(OneOffQueryFailureCategory failureCategory) =>
        failureCategory switch
        {
            OneOffQueryFailureCategory.InvalidQuery =>
                "Fix the SQL clause or query shape before retrying. One-off queries use the generated table selected by the requested row type.",
            OneOffQueryFailureCategory.TimedOut =>
                "Retry with a longer timeout only if the query is expected to be slow, otherwise inspect server health and query shape first.",
            OneOffQueryFailureCategory.Failed =>
                "Treat this as a server-side runtime failure. Capture diagnostics, check server logs, and retry only after confirming the failure is transient.",
            _ =>
                "Do not retry automatically. Surface a safe generic error and capture diagnostics for follow-up.",
        };

    private readonly record struct QueryCandidate(string MemberName, object Handle);

    private readonly record struct QueryTarget(object Handle, string TableName);
}

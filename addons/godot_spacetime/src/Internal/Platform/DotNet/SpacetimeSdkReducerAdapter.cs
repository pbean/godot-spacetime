using System;
using SpacetimeDB;

namespace GodotSpacetime.Runtime.Platform.DotNet;

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

    internal void SetConnection(IDbConnection? connection)
    {
        _dbConnection = connection;
    }

    internal void Invoke(object reducerArgs)
    {
        if (_dbConnection == null)
        {
            Console.Error.WriteLine("[GodotSpacetime] SpacetimeSdkReducerAdapter.Invoke called with no active connection — ignoring.");
            return;
        }

        if (reducerArgs is not IReducerArgs)
            throw new ArgumentException(
                $"reducerArgs must implement SpacetimeDB.IReducerArgs, got {reducerArgs?.GetType().FullName ?? "null"}.",
                nameof(reducerArgs));

        // InternalCallReducer<T>(T args) must see the concrete generated reducer type, not IReducerArgs.
        dynamic typedReducerArgs = reducerArgs;
        _dbConnection.InternalCallReducer(typedReducerArgs);
    }

    internal void ClearConnection()
    {
        _dbConnection = null;
    }
}

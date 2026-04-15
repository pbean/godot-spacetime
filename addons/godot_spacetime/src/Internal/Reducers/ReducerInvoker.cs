using System;
using GodotSpacetime.Runtime.Platform.DotNet;

namespace GodotSpacetime.Runtime.Reducers;

/// <summary>
/// Internal coordinator for reducer invocations.
///
/// Validates invocation arguments and delegates to <see cref="SpacetimeSdkReducerAdapter"/>.
/// This class must NOT import or reference <c>SpacetimeDB.*</c> types directly —
/// that dependency is encapsulated inside <see cref="SpacetimeSdkReducerAdapter"/>.
/// </summary>
internal sealed class ReducerInvoker
{
    private readonly SpacetimeSdkReducerAdapter _adapter;

    internal ReducerInvoker(SpacetimeSdkReducerAdapter adapter)
    {
        _adapter = adapter;
    }

    internal void Invoke(object reducerArgs)
    {
        ArgumentNullException.ThrowIfNull(reducerArgs);
        _adapter.Invoke(reducerArgs);
    }
}

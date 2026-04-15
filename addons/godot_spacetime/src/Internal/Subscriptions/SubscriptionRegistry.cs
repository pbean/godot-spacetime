using System;
using System.Collections.Generic;
using GodotSpacetime.Subscriptions;

namespace GodotSpacetime.Runtime.Subscriptions;

/// <summary>
/// Tracks active <see cref="SubscriptionHandle"/> instances within the current session.
/// Used by <c>SpacetimeConnectionService</c> to maintain a stable reference to every
/// subscription scope that has been applied and to clean up on session end.
/// </summary>
internal sealed class SubscriptionRegistry
{
    private readonly Dictionary<Guid, SubscriptionHandle> _handles = new();

    /// <summary>Registers a handle when a subscription is applied.</summary>
    internal void Register(SubscriptionHandle handle)
    {
        _handles[handle.HandleId] = handle;
    }

    /// <summary>Removes a handle when a subscription is unsubscribed or errors.</summary>
    internal void Unregister(Guid handleId)
    {
        _handles.Remove(handleId);
    }

    /// <summary>All currently tracked active subscription handles.</summary>
    internal IReadOnlyCollection<SubscriptionHandle> ActiveHandles => _handles.Values;

    /// <summary>Clears all tracked handles — called when a session disconnects.</summary>
    internal void Clear()
    {
        _handles.Clear();
    }
}

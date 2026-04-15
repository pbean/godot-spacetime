using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using GodotSpacetime.Subscriptions;

namespace GodotSpacetime.Runtime.Subscriptions;

/// <summary>
/// Pairs a <see cref="SubscriptionHandle"/> with the raw SDK subscription object returned
/// by the SpacetimeDB SDK after calling Subscribe(). The SDK object is stored so that
/// <c>TryUnsubscribe</c> can be invoked on it when the subscription scope is closed.
/// </summary>
internal sealed record SubscriptionEntry(SubscriptionHandle Handle, object? SdkSubscription);

/// <summary>
/// Tracks active <see cref="SubscriptionHandle"/> instances within the current session.
/// Used by <c>SpacetimeConnectionService</c> to maintain a stable reference to every
/// subscription scope that has been applied and to clean up on session end.
/// </summary>
internal sealed class SubscriptionRegistry
{
    private readonly Dictionary<Guid, SubscriptionEntry> _handles = new();

    /// <summary>Registers a handle when a subscription is applied. The SDK subscription object may be set later via <see cref="UpdateSdkSubscription"/>.</summary>
    internal void Register(SubscriptionHandle handle, object? sdkSubscription = null)
    {
        _handles[handle.HandleId] = new SubscriptionEntry(handle, sdkSubscription);
    }

    /// <summary>Updates the stored SDK subscription object for an existing handle entry.</summary>
    internal void UpdateSdkSubscription(Guid handleId, object? sdkSubscription)
    {
        if (_handles.TryGetValue(handleId, out var existing))
            _handles[handleId] = existing with { SdkSubscription = sdkSubscription };
    }

    /// <summary>Removes a handle when a subscription is unsubscribed or errors.</summary>
    internal void Unregister(Guid handleId)
    {
        _handles.Remove(handleId);
    }

    /// <summary>Looks up the entry for the given handle ID.</summary>
    internal bool TryGetEntry(Guid handleId, [NotNullWhen(true)] out SubscriptionEntry? entry)
    {
        return _handles.TryGetValue(handleId, out entry);
    }

    /// <summary>All currently tracked active subscription entries.</summary>
    internal IReadOnlyCollection<SubscriptionEntry> ActiveHandles => _handles.Values;

    /// <summary>Closes and clears all tracked handles — called when a session disconnects.</summary>
    internal void Clear()
    {
        foreach (var entry in _handles.Values)
            entry.Handle.Close();

        _handles.Clear();
    }
}

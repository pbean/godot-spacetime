using System;
using Godot;

namespace GodotSpacetime.Subscriptions;

/// <summary>
/// Event payload raised when a subscription's initial synchronization is complete
/// and the local cache slice is ready to read.
/// Corresponds to the <c>subscription.applied</c> SDK domain event.
/// </summary>
public partial class SubscriptionAppliedEvent : RefCounted
{
    public SubscriptionHandle Handle { get; }

    public DateTimeOffset AppliedAt { get; }

    internal SubscriptionAppliedEvent(SubscriptionHandle handle)
    {
        Handle = handle;
        AppliedAt = DateTimeOffset.UtcNow;
    }
}

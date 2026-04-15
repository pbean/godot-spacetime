using System;
using Godot;

namespace GodotSpacetime.Subscriptions;

/// <summary>
/// Event payload raised when a subscription fails — either at the point of application
/// or due to a runtime subscription error.
/// Corresponds to the <c>subscription.failed</c> SDK domain event.
/// </summary>
public partial class SubscriptionFailedEvent : RefCounted
{
    public SubscriptionHandle Handle { get; }

    public string ErrorMessage { get; }

    public DateTimeOffset FailedAt { get; }

    internal SubscriptionFailedEvent(SubscriptionHandle handle, Exception error)
    {
        Handle = handle;
        ErrorMessage = error.Message;
        FailedAt = DateTimeOffset.UtcNow;
    }
}

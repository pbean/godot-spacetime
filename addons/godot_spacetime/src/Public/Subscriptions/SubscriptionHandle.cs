using System;
using Godot;

namespace GodotSpacetime.Subscriptions;

/// <summary>
/// A handle representing an active subscription query scope.
/// Returned by SpacetimeClient when a subscription is applied.
/// Use this handle to manage the subscription's lifecycle.
/// </summary>
public partial class SubscriptionHandle : RefCounted
{
    public Guid HandleId { get; }

    /// <summary>
    /// The current lifecycle state of this subscription.
    /// Initialized to <see cref="SubscriptionStatus.Active"/> when the handle is created.
    /// </summary>
    public SubscriptionStatus Status { get; private set; }

    internal SubscriptionHandle()
    {
        HandleId = Guid.NewGuid();
        Status = SubscriptionStatus.Active;
    }

    /// <summary>
    /// Marks this handle as superseded by a replacement subscription.
    /// Called after the new subscription is confirmed applied by the server.
    /// </summary>
    internal void Supersede() => Status = SubscriptionStatus.Superseded;

    /// <summary>
    /// Marks this handle as closed. Called when <c>Unsubscribe()</c> is invoked
    /// or when the subscription errors before reaching applied state.
    /// </summary>
    internal void Close() => Status = SubscriptionStatus.Closed;
}

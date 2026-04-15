namespace GodotSpacetime.Subscriptions;

/// <summary>
/// Represents the lifecycle state of a <see cref="SubscriptionHandle"/>.
/// </summary>
public enum SubscriptionStatus
{
    /// <summary>The subscription is active and the local cache is authoritative for its query scope.</summary>
    Active,

    /// <summary>
    /// The subscription has been superseded by a replacement. The old handle's data is no longer
    /// authoritative; the new handle's <c>SubscriptionApplied</c> event has already fired.
    /// </summary>
    Superseded,

    /// <summary>The subscription has been explicitly closed via <c>Unsubscribe()</c>.</summary>
    Closed
}

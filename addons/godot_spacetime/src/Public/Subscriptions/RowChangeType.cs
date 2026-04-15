namespace GodotSpacetime.Subscriptions;

/// <summary>
/// The type of row-level change in a subscribed table.
/// Corresponds to the <c>subscription.row_changed</c> SDK domain event.
/// </summary>
public enum RowChangeType
{
    /// <summary>A new row was inserted into the local cache.</summary>
    Insert,

    /// <summary>An existing row was updated in the local cache.</summary>
    Update,

    /// <summary>A row was removed from the local cache.</summary>
    Delete
}

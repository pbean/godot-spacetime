using System;
using Godot;

namespace GodotSpacetime.Subscriptions;

/// <summary>
/// Event payload raised when a row-level change occurs in a subscribed table.
/// Emitted by <see cref="GodotSpacetime.SpacetimeClient.RowChanged"/> after the
/// <c>SubscriptionApplied</c> signal fires and the subscription is active.
///
/// Corresponds to the <c>subscription.row_changed</c> SDK domain event.
///
/// See <c>docs/runtime-boundaries.md</c> — "Row Changes — Observing Live Cache Updates" for usage.
/// </summary>
public partial class RowChangedEvent : RefCounted
{
    /// <summary>
    /// The PascalCase name of the table in which the row changed.
    /// Matches the generated property name on the <c>RemoteTables</c> type
    /// (e.g., <c>"SmokeTest"</c> for a <c>smoke_test</c> module table).
    /// </summary>
    public string TableName { get; }

    /// <summary>
    /// The kind of row change: Insert, Update, or Delete.
    /// </summary>
    public RowChangeType ChangeType { get; }

    /// <summary>
    /// The row value before the change. Null for <see cref="RowChangeType.Insert"/> events.
    /// Cast to the generated row type to access typed fields.
    /// </summary>
    public object? OldRow { get; }

    /// <summary>
    /// The row value after the change. Null for <see cref="RowChangeType.Delete"/> events.
    /// Cast to the generated row type to access typed fields.
    /// </summary>
    public object? NewRow { get; }

    internal RowChangedEvent(
        string tableName,
        RowChangeType changeType,
        object? oldRow,
        object? newRow)
    {
        TableName = tableName;
        ChangeType = changeType;
        OldRow = oldRow;
        NewRow = newRow;
    }
}

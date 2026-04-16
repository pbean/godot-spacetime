using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Godot;
using GodotSpacetime.Subscriptions;

namespace GodotSpacetime.Scenes;

/// <summary>
/// A scene-tree node that subscribes to <see cref="GodotSpacetime.SpacetimeClient.RowChanged"/>
/// and re-emits filtered row events as table-scoped signals.
///
/// Add a RowReceiver to any scene, set <see cref="TableName"/> to a generated table property name
/// (PascalCase, matching the <c>RemoteTables</c> generated type), and connect to
/// <c>row_inserted</c>, <c>row_updated</c>, or <c>row_deleted</c> to receive typed row events
/// without writing signal connection boilerplate.
///
/// Requires <c>SpacetimeClient</c> registered as an autoload at <c>/root/SpacetimeClient</c>.
/// A warning is pushed (not an error) if the autoload is not found at runtime.
///
/// See <c>docs/runtime-boundaries.md</c> — "RowReceiver — Scene-Tree Row Event Integration" for usage.
/// </summary>
[Tool]
public partial class RowReceiver : Node
{
    /// <summary>
    /// The PascalCase name of the table this receiver filters on.
    /// Must match the generated property name on the <c>RemoteTables</c> type
    /// (e.g., <c>"SmokeTest"</c> for a <c>smoke_test</c> module table).
    /// Set this in the Inspector dropdown, which is populated at editor time via reflection.
    /// </summary>
    [Export] public string TableName { get; set; } = "";

    /// <summary>Emitted when a row is inserted into the subscribed table.</summary>
    [Signal] public delegate void RowInsertedEventHandler(RowChangedEvent e);

    /// <summary>Emitted when a row in the subscribed table is updated.</summary>
    [Signal] public delegate void RowUpdatedEventHandler(RowChangedEvent e);

    /// <summary>Emitted when a row is removed from the subscribed table.</summary>
    [Signal] public delegate void RowDeletedEventHandler(RowChangedEvent e);

    private SpacetimeClient? _client;

    /// <summary>
    /// Returns a property list entry for <see cref="TableName"/> with a <c>PROPERTY_HINT_ENUM</c>
    /// hint string built from the <c>RemoteTables</c> type discovered at editor time.
    /// When no <c>RemoteTables</c> type is found in user assemblies, returns an empty array and the
    /// <c>[Export]</c> plain string fallback is shown in the Inspector.
    /// </summary>
    public override Godot.Collections.Array<Godot.Collections.Dictionary> _GetPropertyList()
    {
        var tableNames = DiscoverTableNames();
        var properties = new Godot.Collections.Array<Godot.Collections.Dictionary>();

        if (tableNames.Length > 0)
        {
            properties.Add(new Godot.Collections.Dictionary
            {
                { "name", "TableName" },
                { "type", (int)Variant.Type.String },
                { "hint", (int)PropertyHint.Enum },
                { "hint_string", string.Join(",", tableNames) },
                { "usage", (int)(PropertyUsageFlags.Default | PropertyUsageFlags.ScriptVariable) }
            });
        }

        return properties;
    }

    /// <summary>
    /// Discovers candidate table names from the first <c>RemoteTables</c> type found in user assemblies.
    /// Skips assemblies whose <c>FullName</c> begins with <c>System</c>, <c>mscorlib</c>,
    /// <c>Microsoft</c>, <c>Godot</c>, <c>SpacetimeDB</c>, or <c>GodotSpacetime</c>.
    /// Supports both field-backed and property-backed generated table members.
    /// Returns an empty array when no <c>RemoteTables</c> type is found.
    /// </summary>
    private static string[] DiscoverTableNames()
    {
        foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
        {
            var fullName = assembly.FullName ?? "";
            if (ShouldSkipAssembly(fullName))
            {
                continue;
            }

            var remoteTables = FindRemoteTablesType(assembly);
            if (remoteTables == null)
                continue;

            return remoteTables
                .GetProperties(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly)
                .Select(property => property.Name)
                .Concat(
                    remoteTables
                        .GetFields(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly)
                        .Select(field => field.Name))
                .Distinct(StringComparer.Ordinal)
                .OrderBy(name => name, StringComparer.Ordinal)
                .ToArray();
        }

        return Array.Empty<string>();
    }

    private static bool ShouldSkipAssembly(string fullName) =>
        fullName.StartsWith("System", StringComparison.Ordinal)
        || fullName.StartsWith("mscorlib", StringComparison.Ordinal)
        || fullName.StartsWith("Microsoft", StringComparison.Ordinal)
        || fullName.StartsWith("Godot", StringComparison.Ordinal)
        || fullName.StartsWith("SpacetimeDB", StringComparison.Ordinal)
        || fullName.StartsWith("GodotSpacetime", StringComparison.Ordinal);

    private static Type? FindRemoteTablesType(Assembly assembly)
    {
        foreach (var candidate in SafeGetTypes(assembly))
        {
            if (candidate.Name == "RemoteTables")
                return candidate;
        }

        return null;
    }

    private static IEnumerable<Type> SafeGetTypes(Assembly assembly)
    {
        try
        {
            return assembly.GetTypes();
        }
        catch (ReflectionTypeLoadException ex)
        {
            return ex.Types.Where(type => type != null)!;
        }
    }

    /// <summary>
    /// Wires this node to <see cref="SpacetimeClient.RowChanged"/> at runtime.
    /// No-op when <see cref="Engine.IsEditorHint"/> returns <c>true</c>.
    /// Pushes a warning (not an error) if the <c>SpacetimeClient</c> autoload is not found.
    /// </summary>
    public override void _Ready()
    {
        if (Engine.IsEditorHint()) return;

        var clientNode = GetNodeOrNull<SpacetimeClient>("/root/SpacetimeClient");
        if (clientNode == null)
        {
            GD.PushWarning("RowReceiver: SpacetimeClient autoload not found at /root/SpacetimeClient. " +
                           "Register SpacetimeClient as an autoload to receive row events.");
            return;
        }

        _client = clientNode;
        _client.RowChanged += OnRowChanged;
    }

    private void OnRowChanged(RowChangedEvent e)
    {
        if (Engine.IsEditorHint()) return;
        if (e.TableName != TableName) return;

        switch (e.ChangeType)
        {
            case RowChangeType.Insert:
                EmitSignal(SignalName.RowInserted, e);
                break;
            case RowChangeType.Update:
                EmitSignal(SignalName.RowUpdated, e);
                break;
            case RowChangeType.Delete:
                EmitSignal(SignalName.RowDeleted, e);
                break;
        }
    }

    /// <summary>
    /// Disconnects from <see cref="SpacetimeClient.RowChanged"/> when removed from the scene tree.
    /// No-op when <see cref="Engine.IsEditorHint"/> returns <c>true</c>.
    /// Guards with <see cref="IsInstanceValid"/> to avoid errors if the autoload was already freed.
    /// </summary>
    public override void _ExitTree()
    {
        if (Engine.IsEditorHint()) return;

        if (IsInstanceValid(_client))
        {
            _client!.RowChanged -= OnRowChanged;
        }

        _client = null;
    }
}

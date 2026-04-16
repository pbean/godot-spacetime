using System;
using System.Linq;
using Godot;
using GodotSpacetime.Runtime.Platform.DotNet;
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
/// By default the node targets <c>/root/SpacetimeClient</c> so existing scenes continue to work
/// unchanged. Set <see cref="ClientPath"/> to retarget the receiver at a different client node.
/// A warning is pushed (not an error) if the target client is not found at runtime.
///
/// See <c>docs/runtime-boundaries.md</c> — "RowReceiver — Scene-Tree Row Event Integration" for usage.
/// </summary>
[Tool]
public partial class RowReceiver : Node
{
    private static readonly NodePath DefaultClientPath = new("/root/SpacetimeClient");

    /// <summary>
    /// The PascalCase name of the table this receiver filters on.
    /// Must match the generated property name on the <c>RemoteTables</c> type
    /// (e.g., <c>"SmokeTest"</c> for a <c>smoke_test</c> module table).
    /// Set this in the Inspector dropdown, which is populated at editor time via reflection.
    /// </summary>
    [Export] public string TableName { get; set; } = "";

    private NodePath _clientPath = DefaultClientPath;

    [Export]
    public NodePath ClientPath
    {
        get => _clientPath;
        set
        {
            _clientPath = value;
            NotifyPropertyListChanged();
        }
    }

    /// <summary>Emitted when a row is inserted into the subscribed table.</summary>
    [Signal] public delegate void RowInsertedEventHandler(RowChangedEvent e);

    /// <summary>Emitted when a row in the subscribed table is updated.</summary>
    [Signal] public delegate void RowUpdatedEventHandler(RowChangedEvent e);

    /// <summary>Emitted when a row is removed from the subscribed table.</summary>
    [Signal] public delegate void RowDeletedEventHandler(RowChangedEvent e);

    private SpacetimeClient? _client;

    /// <summary>
    /// Returns a property list entry for <see cref="TableName"/> with a <c>PROPERTY_HINT_ENUM</c>
    /// hint string built from the selected client's generated <c>RemoteTables</c> type.
    /// When the target client or generated bindings are unavailable, returns an empty array and the
    /// <c>[Export]</c> plain string fallback stays visible in the Inspector.
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
    /// Discovers candidate table names from the generated namespace associated with the selected client.
    /// Supports both field-backed and property-backed generated table members.
    /// Returns an empty array when the selected client cannot be resolved or the generated
    /// bindings are unavailable.
    /// </summary>
    private string[] DiscoverTableNames()
    {
        var generatedBindingsNamespace = ResolveGeneratedBindingsNamespace();
        if (generatedBindingsNamespace == null)
            return Array.Empty<string>();

        return GeneratedBindingTypeResolver.GetRemoteTableNames(generatedBindingsNamespace);
    }

    internal string? GetResolvedRemoteTablesTypeNameForInspection()
    {
        var generatedBindingsNamespace = ResolveGeneratedBindingsNamespace();
        if (generatedBindingsNamespace == null)
            return null;

        return GeneratedBindingTypeResolver.TryResolveRemoteTablesType(generatedBindingsNamespace)?.FullName;
    }

    private string? ResolveGeneratedBindingsNamespace()
    {
        var selectedClient = ResolveSelectedClient();
        if (selectedClient?.Settings != null)
            return selectedClient.Settings.ResolveGeneratedBindingsNamespace();

        return IsDefaultClientPath(ClientPath)
            ? SpacetimeSettings.DefaultGeneratedBindingsNamespace
            : null;
    }

    /// <summary>
    /// Wires this node to <see cref="SpacetimeClient.RowChanged"/> at runtime.
    /// No-op when <see cref="Engine.IsEditorHint"/> returns <c>true</c>.
    /// Pushes a warning (not an error) if the selected client is not found.
    /// </summary>
    public override void _Ready()
    {
        if (Engine.IsEditorHint()) return;

        var clientNode = ResolveSelectedClient();
        if (clientNode == null)
        {
            GD.PushWarning(
                "RowReceiver: target SpacetimeClient not found at " +
                $"'{FormatClientPath(ClientPath)}'. Configure ClientPath to receive row events.");
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

    private SpacetimeClient? ResolveSelectedClient()
    {
        var clientPath = FormatClientPath(ClientPath);
        if (!string.IsNullOrWhiteSpace(clientPath))
        {
            var clientFromPath = GetNodeOrNull<SpacetimeClient>(ClientPath);
            if (clientFromPath != null)
                return clientFromPath;
        }

        if (IsDefaultClientPath(ClientPath) &&
            SpacetimeClient.TryGetClient(SpacetimeClient.DefaultConnectionId, out var defaultClient))
        {
            return defaultClient;
        }

        return null;
    }

    private static bool IsDefaultClientPath(NodePath nodePath) =>
        string.Equals(
            FormatClientPath(nodePath),
            FormatClientPath(DefaultClientPath),
            StringComparison.Ordinal);

    private static string FormatClientPath(NodePath nodePath) => nodePath.ToString();
}

#if TOOLS
using Godot;
using GodotSpacetime.Editor.Codegen;
using GodotSpacetime.Editor.Compatibility;
using GodotSpacetime.Editor.Status;

namespace GodotSpacetime;

[Tool]
public partial class GodotSpacetimePlugin : EditorPlugin
{
    private const string CodegenPanelScenePath = "res://addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn";
    private const string CompatPanelScenePath = "res://addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn";
    private const string StatusPanelScenePath = "res://addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.tscn";
    private CodegenValidationPanel? _codegenPanel;
    private CompatibilityPanel? _compatPanel;
    private ConnectionAuthStatusPanel? _statusPanel;

    public override void _EnterTree()
    {
        AddCustomType(
            "RowReceiver",
            "Node",
            GD.Load<Script>("res://addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs"),
            GD.Load<Texture2D>("res://addons/godot_spacetime/assets/row_receiver_icon.svg")
        );

        var panelScene = GD.Load<PackedScene>(CodegenPanelScenePath);
        if (panelScene != null)
        {
            var panelRoot = panelScene.Instantiate();
            _codegenPanel = panelRoot as CodegenValidationPanel;
            if (_codegenPanel == null)
            {
                panelRoot.QueueFree();
                GD.PushError($"Code generation panel scene root must be {nameof(CodegenValidationPanel)}.");
            }
            else
            {
#pragma warning disable CS0618
                AddControlToBottomPanel(_codegenPanel, "Spacetime Codegen");
#pragma warning restore CS0618
            }
        }
        else
        {
            GD.PushError($"Failed to load code generation panel scene: {CodegenPanelScenePath}");
        }

        var compatScene = GD.Load<PackedScene>(CompatPanelScenePath);
        if (compatScene != null)
        {
            var compatRoot = compatScene.Instantiate();
            _compatPanel = compatRoot as CompatibilityPanel;
            if (_compatPanel == null)
            {
                compatRoot.QueueFree();
                GD.PushError($"Compatibility panel scene root must be {nameof(CompatibilityPanel)}.");
            }
            else
            {
#pragma warning disable CS0618
                AddControlToBottomPanel(_compatPanel, "Spacetime Compat");
#pragma warning restore CS0618
            }
        }
        else
        {
            GD.PushError($"Failed to load compatibility panel scene: {CompatPanelScenePath}");
        }

        var statusScene = GD.Load<PackedScene>(StatusPanelScenePath);
        if (statusScene != null)
        {
            var statusRoot = statusScene.Instantiate();
            _statusPanel = statusRoot as ConnectionAuthStatusPanel;
            if (_statusPanel == null)
            {
                statusRoot.QueueFree();
                GD.PushError($"Status panel scene root must be {nameof(ConnectionAuthStatusPanel)}.");
            }
            else
            {
#pragma warning disable CS0618
                AddControlToBottomPanel(_statusPanel, "Spacetime Status");
#pragma warning restore CS0618
            }
        }
        else
        {
            GD.PushError($"Failed to load status panel scene: {StatusPanelScenePath}");
        }

        GD.Print("Godot Spacetime plugin enabled.");
    }

    public override void _ExitTree()
    {
        if (_statusPanel != null)
        {
#pragma warning disable CS0618
            RemoveControlFromBottomPanel(_statusPanel);
#pragma warning restore CS0618
            _statusPanel.QueueFree();
            _statusPanel = null;
        }

        if (_compatPanel != null)
        {
#pragma warning disable CS0618
            RemoveControlFromBottomPanel(_compatPanel);
#pragma warning restore CS0618
            _compatPanel.QueueFree();
            _compatPanel = null;
        }

        if (_codegenPanel != null)
        {
#pragma warning disable CS0618
            RemoveControlFromBottomPanel(_codegenPanel);
#pragma warning restore CS0618
            _codegenPanel.QueueFree();
            _codegenPanel = null;
        }
        RemoveCustomType("RowReceiver");
        GD.Print("Godot Spacetime plugin disabled.");
    }
}
#endif

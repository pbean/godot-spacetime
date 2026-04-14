#if TOOLS
using Godot;
using GodotSpacetime.Editor.Codegen;
using GodotSpacetime.Editor.Compatibility;

namespace GodotSpacetime;

[Tool]
public partial class GodotSpacetimePlugin : EditorPlugin
{
    private const string CodegenPanelScenePath = "res://addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn";
    private const string CompatPanelScenePath = "res://addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn";
    private CodegenValidationPanel? _codegenPanel;
    private CompatibilityPanel? _compatPanel;

    public override void _EnterTree()
    {
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

        GD.Print("Godot Spacetime plugin enabled.");
    }

    public override void _ExitTree()
    {
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
        GD.Print("Godot Spacetime plugin disabled.");
    }
}
#endif

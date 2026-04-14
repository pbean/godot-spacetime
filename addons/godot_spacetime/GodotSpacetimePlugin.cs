#if TOOLS
using Godot;
using GodotSpacetime.Editor.Codegen;

namespace GodotSpacetime;

[Tool]
public partial class GodotSpacetimePlugin : EditorPlugin
{
    private const string CodegenPanelScenePath = "res://addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn";
    private CodegenValidationPanel? _codegenPanel;

    public override void _EnterTree()
    {
        var panelScene = GD.Load<PackedScene>(CodegenPanelScenePath);
        if (panelScene == null)
        {
            GD.PushError($"Failed to load code generation panel scene: {CodegenPanelScenePath}");
            GD.Print("Godot Spacetime plugin enabled.");
            return;
        }

        var panelRoot = panelScene.Instantiate();
        _codegenPanel = panelRoot as CodegenValidationPanel;
        if (_codegenPanel == null)
        {
            panelRoot.QueueFree();
            GD.PushError($"Code generation panel scene root must be {nameof(CodegenValidationPanel)}.");
            GD.Print("Godot Spacetime plugin enabled.");
            return;
        }

#pragma warning disable CS0618
        AddControlToBottomPanel(_codegenPanel, "Spacetime Codegen");
#pragma warning restore CS0618
        GD.Print("Godot Spacetime plugin enabled.");
    }

    public override void _ExitTree()
    {
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

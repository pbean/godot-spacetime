#if TOOLS
using Godot;

namespace GodotSpacetime;

[Tool]
public partial class GodotSpacetimePlugin : EditorPlugin
{
    public override void _EnterTree()
    {
        GD.Print("Godot Spacetime plugin enabled.");
    }

    public override void _ExitTree()
    {
        GD.Print("Godot Spacetime plugin disabled.");
    }
}
#endif

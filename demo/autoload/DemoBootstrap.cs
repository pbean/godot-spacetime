using Godot;

namespace GodotSpacetime.Demo;

public partial class DemoBootstrap : Node
{
    public override void _Ready()
    {
        GD.Print("[Demo] Bootstrap ready — godot-spacetime addon enabled");
    }
}

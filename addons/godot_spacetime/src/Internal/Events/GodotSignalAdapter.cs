using System;
using Godot;

namespace GodotSpacetime.Runtime.Events;

internal sealed class GodotSignalAdapter
{
    private readonly Node _owner;

    public GodotSignalAdapter(Node owner)
    {
        _owner = owner;
    }

    public void Dispatch(Action action)
    {
        if (!GodotObject.IsInstanceValid(_owner))
            return;

        Callable.From(action).CallDeferred();
    }
}

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

    /// <summary>
    /// Marshals <paramref name="action"/> onto the main thread via a deferred call on the owning
    /// client Node. The action is delivered at most once, and only while the owning Node remains a
    /// valid instance in the scene tree. If the Node leaves the tree (or is freed) mid-flight, the
    /// deferred call is dropped by design — there is no exit-tree completion registry; this is the
    /// documented main-thread-while-in-tree caveat (see docs/runtime-boundaries.md).
    /// </summary>
    public void Dispatch(Action action)
    {
        if (!GodotObject.IsInstanceValid(_owner))
            return;

        Callable.From(action).CallDeferred();
    }
}

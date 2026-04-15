using Godot;
using GodotSpacetime;
using GodotSpacetime.Connection;

namespace GodotSpacetime.Demo;

/// <summary>Demo scene for first-connection baseline. Extends for auth and subscription in Stories 5.2 and 5.3.</summary>
public partial class DemoMain : Node
{
    private SpacetimeClient? _client;

    public override void _Ready()
    {
        _client = GetNode<SpacetimeClient>("/root/SpacetimeClient");
        _client.ConnectionStateChanged -= OnConnectionStateChanged;
        _client.ConnectionStateChanged += OnConnectionStateChanged;
        _client.Connect();
    }

    public override void _ExitTree()
    {
        if (_client != null)
            _client.ConnectionStateChanged -= OnConnectionStateChanged;
    }

    private void OnConnectionStateChanged(ConnectionStatus status)
    {
        GD.Print($"[Demo] Connection state: {status.Description}");
    }
}

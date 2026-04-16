using Godot;

namespace GodotSpacetime.Connection;

/// <summary>
/// Pull-based connection telemetry exposed from <see cref="GodotSpacetime.SpacetimeClient"/>.
/// The same instance is reused for the lifetime of the client and reset in place when a
/// session disconnects or reconnects.
/// </summary>
public partial class ConnectionTelemetryStats : RefCounted
{
    public long MessagesSent { get; internal set; }

    public long MessagesReceived { get; internal set; }

    public long BytesSent { get; internal set; }

    public long BytesReceived { get; internal set; }

    public double ConnectionUptimeSeconds { get; internal set; }

    public double LastReducerRoundTripMilliseconds { get; internal set; }
}

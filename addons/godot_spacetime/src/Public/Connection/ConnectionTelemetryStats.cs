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

    /// <summary>
    /// Rolling 1-second rate derived from <see cref="MessagesReceived"/>.
    /// Updates on-read when at least 1 second has elapsed since the last baseline;
    /// two reads inside the same 1-second bucket return the same value.
    /// Resets to <c>0.0</c> on disconnect/reconnect.
    /// </summary>
    public double MessagesReceivedPerSecond { get; internal set; }

    /// <summary>
    /// Rolling 1-second rate derived from <see cref="MessagesSent"/>.
    /// Updates on-read when at least 1 second has elapsed since the last baseline;
    /// two reads inside the same 1-second bucket return the same value.
    /// Resets to <c>0.0</c> on disconnect/reconnect.
    /// </summary>
    public double MessagesSentPerSecond { get; internal set; }

    /// <summary>
    /// Rolling 1-second rate derived from <see cref="BytesReceived"/>.
    /// Updates on-read when at least 1 second has elapsed since the last baseline;
    /// two reads inside the same 1-second bucket return the same value.
    /// Resets to <c>0.0</c> on disconnect/reconnect.
    /// </summary>
    public double BytesReceivedPerSecond { get; internal set; }

    /// <summary>
    /// Rolling 1-second rate derived from <see cref="BytesSent"/>.
    /// Updates on-read when at least 1 second has elapsed since the last baseline;
    /// two reads inside the same 1-second bucket return the same value.
    /// Resets to <c>0.0</c> on disconnect/reconnect.
    /// </summary>
    public double BytesSentPerSecond { get; internal set; }
}

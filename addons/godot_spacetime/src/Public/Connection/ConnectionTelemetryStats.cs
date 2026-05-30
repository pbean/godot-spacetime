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

    /// <summary>
    /// Per-category latency, sample count, and pending-request telemetry for client-driven
    /// reducer calls. Populated on the pinned 2.1.0 client after real reducer traffic.
    /// </summary>
    public CategoryTelemetry Reducers { get; } = new();

    /// <summary>
    /// Per-category telemetry for procedure calls.
    /// </summary>
    public CategoryTelemetry Procedures { get; } = new();

    /// <summary>
    /// Per-category telemetry for subscription requests. Populated on the pinned 2.1.0 client
    /// after real subscription traffic.
    /// </summary>
    public CategoryTelemetry Subscriptions { get; } = new();

    /// <summary>
    /// Per-category telemetry for one-off queries. Populated on the pinned 2.1.0 client after
    /// real one-off query traffic.
    /// </summary>
    public CategoryTelemetry OneOffQueries { get; } = new();

    /// <summary>
    /// Aggregate "all reducers" tracker. Empirically expected-empty on the pinned 2.1.0
    /// client (all six scalars stay <c>0.0</c>/<c>0</c>); see <c>docs/connection.md</c>.
    /// </summary>
    public CategoryTelemetry AllReducers { get; } = new();

    /// <summary>
    /// Aggregate message-parse-queue tracker. Populated on the pinned 2.1.0 client from inbound
    /// message traffic — the initial subscription/transaction messages, and again on the reconnect
    /// handshake (measured live lane); see <c>docs/connection.md</c>.
    /// </summary>
    public CategoryTelemetry ParseMessageQueue { get; } = new();

    /// <summary>
    /// Per-message parse latency tracker. Populated on the pinned 2.1.0 client as inbound
    /// messages are parsed.
    /// </summary>
    public CategoryTelemetry ParseMessage { get; } = new();

    /// <summary>
    /// Aggregate apply-message-queue tracker. Populated on the pinned 2.1.0 client from inbound
    /// message traffic — the initial subscription/transaction messages, and again on the reconnect
    /// handshake (measured live lane); see <c>docs/connection.md</c>.
    /// </summary>
    public CategoryTelemetry ApplyMessageQueue { get; } = new();

    /// <summary>
    /// Per-message apply latency tracker. Populated on the pinned 2.1.0 client as inbound
    /// messages are applied to the cache.
    /// </summary>
    public CategoryTelemetry ApplyMessage { get; } = new();
}

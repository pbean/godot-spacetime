using Godot;

namespace GodotSpacetime.Connection;

/// <summary>
/// Per-category connection telemetry surfaced from <see cref="ConnectionTelemetryStats"/>.
/// One instance maps to a single SpacetimeDB request/message tracker (e.g. reducers,
/// subscriptions, message parse/apply). The same instance is reused for the lifetime of
/// the owning <see cref="ConnectionTelemetryStats"/> and reset in place when a session
/// disconnects or reconnects.
///
/// This type stays runtime-neutral: it carries only plain <c>double</c>/<c>long</c> scalars
/// that the .NET isolation zone flattens from the SDK trackers before they cross the public
/// boundary. No SDK transport types appear here.
/// </summary>
public partial class CategoryTelemetry : RefCounted
{
    /// <summary>
    /// Minimum latency (milliseconds) observed in the rolling 1-second window.
    /// Reads <c>0.0</c> on an idle/empty window or while disconnected — the SDK tracker
    /// returns <c>null</c> for that window and the flatten layer coalesces it to <c>0.0</c>,
    /// matching the <see cref="ConnectionTelemetryStats.LastReducerRoundTripMilliseconds"/>
    /// reset convention.
    /// </summary>
    public double MinMs { get; internal set; }

    /// <summary>
    /// Maximum latency (milliseconds) observed in the rolling 1-second window.
    /// Reads <c>0.0</c> on an idle/empty window or while disconnected (see <see cref="MinMs"/>).
    /// </summary>
    public double MaxMs { get; internal set; }

    /// <summary>
    /// All-time minimum latency (milliseconds) observed since the connection opened
    /// (window-independent). Reads <c>0.0</c> before any sample is recorded or while
    /// disconnected — the SDK exposes <c>null</c> until the first sample.
    /// </summary>
    public double AllTimeMinMs { get; internal set; }

    /// <summary>
    /// All-time maximum latency (milliseconds) observed since the connection opened
    /// (window-independent). Reads <c>0.0</c> before any sample is recorded or while
    /// disconnected (see <see cref="AllTimeMinMs"/>).
    /// </summary>
    public double AllTimeMaxMs { get; internal set; }

    /// <summary>
    /// Cumulative number of completed requests/messages this category has recorded since
    /// the active connection opened (count). Reads <c>0</c> while disconnected.
    /// </summary>
    public long SampleCount { get; internal set; }

    /// <summary>
    /// Number of requests currently awaiting a response for this category (in-flight count).
    /// Reads <c>0</c> while disconnected or when nothing is in flight.
    /// </summary>
    public long PendingRequests { get; internal set; }
}

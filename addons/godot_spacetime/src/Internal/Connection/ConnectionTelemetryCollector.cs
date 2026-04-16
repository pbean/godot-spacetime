using System;
using GodotSpacetime.Connection;

namespace GodotSpacetime.Runtime.Connection;

internal sealed class ConnectionTelemetryCollector
{
    internal const string SdkClientMessageBsatnSource = "sdk_client_message_bsatn";

    private readonly ConnectionTelemetryStats _stats = new();
    private DateTimeOffset? _connectedAtUtc;

    internal ConnectionTelemetryStats CurrentTelemetry
    {
        get
        {
            RefreshUptime();
            return _stats;
        }
    }

    internal string BytesSentSource { get; private set; } = string.Empty;

    internal bool HasProvenOutboundBytes =>
        string.Equals(BytesSentSource, SdkClientMessageBsatnSource, StringComparison.Ordinal);

    internal void StartSession()
    {
        Reset();
        _connectedAtUtc = DateTimeOffset.UtcNow;
        RefreshUptime();
    }

    internal void Reset()
    {
        _connectedAtUtc = null;
        BytesSentSource = string.Empty;
        _stats.MessagesSent = 0;
        _stats.MessagesReceived = 0;
        _stats.BytesSent = 0;
        _stats.BytesReceived = 0;
        _stats.ConnectionUptimeSeconds = 0;
        _stats.LastReducerRoundTripMilliseconds = 0;
    }

    internal void RecordInboundMessage(int byteCount)
    {
        if (byteCount < 0)
            return;

        _stats.MessagesReceived += 1;
        _stats.BytesReceived += byteCount;
    }

    internal void RecordOutboundMessage(long byteCount)
    {
        if (byteCount < 0)
            return;

        _stats.MessagesSent += 1;
        _stats.BytesSent += byteCount;
        BytesSentSource = SdkClientMessageBsatnSource;
    }

    internal void UpdateTrackerCounts(long messagesSent, long messagesReceived)
    {
        if (messagesSent > _stats.MessagesSent)
            _stats.MessagesSent = messagesSent;

        if (messagesReceived > _stats.MessagesReceived)
            _stats.MessagesReceived = messagesReceived;
    }

    internal void RecordReducerRoundTrip(DateTimeOffset calledAt, DateTimeOffset finishedAt)
    {
        var elapsed = finishedAt - calledAt;
        _stats.LastReducerRoundTripMilliseconds = elapsed.TotalMilliseconds < 0
            ? 0
            : elapsed.TotalMilliseconds;
    }

    private void RefreshUptime()
    {
        _stats.ConnectionUptimeSeconds = _connectedAtUtc.HasValue
            ? Math.Max(0, (DateTimeOffset.UtcNow - _connectedAtUtc.Value).TotalSeconds)
            : 0;
    }
}

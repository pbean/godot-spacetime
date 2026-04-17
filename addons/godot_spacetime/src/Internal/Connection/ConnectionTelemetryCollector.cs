using System;
using GodotSpacetime.Connection;

namespace GodotSpacetime.Runtime.Connection;

internal sealed class ConnectionTelemetryCollector
{
    internal const string SdkClientMessageBsatnSource = "sdk_client_message_bsatn";

    private readonly ConnectionTelemetryStats _stats = new();
    private DateTimeOffset? _connectedAtUtc;
    private DateTimeOffset? _rateBaselineUtc;
    private long _rateBaselineMessagesReceived;
    private long _rateBaselineMessagesSent;
    private long _rateBaselineBytesReceived;
    private long _rateBaselineBytesSent;

    internal ConnectionTelemetryStats CurrentTelemetry
    {
        get
        {
            RefreshUptime();
            RefreshRates();
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
        _rateBaselineUtc = _connectedAtUtc;
        RefreshUptime();
    }

    internal void Reset()
    {
        _connectedAtUtc = null;
        _rateBaselineUtc = null;
        _rateBaselineMessagesReceived = 0;
        _rateBaselineMessagesSent = 0;
        _rateBaselineBytesReceived = 0;
        _rateBaselineBytesSent = 0;
        BytesSentSource = string.Empty;
        _stats.MessagesSent = 0;
        _stats.MessagesReceived = 0;
        _stats.BytesSent = 0;
        _stats.BytesReceived = 0;
        _stats.ConnectionUptimeSeconds = 0;
        _stats.LastReducerRoundTripMilliseconds = 0;
        _stats.MessagesReceivedPerSecond = 0;
        _stats.MessagesSentPerSecond = 0;
        _stats.BytesReceivedPerSecond = 0;
        _stats.BytesSentPerSecond = 0;
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

    private void RefreshRates()
    {
        if (!_rateBaselineUtc.HasValue)
            return;

        var elapsedSeconds = (DateTimeOffset.UtcNow - _rateBaselineUtc.Value).TotalSeconds;
        if (elapsedSeconds < 1.0)
            return;

        _stats.MessagesReceivedPerSecond = Math.Max(0,
            (_stats.MessagesReceived - _rateBaselineMessagesReceived) / elapsedSeconds);
        _stats.MessagesSentPerSecond = Math.Max(0,
            (_stats.MessagesSent - _rateBaselineMessagesSent) / elapsedSeconds);
        _stats.BytesReceivedPerSecond = Math.Max(0,
            (_stats.BytesReceived - _rateBaselineBytesReceived) / elapsedSeconds);
        _stats.BytesSentPerSecond = Math.Max(0,
            (_stats.BytesSent - _rateBaselineBytesSent) / elapsedSeconds);

        _rateBaselineUtc = DateTimeOffset.UtcNow;
        _rateBaselineMessagesReceived = _stats.MessagesReceived;
        _rateBaselineMessagesSent = _stats.MessagesSent;
        _rateBaselineBytesReceived = _stats.BytesReceived;
        _rateBaselineBytesSent = _stats.BytesSent;
    }
}

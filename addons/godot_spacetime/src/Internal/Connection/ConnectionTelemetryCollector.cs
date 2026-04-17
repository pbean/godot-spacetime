using System;
using System.Diagnostics;
using GodotSpacetime.Connection;

namespace GodotSpacetime.Runtime.Connection;

internal sealed class ConnectionTelemetryCollector
{
    internal const string SdkClientMessageBsatnSource = "sdk_client_message_bsatn";

    private readonly object _gate = new();
    private readonly ConnectionTelemetryStats _stats = new();
    private long _activeSessionId;
    private long? _connectedAtTimestamp;
    private long? _rateBaselineTimestamp;
    private long _rateBaselineMessagesReceived;
    private long _rateBaselineMessagesSent;
    private long _rateBaselineBytesReceived;
    private long _rateBaselineBytesSent;
    private long _trackerBaselineMessagesSent;
    private long _trackerBaselineMessagesReceived;
    private bool _trackerBaselineArmed;
    private string _bytesSentSource = string.Empty;

    internal ConnectionTelemetryStats CurrentTelemetry
    {
        get
        {
            lock (_gate)
            {
                var now = Stopwatch.GetTimestamp();
                RefreshUptime(now);
                RefreshRates(now);
                return _stats;
            }
        }
    }

    internal string BytesSentSource
    {
        get
        {
            lock (_gate)
                return _bytesSentSource;
        }
    }

    internal bool HasProvenOutboundBytes
    {
        get
        {
            lock (_gate)
            {
                return string.Equals(_bytesSentSource, SdkClientMessageBsatnSource, StringComparison.Ordinal);
            }
        }
    }

    internal void StartSession(long sessionId)
    {
        if (sessionId <= 0)
            throw new ArgumentOutOfRangeException(nameof(sessionId), "Telemetry session ids must be positive.");

        lock (_gate)
        {
            ResetNoLock();
            var now = Stopwatch.GetTimestamp();
            _activeSessionId = sessionId;
            _connectedAtTimestamp = now;
            _rateBaselineTimestamp = now;
            RefreshUptime(now);
        }
    }

    internal void Reset()
    {
        lock (_gate)
            ResetNoLock();
    }

    internal void RecordInboundMessage(long sessionId, int byteCount)
    {
        if (byteCount < 0)
            return;

        lock (_gate)
        {
            if (!IsActiveSession(sessionId))
                return;

            _stats.MessagesReceived += 1;
            _stats.BytesReceived += byteCount;
        }
    }

    internal void RecordOutboundMessage(long sessionId, long byteCount)
    {
        if (byteCount < 0)
            return;

        lock (_gate)
        {
            if (!IsActiveSession(sessionId))
                return;

            _stats.MessagesSent += 1;
            _stats.BytesSent += byteCount;
            _bytesSentSource = SdkClientMessageBsatnSource;
        }
    }

    /// <summary>
    /// Arms the tracker baseline for the currently active session. Must be called at most once per
    /// session, immediately after <see cref="StartSession"/> while the session is still armed. A
    /// second call silently overwrites the baseline and will make subsequent
    /// <see cref="SyncTrackerCounts"/> calls treat prior traffic as new (clamped to zero by the
    /// Math.Max subtraction). The single-call invariant is structurally enforced by the
    /// StartSession→InitializeTrackerBaseline ordering in the connection service.
    /// </summary>
    internal void InitializeTrackerBaseline(long sessionId, long messagesSent, long messagesReceived)
    {
        lock (_gate)
        {
            if (!IsActiveSession(sessionId))
                return;

            _trackerBaselineMessagesSent = Math.Max(0, messagesSent);
            _trackerBaselineMessagesReceived = Math.Max(0, messagesReceived);
            _trackerBaselineArmed = true;
        }
    }

    internal void SyncTrackerCounts(long sessionId, long messagesSent, long messagesReceived)
    {
        lock (_gate)
        {
            if (!IsActiveSession(sessionId) || !_trackerBaselineArmed)
                return;

            var sessionMessagesSent = Math.Max(0L, messagesSent - _trackerBaselineMessagesSent);
            var sessionMessagesReceived = Math.Max(0L, messagesReceived - _trackerBaselineMessagesReceived);

            if (sessionMessagesSent > _stats.MessagesSent)
                _stats.MessagesSent = sessionMessagesSent;

            if (sessionMessagesReceived > _stats.MessagesReceived)
                _stats.MessagesReceived = sessionMessagesReceived;
        }
    }

    internal void RecordReducerRoundTrip(long sessionId, DateTimeOffset calledAt, DateTimeOffset finishedAt)
    {
        lock (_gate)
        {
            if (!IsActiveSession(sessionId))
                return;

            var elapsed = finishedAt - calledAt;
            _stats.LastReducerRoundTripMilliseconds = elapsed.TotalMilliseconds < 0
                ? 0
                : elapsed.TotalMilliseconds;
        }
    }

    private void ResetNoLock()
    {
        _activeSessionId = 0;
        _connectedAtTimestamp = null;
        _rateBaselineTimestamp = null;
        _rateBaselineMessagesReceived = 0;
        _rateBaselineMessagesSent = 0;
        _rateBaselineBytesReceived = 0;
        _rateBaselineBytesSent = 0;
        _trackerBaselineMessagesSent = 0;
        _trackerBaselineMessagesReceived = 0;
        _trackerBaselineArmed = false;
        _bytesSentSource = string.Empty;
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

    private void RefreshUptime(long now)
    {
        _stats.ConnectionUptimeSeconds = _connectedAtTimestamp.HasValue
            ? GetElapsedSeconds(_connectedAtTimestamp.Value, now)
            : 0;
    }

    private void RefreshRates(long now)
    {
        if (!_rateBaselineTimestamp.HasValue)
            return;

        var elapsedSeconds = GetElapsedSeconds(_rateBaselineTimestamp.Value, now);
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

        _rateBaselineTimestamp = now;
        _rateBaselineMessagesReceived = _stats.MessagesReceived;
        _rateBaselineMessagesSent = _stats.MessagesSent;
        _rateBaselineBytesReceived = _stats.BytesReceived;
        _rateBaselineBytesSent = _stats.BytesSent;
    }

    private bool IsActiveSession(long sessionId) =>
        sessionId > 0 && sessionId == _activeSessionId;

    private static double GetElapsedSeconds(long startTimestamp, long endTimestamp)
    {
        return Math.Max(0, (endTimestamp - startTimestamp) / (double)Stopwatch.Frequency);
    }
}

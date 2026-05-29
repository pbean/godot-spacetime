using System;

namespace GodotSpacetime.Runtime.Connection;

internal sealed class ReconnectPolicy
{
    private int _attemptsUsed;

    /// <summary>
    /// Creates a reconnect policy with the given retry budget and initial backoff.
    /// The backoff grows geometrically with a fixed 2× factor so the full schedule is
    /// <c>initialBackoffSeconds * 2^(attempt-1)</c> seconds.
    /// </summary>
    /// <param name="maxAttempts">Retry budget; must be at least <c>1</c>.</param>
    /// <param name="initialBackoffSeconds">First-attempt backoff; must be greater than zero.</param>
    public ReconnectPolicy(int maxAttempts = 3, double initialBackoffSeconds = 1.0)
    {
        if (maxAttempts < 1)
            throw new ArgumentOutOfRangeException(nameof(maxAttempts), "ReconnectPolicy requires at least one attempt.");

        if (initialBackoffSeconds <= 0 || double.IsNaN(initialBackoffSeconds) || double.IsInfinity(initialBackoffSeconds))
            throw new ArgumentOutOfRangeException(nameof(initialBackoffSeconds), "ReconnectPolicy requires positive initial backoff.");

        MaxAttempts = maxAttempts;
        InitialBackoffSeconds = initialBackoffSeconds;
    }

    public int MaxAttempts { get; }

    public double InitialBackoffSeconds { get; }

    public int AttemptsUsed => _attemptsUsed;

    public void Reset()
    {
        _attemptsUsed = 0;
    }

    public bool TryBeginRetry(out int attemptNumber, out TimeSpan delay)
    {
        if (_attemptsUsed >= MaxAttempts)
        {
            attemptNumber = _attemptsUsed;
            delay = TimeSpan.Zero;
            return false;
        }

        _attemptsUsed++;
        attemptNumber = _attemptsUsed;

        // Internal overflow safety guard — NOT a user-tunable per-attempt cap. Under extreme
        // operator tunings the geometric backoff can grow to Infinity or to a finite value above
        // TimeSpan's representable range, and TimeSpan.FromSeconds would throw OverflowException on
        // the disconnect-callback path before any state transition runs. The 24h ceiling sits far
        // above any intended schedule and is inert below 86400s, so it never alters real backoffs.
        // Math.Min returns the right-hand operand for Infinity and for any value above the ceiling,
        // clamping both the Infinity and the finite-but-too-large cases.
        double rawDelaySeconds = InitialBackoffSeconds * Math.Pow(2, attemptNumber - 1);
        double delaySeconds = Math.Min(rawDelaySeconds, TimeSpan.FromHours(24).TotalSeconds);
        delay = TimeSpan.FromSeconds(delaySeconds);
        return true;
    }
}

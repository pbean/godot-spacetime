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
        delay = TimeSpan.FromSeconds(InitialBackoffSeconds * Math.Pow(2, attemptNumber - 1));
        return true;
    }
}

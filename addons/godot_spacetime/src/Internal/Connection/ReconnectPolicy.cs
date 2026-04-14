using System;

namespace GodotSpacetime.Runtime.Connection;

internal sealed class ReconnectPolicy
{
    private int _attemptsUsed;

    public ReconnectPolicy(int maxAttempts = 3)
    {
        if (maxAttempts < 1)
            throw new ArgumentOutOfRangeException(nameof(maxAttempts), "ReconnectPolicy requires at least one attempt.");

        MaxAttempts = maxAttempts;
    }

    public int MaxAttempts { get; }

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
        delay = TimeSpan.FromSeconds(Math.Pow(2, attemptNumber - 1));
        return true;
    }
}

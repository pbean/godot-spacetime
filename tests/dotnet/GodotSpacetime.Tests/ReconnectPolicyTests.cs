using System;
using GodotSpacetime.Runtime.Connection;
using Xunit;

namespace GodotSpacetime.Tests;

/// <summary>
/// Behavioral coverage for <see cref="ReconnectPolicy"/>, source-linked into this assembly
/// (see <c>GodotSpacetime.Tests.csproj</c>). Each fact/theory maps to a row of the spec's
/// I/O &amp; Edge-Case Matrix, including the 24h overflow-clamp safety guard in
/// <see cref="ReconnectPolicy.TryBeginRetry"/>.
/// </summary>
public sealed class ReconnectPolicyTests
{
    [Fact]
    public void Default_Schedule_Yields_1s_2s_4s_Across_Three_Attempts()
    {
        var policy = new ReconnectPolicy();

        Assert.True(policy.TryBeginRetry(out var attempt1, out var delay1));
        Assert.Equal(1, attempt1);
        Assert.Equal(TimeSpan.FromSeconds(1), delay1);

        Assert.True(policy.TryBeginRetry(out var attempt2, out var delay2));
        Assert.Equal(2, attempt2);
        Assert.Equal(TimeSpan.FromSeconds(2), delay2);

        Assert.True(policy.TryBeginRetry(out var attempt3, out var delay3));
        Assert.Equal(3, attempt3);
        Assert.Equal(TimeSpan.FromSeconds(4), delay3);
    }

    [Fact]
    public void Fourth_Retry_After_Exhausting_Default_Budget_Returns_False()
    {
        var policy = new ReconnectPolicy();

        // Burn the 3-attempt budget.
        policy.TryBeginRetry(out _, out _);
        policy.TryBeginRetry(out _, out _);
        policy.TryBeginRetry(out _, out _);

        Assert.False(policy.TryBeginRetry(out var attemptNumber, out var delay));
        Assert.Equal(TimeSpan.Zero, delay);
        // AttemptsUsed is unchanged by the rejected attempt.
        Assert.Equal(policy.AttemptsUsed, attemptNumber);
        Assert.Equal(3, policy.AttemptsUsed);
    }

    [Fact]
    public void Tuned_Policy_Yields_Geometric_Schedule_From_Custom_Initial_Backoff()
    {
        var policy = new ReconnectPolicy(maxAttempts: 5, initialBackoffSeconds: 0.5);

        double[] expectedSeconds = { 0.5, 1.0, 2.0, 4.0, 8.0 };
        foreach (var expected in expectedSeconds)
        {
            Assert.True(policy.TryBeginRetry(out _, out var delay));
            Assert.Equal(TimeSpan.FromSeconds(expected), delay);
        }
    }

    [Fact]
    public void Reset_Restores_Budget_And_Schedule_Resumes_From_Attempt_One()
    {
        var policy = new ReconnectPolicy();

        // Exhaust the budget.
        policy.TryBeginRetry(out _, out _);
        policy.TryBeginRetry(out _, out _);
        policy.TryBeginRetry(out _, out _);
        Assert.False(policy.TryBeginRetry(out _, out _));

        policy.Reset();
        Assert.Equal(0, policy.AttemptsUsed);

        Assert.True(policy.TryBeginRetry(out var attemptNumber, out var delay));
        Assert.Equal(1, attemptNumber);
        Assert.Equal(TimeSpan.FromSeconds(1), delay);
    }

    [Fact]
    public void Extreme_Tuning_That_Overflows_To_Infinity_Clamps_To_24h_Without_Throwing()
    {
        // 1.0 * 2^(attempt-1) overflows the double range to Infinity long before attempt 2048,
        // and TimeSpan.FromSeconds(Infinity) would throw OverflowException without the clamp.
        var policy = new ReconnectPolicy(maxAttempts: 2048, initialBackoffSeconds: 1.0);

        TimeSpan lastDelay = TimeSpan.Zero;
        bool sawClamp = false;
        for (var i = 0; i < 2048; i++)
        {
            Assert.True(policy.TryBeginRetry(out _, out var delay));
            lastDelay = delay;
            if (delay == TimeSpan.FromHours(24))
                sawClamp = true;
        }

        // Late attempts overflow to Infinity; the clamp pins them at the 24h ceiling.
        Assert.True(sawClamp);
        Assert.Equal(TimeSpan.FromHours(24), lastDelay);
    }

    [Fact]
    public void Extreme_Tuning_That_Is_Finite_But_Too_Large_Clamps_To_24h_Without_Throwing()
    {
        // initial * 2^(attempt-1) stays finite here (well below double.MaxValue) but vastly
        // exceeds TimeSpan.MaxValue.TotalSeconds (~9.22e11), which TimeSpan.FromSeconds would
        // reject. The clamp must absorb the finite-but-too-large case too.
        var policy = new ReconnectPolicy(maxAttempts: 1, initialBackoffSeconds: 1e30);

        Assert.True(policy.TryBeginRetry(out _, out var delay));
        Assert.Equal(TimeSpan.FromHours(24), delay);
    }

    [Fact]
    public void Default_Schedule_Is_Unaltered_By_The_Inert_Clamp()
    {
        // The clamp is inert below 86400s — the full default schedule must be byte-identical
        // to the pre-change geometric backoff.
        var policy = new ReconnectPolicy();

        policy.TryBeginRetry(out _, out var delay1);
        policy.TryBeginRetry(out _, out var delay2);
        policy.TryBeginRetry(out _, out var delay3);

        Assert.Equal(TimeSpan.FromSeconds(1), delay1);
        Assert.Equal(TimeSpan.FromSeconds(2), delay2);
        Assert.Equal(TimeSpan.FromSeconds(4), delay3);
        Assert.True(delay3 < TimeSpan.FromHours(24));
    }

    [Fact]
    public void Constructor_Rejects_MaxAttempts_Below_One()
    {
        var ex = Assert.Throws<ArgumentOutOfRangeException>(() => new ReconnectPolicy(maxAttempts: 0));

        Assert.Equal("maxAttempts", ex.ParamName);
    }

    [Theory]
    [InlineData(0.0)]
    [InlineData(-1.0)]
    [InlineData(double.NaN)]
    [InlineData(double.PositiveInfinity)]
    public void Constructor_Rejects_NonPositive_NaN_Or_Infinite_Initial_Backoff(double initialBackoffSeconds)
    {
        var ex = Assert.Throws<ArgumentOutOfRangeException>(
            () => new ReconnectPolicy(initialBackoffSeconds: initialBackoffSeconds));

        Assert.Equal("initialBackoffSeconds", ex.ParamName);
    }
}

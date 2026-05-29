using System;
using Xunit;

namespace GodotSpacetime.Tests;

/// <summary>
/// Invariant coverage for the Godot-free <see cref="Identity"/> struct, source-linked
/// into this assembly (see <c>GodotSpacetime.Tests.csproj</c>). Each fact/theory maps
/// to a row of the spec's I/O &amp; Edge-Case Matrix.
/// </summary>
public sealed class IdentityTests
{
    // Real 64-char hex constant and the matching 32-byte array for parity tests.
    private const string SampleHex = "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF";

    private static readonly byte[] SampleBytes =
    {
        0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF,
        0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF,
        0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF,
        0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF,
    };

    [Fact]
    public void FromHexString_And_FromBytes_Produce_Equal_Identities()
    {
        var fromHex = Identity.FromHexString(SampleHex);
        var fromBytes = Identity.FromBytes(SampleBytes);

        Assert.Equal(fromHex, fromBytes);
        Assert.True(fromHex == fromBytes);
        Assert.False(fromHex != fromBytes);
        Assert.Equal(fromHex.GetHashCode(), fromBytes.GetHashCode());
    }

    [Fact]
    public void FromHexString_UpperCases_LowerCase_Input()
    {
        var lower = SampleHex.ToLowerInvariant();

        var identity = Identity.FromHexString(lower);

        Assert.Equal(SampleHex, identity.ToString());
    }

    [Fact]
    public void FromHexString_UpperCases_MixedCase_Input()
    {
        // Mix the case explicitly so the assertion proves canonicalization, not echo.
        const string mixed = "0123456789abcdef0123456789ABCDEF0123456789aBcDeF0123456789ABCDEF";

        var identity = Identity.FromHexString(mixed);

        Assert.Equal(SampleHex, identity.ToString());
    }

    [Theory]
    [InlineData("0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDE")]   // 63 chars
    [InlineData("0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEFA")] // 65 chars
    public void FromHexString_Rejects_Wrong_Length_Without_Echoing_Input(string offending)
    {
        var ex = Assert.Throws<ArgumentException>(() => Identity.FromHexString(offending));

        Assert.DoesNotContain(offending, ex.Message);
    }

    [Theory]
    [InlineData("0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEg")] // trailing 'g'
    [InlineData("z123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF")] // leading 'z'
    public void FromHexString_Rejects_NonHex_Chars_Without_Echoing_Input(string offending)
    {
        var ex = Assert.Throws<ArgumentException>(() => Identity.FromHexString(offending));

        Assert.DoesNotContain(offending, ex.Message);
    }

    [Fact]
    public void FromHexString_Throws_ArgumentNullException_On_Null()
    {
        var ex = Assert.Throws<ArgumentNullException>(() => Identity.FromHexString(null!));

        Assert.Equal("hex", ex.ParamName);
    }

    [Theory]
    [InlineData(31)]
    [InlineData(33)]
    public void FromBytes_Rejects_Wrong_Byte_Count(int length)
    {
        var bytes = new byte[length];

        var ex = Assert.Throws<ArgumentException>(() => Identity.FromBytes(bytes));

        Assert.Equal("bytes", ex.ParamName);
    }

    [Fact]
    public void Default_Identity_Renders_64_Zeros()
    {
        var rendered = default(Identity).ToString();

        Assert.Equal(new string('0', 64), rendered);
    }

    [Fact]
    public void Equal_Identities_Are_Consistent_Across_Equality_Members()
    {
        var left = Identity.FromHexString(SampleHex);
        var right = Identity.FromBytes(SampleBytes);

        Assert.True(left.Equals(right));
        Assert.True(left == right);
        Assert.False(left != right);
        Assert.Equal(left.GetHashCode(), right.GetHashCode());
    }

    [Fact]
    public void Unequal_Identities_Are_Consistent_Across_Equality_Members()
    {
        var left = Identity.FromHexString(SampleHex);
        var right = Identity.FromHexString(
            "FEDCBA9876543210FEDCBA9876543210FEDCBA9876543210FEDCBA9876543210");

        Assert.False(left.Equals(right));
        Assert.False(left == right);
        Assert.True(left != right);
    }
}

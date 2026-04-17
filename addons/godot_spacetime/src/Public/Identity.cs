using System;

namespace GodotSpacetime;

/// <summary>
/// Server-assigned identity for a connected SpacetimeDB session.
/// Immutable 32-byte value rendered as the 64-character uppercase hex form
/// emitted by the supported runtime's own identity string.
/// </summary>
/// <remarks>
/// Obtain instances from <see cref="Connection.ConnectionOpenedEvent.IdentityValue"/>
/// or <see cref="SpacetimeClient.CurrentIdentity"/>. Construct manually from a hex
/// string via <see cref="FromHexString"/> or from raw bytes via <see cref="FromBytes"/>.
/// <see cref="ToString"/> on <c>default(Identity)</c> returns 64 <c>'0'</c> characters.
/// </remarks>
public readonly struct Identity : IEquatable<Identity>
{
    private const int HexLength = 64;
    private const string DefaultHex = "0000000000000000000000000000000000000000000000000000000000000000";

    private readonly string? _hex;

    private Identity(string hex) => _hex = hex;

    /// <summary>Creates an <see cref="Identity"/> from a 64-character hex string (case-insensitive).</summary>
    /// <exception cref="ArgumentNullException"><paramref name="hex"/> is <c>null</c>.</exception>
    /// <exception cref="ArgumentException">The input is not exactly 64 hexadecimal characters.</exception>
    public static Identity FromHexString(string hex)
    {
        if (hex is null)
            throw new ArgumentNullException(nameof(hex));
        if (hex.Length != HexLength || !IsAllHexChars(hex))
            throw new ArgumentException("expected 64 hex characters", nameof(hex));

        return new Identity(hex.ToUpperInvariant());
    }

    /// <summary>Creates an <see cref="Identity"/> from a 32-byte span.</summary>
    /// <exception cref="ArgumentException">The input is not exactly 32 bytes.</exception>
    public static Identity FromBytes(ReadOnlySpan<byte> bytes)
    {
        if (bytes.Length != HexLength / 2)
            throw new ArgumentException("expected 32 bytes", nameof(bytes));

        var buffer = new char[HexLength];
        for (var i = 0; i < bytes.Length; i++)
        {
            var b = bytes[i];
            buffer[i * 2] = HexDigit(b >> 4);
            buffer[i * 2 + 1] = HexDigit(b & 0xF);
        }

        return new Identity(new string(buffer));
    }

    /// <summary>Returns the canonical 64-character uppercase hex rendering.</summary>
    public override string ToString() => _hex ?? DefaultHex;

    public bool Equals(Identity other) =>
        string.Equals(ToString(), other.ToString(), StringComparison.Ordinal);

    public override bool Equals(object? obj) => obj is Identity other && Equals(other);

    public override int GetHashCode() => ToString().GetHashCode(StringComparison.Ordinal);

    public static bool operator ==(Identity left, Identity right) => left.Equals(right);

    public static bool operator !=(Identity left, Identity right) => !left.Equals(right);

    private static bool IsAllHexChars(string value)
    {
        foreach (var ch in value)
        {
            var isHex = (ch >= '0' && ch <= '9')
                || (ch >= 'a' && ch <= 'f')
                || (ch >= 'A' && ch <= 'F');
            if (!isHex)
                return false;
        }
        return true;
    }

    private static char HexDigit(int nibble) =>
        (char)(nibble < 10 ? '0' + nibble : 'A' + (nibble - 10));
}

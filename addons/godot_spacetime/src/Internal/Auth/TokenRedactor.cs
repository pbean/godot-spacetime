namespace GodotSpacetime.Runtime.Auth;

internal static class TokenRedactor
{
    public static string Redact(string? token)
    {
        if (string.IsNullOrEmpty(token))
            return "<no token>";

        if (token.Length <= 8)
            return "<redacted>";

        return $"{token[..4]}…<redacted>";
    }
}

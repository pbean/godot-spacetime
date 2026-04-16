namespace GodotSpacetime.Connection;

/// <summary>
/// The authentication phase of a <see cref="ConnectionStatus"/>.
/// Complements <see cref="ConnectionState"/> with auth-specific context.
/// </summary>
public enum ConnectionAuthState
{
    /// <summary>No authentication context. Anonymous connection, or a state with no auth flow in progress.</summary>
    None,

    /// <summary>Provided credentials were accepted by the server. The session is authenticated.</summary>
    TokenRestored,

    /// <summary>Provided credentials were rejected. The connection did not complete due to an authentication failure.</summary>
    AuthFailed,

    /// <summary>
    /// The connection failed while credentials were provided, but the cause could not be confirmed as
    /// an authentication rejection (e.g., network timeout, server offline). Check
    /// <see cref="ConnectionStatus.Description"/> for the underlying error detail.
    /// </summary>
    ConnectFailed,

    /// <summary>
    /// A previously stored token was rejected by the server.
    /// Clear the token store via <c>Settings.TokenStore?.ClearTokenAsync()</c> and reconnect to establish a new session.
    /// </summary>
    TokenExpired,
}

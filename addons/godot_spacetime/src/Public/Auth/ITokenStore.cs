using System.Threading.Tasks;

namespace GodotSpacetime.Auth;

/// <summary>
/// Abstraction for opt-in token persistence across sessions.
/// Implement this interface to provide your own storage backend
/// (file, OS keychain, platform service, etc.).
/// </summary>
public interface ITokenStore
{
    /// <summary>Retrieves the stored session token, or <c>null</c> if none is stored.</summary>
    Task<string?> GetTokenAsync();

    /// <summary>Persists the session token for future retrieval.</summary>
    Task StoreTokenAsync(string token);

    /// <summary>Removes any previously stored session token.</summary>
    Task ClearTokenAsync();
}

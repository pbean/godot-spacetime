using System.Threading.Tasks;
using GodotSpacetime.Auth;

namespace GodotSpacetime.Runtime.Auth;

internal sealed class MemoryTokenStore : ITokenStore
{
    private string? _token;

    public Task<string?> GetTokenAsync() => Task.FromResult(_token);

    public Task StoreTokenAsync(string token)
    {
        _token = token;
        return Task.CompletedTask;
    }

    public Task ClearTokenAsync()
    {
        _token = null;
        return Task.CompletedTask;
    }
}

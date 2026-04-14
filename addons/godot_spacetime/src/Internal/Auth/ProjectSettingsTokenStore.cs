using System;
using System.Threading.Tasks;
using Godot;
using GodotSpacetime.Auth;

namespace GodotSpacetime.Runtime.Auth;

internal sealed class ProjectSettingsTokenStore : ITokenStore
{
    private const string SettingKey = "spacetime/auth/token";

    public Task<string?> GetTokenAsync()
    {
        if (!ProjectSettings.HasSetting(SettingKey))
            return Task.FromResult<string?>(null);

        var value = ProjectSettings.GetSetting(SettingKey).AsString();
        return Task.FromResult<string?>(string.IsNullOrEmpty(value) ? null : value);
    }

    public Task StoreTokenAsync(string token)
    {
        ProjectSettings.SetSetting(SettingKey, token);
        return SaveChangesAsync();
    }

    public Task ClearTokenAsync()
    {
        ProjectSettings.SetSetting(SettingKey, string.Empty);
        return SaveChangesAsync();
    }

    private static Task SaveChangesAsync()
    {
        var saveResult = ProjectSettings.Save();
        if (saveResult != Error.Ok)
        {
            return Task.FromException(
                new InvalidOperationException($"Failed to persist ProjectSettings token store state: {saveResult}.")
            );
        }

        return Task.CompletedTask;
    }
}

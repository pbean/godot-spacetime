using System;
using System.Threading;
using System.Threading.Tasks;
using GodotSpacetime.Auth;
using GodotSpacetime.Connection;
using GodotSpacetime.Runtime.Platform.DotNet;

namespace GodotSpacetime.Runtime.Connection;

internal sealed class SpacetimeConnectionService : IConnectionEventSink
{
    private readonly ConnectionStateMachine _stateMachine = new();
    private readonly ReconnectPolicy _reconnectPolicy = new();
    private readonly SpacetimeSdkConnectionAdapter _adapter = new();
    private string _host = string.Empty;
    private string _database = string.Empty;
    private ITokenStore? _tokenStore;
    private bool _credentialsProvided;

    public SpacetimeConnectionService()
    {
        _stateMachine.StateChanged += status => OnStateChanged?.Invoke(status);
    }

    public event Action<ConnectionStatus>? OnStateChanged;

    public event Action<ConnectionOpenedEvent>? OnConnectionOpened;

    public ConnectionStatus CurrentStatus => _stateMachine.CurrentStatus;

    public void Connect(SpacetimeSettings settings)
    {
        ArgumentNullException.ThrowIfNull(settings);
        ValidateSettings(settings);

        if (CurrentStatus.State != ConnectionState.Disconnected)
            Disconnect("DISCONNECTED — closing the previous session before reconnecting.");

        _host = settings.Host.Trim();
        _database = settings.Database.Trim();
        _tokenStore = settings.TokenStore;
        _credentialsProvided = !string.IsNullOrWhiteSpace(settings.Credentials);
        _reconnectPolicy.Reset();

        _stateMachine.Transition(ConnectionState.Connecting, $"CONNECTING — opening a session to {_host}/{_database}");

        try
        {
            _adapter.Open(settings, this);
        }
        catch (Exception ex)
        {
            _adapter.Close();
            _stateMachine.Transition(ConnectionState.Disconnected, $"DISCONNECTED — failed to start the connection: {ex.Message}");
            throw;
        }
    }

    public void Disconnect()
    {
        Disconnect("DISCONNECTED — not connected to SpacetimeDB");
    }

    public void FrameTick()
    {
        if (CurrentStatus.State == ConnectionState.Disconnected)
            return;

        _adapter.FrameTick();
    }

    void IConnectionEventSink.OnConnected(string identity, string token)
    {
        _reconnectPolicy.Reset();
        if (_tokenStore != null)
        {
            // Optional token persistence must never break a successful connection.
            try
            {
                _ = _tokenStore.StoreTokenAsync(token).ContinueWith(
                    static completedTask => _ = completedTask.Exception,
                    CancellationToken.None,
                    TaskContinuationOptions.OnlyOnFaulted | TaskContinuationOptions.ExecuteSynchronously,
                    TaskScheduler.Default
                );
            }
            catch (Exception)
            {
            }
        }

        var authState = _credentialsProvided ? ConnectionAuthState.TokenRestored : ConnectionAuthState.None;

        if (CurrentStatus.State != ConnectionState.Connected)
        {
            var description = CurrentStatus.State == ConnectionState.Degraded
                ? "CONNECTED — active session established after recovery"
                : _credentialsProvided
                    ? "CONNECTED — authenticated session established"
                    : "CONNECTED — active session established";
            _stateMachine.Transition(ConnectionState.Connected, description, authState);
        }

        OnConnectionOpened?.Invoke(
            new ConnectionOpenedEvent
            {
                Host = _host,
                Database = _database,
                Identity = identity,
                ConnectedAt = DateTimeOffset.UtcNow,
            }
        );
    }

    void IConnectionEventSink.OnConnectError(Exception error)
    {
        _adapter.Close();

        if (CurrentStatus.State == ConnectionState.Connecting)
        {
            if (_credentialsProvided)
            {
                _stateMachine.Transition(
                    ConnectionState.Disconnected,
                    $"DISCONNECTED — authentication failed: {error.Message}",
                    ConnectionAuthState.AuthFailed
                );
            }
            else
            {
                _stateMachine.Transition(
                    ConnectionState.Disconnected,
                    $"DISCONNECTED — failed to connect: {error.Message}"
                );
            }
            return;
        }

        HandleDisconnectError(error);
    }

    void IConnectionEventSink.OnDisconnected(Exception? error)
    {
        if (error == null)
        {
            Disconnect("DISCONNECTED — not connected to SpacetimeDB");
            return;
        }

        HandleDisconnectError(error);
    }

    private void HandleDisconnectError(Exception error)
    {
        if (CurrentStatus.State == ConnectionState.Connected && _reconnectPolicy.TryBeginRetry(out var attemptNumber, out var delay))
        {
            _stateMachine.Transition(
                ConnectionState.Degraded,
                $"DEGRADED — session experiencing issues; reconnecting (attempt {attemptNumber}/{_reconnectPolicy.MaxAttempts}, backoff {delay.TotalSeconds:0.#}s): {error.Message}"
            );
            return;
        }

        _stateMachine.Transition(ConnectionState.Disconnected, $"DISCONNECTED — connection lost: {error.Message}");
    }

    private void Disconnect(string description)
    {
        _adapter.Close();
        _reconnectPolicy.Reset();

        if (CurrentStatus.State != ConnectionState.Disconnected)
            _stateMachine.Transition(ConnectionState.Disconnected, description);
    }

    private static void ValidateSettings(SpacetimeSettings settings)
    {
        if (string.IsNullOrWhiteSpace(settings.Host))
        {
            throw new ArgumentException(
                "Host is required before connecting.",
                nameof(SpacetimeSettings.Host)
            );
        }

        if (string.IsNullOrWhiteSpace(settings.Database))
        {
            throw new ArgumentException(
                "Database is required before connecting.",
                nameof(SpacetimeSettings.Database)
            );
        }
    }
}

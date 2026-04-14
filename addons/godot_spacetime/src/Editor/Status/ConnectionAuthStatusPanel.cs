#if TOOLS
using Godot;
using GodotSpacetime.Connection;

namespace GodotSpacetime.Editor.Status;

[Tool]
public partial class ConnectionAuthStatusPanel : VBoxContainer
{
    private const string StatusDisconnected = "DISCONNECTED — not connected to SpacetimeDB";
    private const string StatusConnecting = "CONNECTING — connection attempt in progress";
    private const string StatusConnected = "CONNECTED — active session established";
    private const string StatusDegraded = "DEGRADED — session experiencing issues; reconnecting";
    private const string StatusNotConfigured = "NOT CONFIGURED — assign a SpacetimeSettings resource";

    private Label _autoloadLabel = null!;
    private Label _statusLabel = null!;
    private Label _detailLabel = null!;
    private Label _authStateLabel = null!;
    private Label _authActionLabel = null!;
    private SpacetimeClient? _client;

    public override void _Ready()
    {
        BuildLayout();
        TryBindClient();
        RefreshStatus();
    }

    public override void _ExitTree()
    {
        if (_client != null)
            _client.ConnectionStateChanged -= OnConnectionStateChanged;
    }

    private void BuildLayout()
    {
        CustomMinimumSize = new Vector2(200, 0);

        var header = CreateFocusableLabel("Connection Status");
        header.AddThemeFontSizeOverride("font_size", 14);
        AddChild(header);

        AddChild(CreateFocusableLabel("Observed autoload:"));
        _autoloadLabel = CreateFocusableLabel();
        AddChild(_autoloadLabel);

        AddChild(new HSeparator());

        AddChild(CreateFocusableLabel("Current state:"));
        _statusLabel = CreateFocusableLabel();
        AddChild(_statusLabel);

        _detailLabel = CreateFocusableLabel();
        AddChild(_detailLabel);

        AddChild(new HSeparator());

        AddChild(CreateFocusableLabel("Auth state:"));
        _authStateLabel = CreateFocusableLabel();
        AddChild(_authStateLabel);

        _authActionLabel = CreateFocusableLabel();
        AddChild(_authActionLabel);
    }

    private void TryBindClient()
    {
        var nextClient = GetTree()?.Root.GetNodeOrNull<SpacetimeClient>("SpacetimeClient");
        if (ReferenceEquals(_client, nextClient))
            return;

        if (_client != null)
            _client.ConnectionStateChanged -= OnConnectionStateChanged;

        _client = nextClient;

        if (_client != null)
            _client.ConnectionStateChanged += OnConnectionStateChanged;
    }

    private void RefreshStatus()
    {
        TryBindClient();

        if (_client == null)
        {
            _autoloadLabel.Text = "Missing";
            SetStatus(StatusNotConfigured, "Add SpacetimeClient as an autoload to observe lifecycle state here.");
            SetAuthStatus(ConnectionAuthState.None, ConnectionState.Disconnected);
            return;
        }

        _autoloadLabel.Text = "SpacetimeClient";

        if (_client.Settings == null
            || string.IsNullOrWhiteSpace(_client.Settings.Host)
            || string.IsNullOrWhiteSpace(_client.Settings.Database))
        {
            SetStatus(StatusNotConfigured, "Assign a SpacetimeSettings resource with Host and Database values.");
            SetAuthStatus(ConnectionAuthState.None, ConnectionState.Disconnected);
            return;
        }

        var status = _client.CurrentStatus;
        SetStatus(MapStatus(status.State), status.Description);
        SetAuthStatus(status.AuthState, status.State);
    }

    private void SetAuthStatus(ConnectionAuthState authState, ConnectionState connState)
    {
        var (label, action) = authState switch
        {
            ConnectionAuthState.TokenRestored =>
                ("TOKEN RESTORED", "Session authenticated with provided credentials."),
            ConnectionAuthState.AuthFailed =>
                ("AUTH FAILED", "Credentials were rejected. Verify your token or call Settings.TokenStore?.ClearTokenAsync() to reset."),
            ConnectionAuthState.AuthRequired =>
                ("AUTH REQUIRED", "Configure Credentials on SpacetimeSettings to connect as an identified user."),
            _ when connState == ConnectionState.Connected =>
                ("ANONYMOUS", "Connected without credentials. No persistent identity."),
            _ =>
                ("AUTH REQUIRED", "Configure Credentials or a TokenStore before connecting as an identified user."),
        };

        _authStateLabel.Text = label;
        _authActionLabel.Text = action;
    }

    private static string MapStatus(ConnectionState state)
    {
        return state switch
        {
            ConnectionState.Disconnected => StatusDisconnected,
            ConnectionState.Connecting => StatusConnecting,
            ConnectionState.Connected => StatusConnected,
            ConnectionState.Degraded => StatusDegraded,
            _ => StatusNotConfigured,
        };
    }

    private static Label CreateFocusableLabel(string text = "")
    {
        return new Label
        {
            Text = text,
            FocusMode = FocusModeEnum.All,
            AutowrapMode = TextServer.AutowrapMode.WordSmart,
        };
    }

    private void SetStatus(string statusText, string detailText)
    {
        _statusLabel.Text = statusText;
        _detailLabel.Text = detailText;
    }

    private void OnConnectionStateChanged(ConnectionStatus status)
    {
        RefreshStatus();
    }
}
#endif

#if TOOLS
using System;
using System.IO;
using System.Threading.Tasks;
using Godot;

namespace GodotSpacetime.Editor.Codegen;

[Tool]
public partial class CodegenValidationPanel : VBoxContainer
{
    private const string RelativeModuleSource = "spacetime/modules/smoke_test";
    private const string RelativeOutputPath = "demo/generated/smoke_test";
    private const string DefaultGeneratedNamespace = "Spacetime" + "DB.Types";
    private const string StatusOk = "OK — bindings present";
    private const string StatusMissing = "MISSING — run codegen to generate";
    private const string StatusNotConfigured = "NOT CONFIGURED";
    private const string RecoveryCommand = "Run: bash scripts/codegen/generate-smoke-test.sh";
    private const string NotConfiguredGuidance = "Restore spacetime/modules/smoke_test before running codegen.";
    private const string GenerateInProgress = "Generating…";
    private const string RuntimeBlockedStatus = "BLOCKED — editor-only action unavailable at runtime";
    private const string RuntimeBlockedGuidance = "Fetch & Generate is only available inside the Godot editor.";

    private Label _moduleSourceLabel = null!;
    private Label _outputPathLabel = null!;
    private Label _statusLabel = null!;
    private Label _recoveryLabel = null!;
    private LineEdit _serverUrlEdit = null!;
    private LineEdit _moduleNameEdit = null!;
    private LineEdit _outputDirEdit = null!;
    private LineEdit _namespaceEdit = null!;
    private Button _generateButton = null!;
    private Label _generateStatusLabel = null!;
    private Label _generateRecoveryLabel = null!;
    private EditorCodegenService _editorCodegenService = null!;

    public override void _Ready()
    {
        _editorCodegenService = new EditorCodegenService(ProjectSettings.GlobalizePath("res://"));
        BuildLayout();
        PrepopulateFromSettings();
        RefreshStatus();
        ApplyRuntimeGuardrail();
    }

    private void BuildLayout()
    {
        CustomMinimumSize = new Vector2(200, 0);

        var header = CreateFocusableLabel("Code Generation Status");
        header.AddThemeFontSizeOverride("font_size", 14);
        AddChild(header);

        var moduleSourceFieldLabel = CreateFocusableLabel("Module source:");
        AddChild(moduleSourceFieldLabel);

        _moduleSourceLabel = CreateFocusableLabel();
        AddChild(_moduleSourceLabel);

        var outputPathFieldLabel = CreateFocusableLabel("Output path:");
        AddChild(outputPathFieldLabel);

        _outputPathLabel = CreateFocusableLabel();
        AddChild(_outputPathLabel);

        AddChild(new HSeparator());

        var statusFieldLabel = CreateFocusableLabel("Status:");
        AddChild(statusFieldLabel);

        _statusLabel = CreateFocusableLabel();
        AddChild(_statusLabel);

        _recoveryLabel = CreateFocusableLabel();
        _recoveryLabel.Visible = false;
        AddChild(_recoveryLabel);

        AddChild(new HSeparator());

        var generateHeader = CreateFocusableLabel("Generate from Server");
        generateHeader.AddThemeFontSizeOverride("font_size", 14);
        AddChild(generateHeader);

        AddChild(CreateFocusableLabel("Server URL:"));
        _serverUrlEdit = CreateFocusableLineEdit();
        AddChild(_serverUrlEdit);

        AddChild(CreateFocusableLabel("Module name:"));
        _moduleNameEdit = CreateFocusableLineEdit();
        AddChild(_moduleNameEdit);

        AddChild(CreateFocusableLabel("Output directory:"));
        _outputDirEdit = CreateFocusableLineEdit(RelativeOutputPath);
        AddChild(_outputDirEdit);

        AddChild(CreateFocusableLabel("Namespace:"));
        _namespaceEdit = CreateFocusableLineEdit(DefaultGeneratedNamespace);
        AddChild(_namespaceEdit);

        _generateButton = new Button
        {
            Text = "Fetch & Generate",
            FocusMode = FocusModeEnum.All,
            SizeFlagsHorizontal = SizeFlags.ExpandFill,
        };
        _generateButton.Pressed += OnGeneratePressed;
        AddChild(_generateButton);

        _generateStatusLabel = CreateFocusableLabel();
        AddChild(_generateStatusLabel);

        _generateRecoveryLabel = CreateFocusableLabel();
        _generateRecoveryLabel.Visible = false;
        AddChild(_generateRecoveryLabel);
    }

    private void RefreshStatus()
    {
        _moduleSourceLabel.Text = RelativeModuleSource;
        _outputPathLabel.Text = GetConfiguredOutputPath();

        var absoluteModuleSource = ResolveProjectPath(RelativeModuleSource);
        if (!Directory.Exists(absoluteModuleSource))
        {
            SetStatus(StatusNotConfigured, NotConfiguredGuidance);
            return;
        }

        var absoluteOutputPath = ResolveProjectPath(GetConfiguredOutputPath());
        if (!Directory.Exists(absoluteOutputPath) || !HasGeneratedBindings(absoluteOutputPath))
        {
            SetStatus(StatusMissing, RecoveryCommand);
            return;
        }

        SetStatus(StatusOk);
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

    private static LineEdit CreateFocusableLineEdit(string text = "")
    {
        return new LineEdit
        {
            Text = text,
            FocusMode = FocusModeEnum.All,
            SizeFlagsHorizontal = SizeFlags.ExpandFill,
        };
    }

    private static bool HasGeneratedBindings(string absoluteOutputPath)
    {
        try
        {
            foreach (var _ in Directory.EnumerateFiles(absoluteOutputPath, "*.cs", SearchOption.AllDirectories))
            {
                return true;
            }
        }
        catch (IOException)
        {
            return false;
        }
        catch (UnauthorizedAccessException)
        {
            return false;
        }

        return false;
    }

    private static string ResolveProjectPath(string relativePath)
    {
        if (Path.IsPathRooted(relativePath))
            return Path.GetFullPath(relativePath);

        return Path.Combine(ProjectSettings.GlobalizePath("res://"), relativePath);
    }

    private void SetStatus(string statusText, string recoveryText = "")
    {
        _statusLabel.Text = statusText;
        _recoveryLabel.Text = recoveryText;
        _recoveryLabel.Visible = !string.IsNullOrEmpty(recoveryText);
    }

    private string GetConfiguredOutputPath()
    {
        var configured = _outputDirEdit?.Text?.Trim() ?? string.Empty;
        return string.IsNullOrWhiteSpace(configured) ? RelativeOutputPath : configured;
    }

    private void ApplyRuntimeGuardrail()
    {
        if (Engine.IsEditorHint())
            return;

        _generateButton.Disabled = true;
        ApplyGenerateResult(EditorCodegenResult.Failure(RuntimeBlockedStatus, RuntimeBlockedGuidance));
    }

    private async void OnGeneratePressed()
    {
        if (!Engine.IsEditorHint())
        {
            ApplyGenerateResult(EditorCodegenResult.Failure(RuntimeBlockedStatus, RuntimeBlockedGuidance));
            return;
        }

        _generateButton.Disabled = true;
        _generateStatusLabel.Text = GenerateInProgress;
        _generateRecoveryLabel.Text = string.Empty;
        _generateRecoveryLabel.Visible = false;

        try
        {
            var result = await Task.Run(() => _editorCodegenService.GenerateBindingsAsync(
                _serverUrlEdit.Text,
                _moduleNameEdit.Text,
                _outputDirEdit.Text,
                _namespaceEdit.Text));

            ApplyGenerateResult(result);

            if (result.IsSuccess)
            {
                RefreshStatus();
            }
        }
        finally
        {
            _generateButton.Disabled = !Engine.IsEditorHint();
        }
    }

    private void ApplyGenerateResult(EditorCodegenResult result)
    {
        _generateStatusLabel.Text = result.StatusMessage;
        _generateRecoveryLabel.Text = result.ErrorDetail ?? string.Empty;
        _generateRecoveryLabel.Visible = !string.IsNullOrWhiteSpace(result.ErrorDetail);
    }

    private void PrepopulateFromSettings()
    {
        var settings = FindSpacetimeSettings();
        if (settings is null)
            return;

        if (!string.IsNullOrWhiteSpace(settings.Host))
            _serverUrlEdit.Text = settings.Host.Trim();

        if (!string.IsNullOrWhiteSpace(settings.Database))
            _moduleNameEdit.Text = settings.Database.Trim();

        _namespaceEdit.Text = string.IsNullOrWhiteSpace(settings.GeneratedBindingsNamespace)
            ? DefaultGeneratedNamespace
            : settings.ResolveGeneratedBindingsNamespace();
    }

    private static global::GodotSpacetime.SpacetimeSettings? FindSpacetimeSettings()
    {
        foreach (var preferredPath in new[]
                 {
                     "res://SpacetimeSettings.tres",
                     "res://addons/godot_spacetime/spacetime_settings.tres",
                     "res://addons/godot_spacetime/SpacetimeSettings.tres",
                 })
        {
            if (TryLoadSpacetimeSettings(preferredPath, out var preferred))
                return preferred;
        }

        var projectRoot = ProjectSettings.GlobalizePath("res://");
        var directories = new System.Collections.Generic.Stack<string>();
        directories.Push(projectRoot);

        while (directories.Count > 0)
        {
            var directory = directories.Pop();

            try
            {
                foreach (var subdirectory in Directory.EnumerateDirectories(directory))
                {
                    if (!ShouldSkipSettingsScanDirectory(subdirectory))
                        directories.Push(subdirectory);
                }

                foreach (var file in Directory.EnumerateFiles(directory, "*.tres"))
                {
                    if (TryLoadSpacetimeSettings(ToResPath(projectRoot, file), out var settings))
                        return settings;
                }

                foreach (var file in Directory.EnumerateFiles(directory, "*.res"))
                {
                    if (TryLoadSpacetimeSettings(ToResPath(projectRoot, file), out var settings))
                        return settings;
                }
            }
            catch (IOException)
            {
            }
            catch (UnauthorizedAccessException)
            {
            }
        }

        return null;
    }

    private static bool TryLoadSpacetimeSettings(string resourcePath, out global::GodotSpacetime.SpacetimeSettings? settings)
    {
        settings = null;

        try
        {
            settings = ResourceLoader.Load<global::GodotSpacetime.SpacetimeSettings>(resourcePath);
            return settings is not null;
        }
        catch
        {
            return false;
        }
    }

    private static bool ShouldSkipSettingsScanDirectory(string directoryPath)
    {
        var directoryName = Path.GetFileName(directoryPath);
        return string.Equals(directoryName, ".git", StringComparison.OrdinalIgnoreCase) ||
               string.Equals(directoryName, ".godot", StringComparison.OrdinalIgnoreCase) ||
               string.Equals(directoryName, "bin", StringComparison.OrdinalIgnoreCase) ||
               string.Equals(directoryName, "obj", StringComparison.OrdinalIgnoreCase) ||
               string.Equals(directoryName, "target", StringComparison.OrdinalIgnoreCase) ||
               string.Equals(directoryName, "node_modules", StringComparison.OrdinalIgnoreCase);
    }

    private static string ToResPath(string projectRoot, string absolutePath)
    {
        var relativePath = Path.GetRelativePath(projectRoot, absolutePath)
            .Replace(Path.DirectorySeparatorChar, '/');
        return $"res://{relativePath}";
    }
}
#endif

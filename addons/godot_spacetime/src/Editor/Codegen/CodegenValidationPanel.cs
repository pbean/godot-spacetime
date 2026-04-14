#if TOOLS
using System;
using System.IO;
using Godot;

namespace GodotSpacetime.Editor.Codegen;

[Tool]
public partial class CodegenValidationPanel : VBoxContainer
{
    private const string RelativeModuleSource = "spacetime/modules/smoke_test";
    private const string RelativeOutputPath = "demo/generated/smoke_test";
    private const string StatusOk = "OK — bindings present";
    private const string StatusMissing = "MISSING — run codegen to generate";
    private const string StatusNotConfigured = "NOT CONFIGURED";
    private const string RecoveryCommand = "Run: bash scripts/codegen/generate-smoke-test.sh";
    private const string NotConfiguredGuidance = "Restore spacetime/modules/smoke_test before running codegen.";

    private Label _moduleSourceLabel = null!;
    private Label _outputPathLabel = null!;
    private Label _statusLabel = null!;
    private Label _recoveryLabel = null!;

    public override void _Ready()
    {
        BuildLayout();
        RefreshStatus();
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
    }

    private void RefreshStatus()
    {
        _moduleSourceLabel.Text = RelativeModuleSource;
        _outputPathLabel.Text = RelativeOutputPath;

        var absoluteModuleSource = ResolveProjectPath(RelativeModuleSource);
        if (!Directory.Exists(absoluteModuleSource))
        {
            SetStatus(StatusNotConfigured, NotConfiguredGuidance);
            return;
        }

        var absoluteOutputPath = ResolveProjectPath(RelativeOutputPath);
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
        return Path.Combine(ProjectSettings.GlobalizePath("res://"), relativePath);
    }

    private void SetStatus(string statusText, string recoveryText = "")
    {
        _statusLabel.Text = statusText;
        _recoveryLabel.Text = recoveryText;
        _recoveryLabel.Visible = !string.IsNullOrEmpty(recoveryText);
    }
}
#endif

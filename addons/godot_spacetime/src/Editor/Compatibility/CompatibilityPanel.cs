#if TOOLS
using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Godot;

namespace GodotSpacetime.Editor.Compatibility;

[Tool]
public partial class CompatibilityPanel : VBoxContainer
{
    private const string RelativeBaselineJson = "scripts/compatibility/support-baseline.json";
    private const string RelativeGeneratedClient = "demo/generated/smoke_test/SpacetimeDBClient.g.cs";
    private const string RelativeModuleSource = "spacetime/modules/smoke_test";
    private const string CliVersionPrefix = "// This was generated using spacetimedb cli version ";
    private const string BindingVersionNotFound = "version not found";
    private const string CompatOk = "OK — bindings match declared baseline";
    private const string CompatIncompatible = "INCOMPATIBLE — bindings do not match declared baseline";
    private const string CompatMissing = "MISSING — run codegen to generate bindings";
    private const string CompatNotConfigured = "NOT CONFIGURED";
    private const string CompatRecovery = "Run: bash scripts/codegen/generate-smoke-test.sh";

    private Label _godotVersionLabel = null!;
    private Label _stdbVersionLabel = null!;
    private Label _clientSdkVersionLabel = null!;
    private Label _bindingVersionLabel = null!;
    private Label _compatStatusLabel = null!;
    private Label _recoveryLabel = null!;

    public override void _Ready()
    {
        BuildLayout();
        RefreshStatus();
    }

    private void BuildLayout()
    {
        CustomMinimumSize = new Vector2(200, 0);

        var header = CreateFocusableLabel("Compatibility Baseline");
        header.AddThemeFontSizeOverride("font_size", 14);
        AddChild(header);

        AddChild(CreateFocusableLabel("Godot target:"));
        _godotVersionLabel = CreateFocusableLabel();
        AddChild(_godotVersionLabel);

        AddChild(CreateFocusableLabel("SpacetimeDB CLI:"));
        _stdbVersionLabel = CreateFocusableLabel();
        AddChild(_stdbVersionLabel);

        AddChild(CreateFocusableLabel("ClientSDK:"));
        _clientSdkVersionLabel = CreateFocusableLabel();
        AddChild(_clientSdkVersionLabel);

        AddChild(new HSeparator());

        AddChild(CreateFocusableLabel("Binding CLI version:"));
        _bindingVersionLabel = CreateFocusableLabel();
        AddChild(_bindingVersionLabel);

        AddChild(new HSeparator());

        AddChild(CreateFocusableLabel("Compatibility status:"));
        _compatStatusLabel = CreateFocusableLabel();
        AddChild(_compatStatusLabel);

        _recoveryLabel = CreateFocusableLabel();
        _recoveryLabel.Visible = false;
        AddChild(_recoveryLabel);
    }

    private void RefreshStatus()
    {
        ResetDisplayValues();

        try
        {
            var projectRoot = ProjectSettings.GlobalizePath("res://");
            var jsonPath = ResolveProjectPath(RelativeBaselineJson);
            var jsonText = File.ReadAllText(jsonPath);
            using var doc = JsonDocument.Parse(jsonText);
            var sv = doc.RootElement.GetProperty("support_versions");
            var declaredGodot = sv.GetProperty("godot_product").GetString() ?? "?";
            var declaredStdb = sv.GetProperty("spacetimedb").GetString() ?? "?";
            var declaredClientSdk = sv.GetProperty("spacetimedb_client_sdk").GetString() ?? "?";

            _godotVersionLabel.Text = declaredGodot;
            _stdbVersionLabel.Text = declaredStdb;
            _clientSdkVersionLabel.Text = declaredClientSdk;

            var modulePath = ResolveProjectPath(RelativeModuleSource);
            if (!Directory.Exists(modulePath))
            {
                SetStatus(CompatNotConfigured);
                return;
            }

            var generatedPath = ResolveProjectPath(RelativeGeneratedClient);
            if (!File.Exists(generatedPath))
            {
                SetStatus(CompatMissing, WithRecovery("Binding registry file not found."));
                return;
            }

            string? extractedVersion = null;
            foreach (var line in File.ReadLines(generatedPath))
            {
                if (line.StartsWith(CliVersionPrefix, StringComparison.Ordinal))
                {
                    var rest = line.Substring(CliVersionPrefix.Length);
                    var token = rest.Split(' ', StringSplitOptions.RemoveEmptyEntries).FirstOrDefault();
                    if (!string.IsNullOrEmpty(token))
                        extractedVersion = token;
                    break;
                }
            }

            if (string.IsNullOrEmpty(extractedVersion))
            {
                SetStatus(CompatMissing, WithRecovery("Generated bindings do not contain the CLI version comment."));
                return;
            }

            _bindingVersionLabel.Text = extractedVersion;

            if (TryGetNewestRelevantModuleSource(modulePath, out var newestModuleSource, out var newestModuleWriteUtc)
                && newestModuleWriteUtc > File.GetLastWriteTimeUtc(generatedPath))
            {
                var relativeModuleSource = Path.GetRelativePath(projectRoot, newestModuleSource);
                SetStatus(CompatIncompatible, WithRecovery($"{relativeModuleSource} is newer than generated bindings."));
                return;
            }

            if (VersionSatisfiesBaseline(extractedVersion, declaredStdb))
                SetStatus(CompatOk);
            else
                SetStatus(CompatIncompatible, WithRecovery($"Binding CLI {extractedVersion} does not satisfy declared baseline {declaredStdb}."));
        }
        catch (Exception)
        {
            ResetDisplayValues();
            SetStatus(CompatNotConfigured);
        }
    }

    private static bool VersionSatisfiesBaseline(string extracted, string baseline)
    {
        var minimum = baseline.TrimEnd('+');
        var minimumParts = minimum.Split('.');
        var extractedParts = extracted.Split('.');

        for (var i = 0; i < minimumParts.Length; i++)
        {
            int.TryParse(minimumParts[i], out var minPart);
            int extPart = 0;
            if (i < extractedParts.Length)
                int.TryParse(extractedParts[i], out extPart);

            if (extPart > minPart)
                return true;
            if (extPart < minPart)
                return false;
        }

        return true;
    }

    private static Label CreateFocusableLabel(string text = "")
    {
        return new Label { Text = text, FocusMode = FocusModeEnum.All, AutowrapMode = TextServer.AutowrapMode.WordSmart };
    }

    private void ResetDisplayValues()
    {
        _godotVersionLabel.Text = "?";
        _stdbVersionLabel.Text = "?";
        _clientSdkVersionLabel.Text = "?";
        _bindingVersionLabel.Text = BindingVersionNotFound;
    }

    private static string ResolveProjectPath(string relativePath)
    {
        return Path.Combine(ProjectSettings.GlobalizePath("res://"), relativePath);
    }

    private static bool TryGetNewestRelevantModuleSource(string modulePath, out string newestModuleSource, out DateTime newestWriteUtc)
    {
        newestModuleSource = string.Empty;
        newestWriteUtc = DateTime.MinValue;

        var cargoTomlPath = Path.Combine(modulePath, "Cargo.toml");
        TrySetNewestSource(cargoTomlPath, ref newestModuleSource, ref newestWriteUtc);

        foreach (var sourcePath in Directory.EnumerateFiles(modulePath, "*.rs", SearchOption.AllDirectories))
            TrySetNewestSource(sourcePath, ref newestModuleSource, ref newestWriteUtc);

        return !string.IsNullOrEmpty(newestModuleSource);
    }

    private static void TrySetNewestSource(string sourcePath, ref string newestModuleSource, ref DateTime newestWriteUtc)
    {
        if (!File.Exists(sourcePath))
            return;

        var sourceWriteUtc = File.GetLastWriteTimeUtc(sourcePath);
        if (sourceWriteUtc <= newestWriteUtc)
            return;

        newestWriteUtc = sourceWriteUtc;
        newestModuleSource = sourcePath;
    }

    private static string WithRecovery(string detail)
    {
        return string.IsNullOrWhiteSpace(detail) ? CompatRecovery : $"{detail}\n{CompatRecovery}";
    }

    private void SetStatus(string statusText, string recoveryText = "")
    {
        _compatStatusLabel.Text = statusText;
        _recoveryLabel.Text = recoveryText;
        _recoveryLabel.Visible = !string.IsNullOrEmpty(recoveryText);
    }
}
#endif

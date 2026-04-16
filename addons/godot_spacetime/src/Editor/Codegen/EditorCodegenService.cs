#if TOOLS
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace GodotSpacetime.Editor.Codegen;

internal sealed class EditorCodegenService
{
    private const string DefaultGeneratedNamespace = "Spacetime" + "DB.Types";
    private static readonly TimeSpan HttpTimeout = TimeSpan.FromSeconds(30);
    private readonly string _projectRoot;

    internal EditorCodegenService(string projectRoot)
    {
        _projectRoot = Path.GetFullPath(projectRoot);
    }

    internal async Task<EditorCodegenResult> GenerateBindingsAsync(
        string serverUrl,
        string moduleName,
        string outputDir,
        string generatedNamespace)
    {
        var trimmedServerUrl = serverUrl?.Trim() ?? string.Empty;
        var trimmedModuleName = moduleName?.Trim() ?? string.Empty;
        var trimmedOutputDir = outputDir?.Trim() ?? string.Empty;
        var trimmedNamespace = string.IsNullOrWhiteSpace(generatedNamespace)
            ? DefaultGeneratedNamespace
            : generatedNamespace.Trim();

        if (string.IsNullOrWhiteSpace(trimmedServerUrl))
        {
            return EditorCodegenResult.Failure(
                "FAILED — could not reach server: missing server URL",
                "Enter a server URL before fetching bindings.");
        }

        if (string.IsNullOrWhiteSpace(trimmedModuleName))
        {
            return EditorCodegenResult.Failure(
                "FAILED — generation error (see recovery guidance)",
                "Enter a module name before fetching bindings.");
        }

        if (string.IsNullOrWhiteSpace(trimmedOutputDir))
        {
            return EditorCodegenResult.Failure(
                "BLOCKED — output directory outside safe boundary",
                "Output must be under a 'generated' path. Current: <empty>");
        }

        if (!TryResolveOutputDirectory(trimmedOutputDir, out var absoluteOutputDir, out var safetyError))
        {
            return EditorCodegenResult.Failure(
                "BLOCKED — output directory outside safe boundary",
                safetyError);
        }

        string? tempArtifactPath = null;
        try
        {
            var artifact = await FetchSchemaArtifactAsync(trimmedServerUrl, trimmedModuleName).ConfigureAwait(false);
            tempArtifactPath = WriteArtifactToTempFile(artifact);

            PrepareOutputDirectory(absoluteOutputDir);

            var codegenProcess = await RunProcessAsync(
                "spacetime",
                [
                    "generate",
                    "--bin-path",
                    tempArtifactPath,
                    "--lang",
                    "csharp",
                    "--out-dir",
                    absoluteOutputDir,
                    "--namespace",
                    trimmedNamespace,
                    "-y",
                ]).ConfigureAwait(false);

            if (codegenProcess.ExitCode != 0)
            {
                return EditorCodegenResult.Failure(
                    "FAILED — generation error (see recovery guidance)",
                    BuildProcessErrorDetail(
                        "spacetime generate failed.",
                        codegenProcess,
                        "Install spacetime CLI 2.1+ and ensure it is in PATH."));
            }

            var typesDirectory = Path.Combine(absoluteOutputDir, "Types");
            var postProcess = await RunProcessAsync(
                "python3",
                [
                    Path.Combine(_projectRoot, "scripts", "codegen", "detect-godot-types.py"),
                    typesDirectory,
                ]).ConfigureAwait(false);

            if (postProcess.ExitCode != 0)
            {
                return EditorCodegenResult.Failure(
                    "FAILED — generation error (see recovery guidance)",
                    BuildProcessErrorDetail(
                        "detect-godot-types.py failed.",
                        postProcess,
                        "Install python3 and ensure it is in PATH."));
            }

            AlignGodotCompanionNamespaces(typesDirectory, trimmedNamespace);

            return EditorCodegenResult.Success($"OK — bindings generated from {trimmedModuleName}");
        }
        catch (EditorCodegenFailureException ex)
        {
            return EditorCodegenResult.Failure(ex.StatusMessage, ex.ErrorDetail);
        }
        catch (Exception ex)
        {
            return EditorCodegenResult.Failure(
                "FAILED — generation error (see recovery guidance)",
                ex.ToString());
        }
        finally
        {
            if (!string.IsNullOrEmpty(tempArtifactPath))
            {
                TryDeleteFile(tempArtifactPath);
            }
        }
    }

    private async Task<DownloadedArtifact> FetchSchemaArtifactAsync(string serverUrl, string moduleName)
    {
        var normalizedServer = NormalizeServerUrl(serverUrl);
        var modulePath = $"v1/database/{Uri.EscapeDataString(moduleName)}";
        var candidateUris = new[]
        {
            new Uri(normalizedServer, modulePath),
            new Uri(normalizedServer, $"{modulePath}/wasm"),
            new Uri(normalizedServer, $"{modulePath}/schema"),
        };

        using var httpClient = new HttpClient
        {
            Timeout = HttpTimeout,
        };

        string? lastNon404Error = null;
        byte[]? lastJsonPayload = null;

        foreach (var candidateUri in candidateUris)
        {
            using var response = await SendAnonymousGetAsync(httpClient, candidateUri).ConfigureAwait(false);

            if (response.StatusCode == HttpStatusCode.NotFound)
            {
                continue;
            }

            if (!response.IsSuccessStatusCode)
            {
                lastNon404Error = $"GET {candidateUri} returned {(int)response.StatusCode} {response.ReasonPhrase}.";
                continue;
            }

            var payload = await response.Content.ReadAsByteArrayAsync().ConfigureAwait(false);
            if (!IsJsonResponse(response, payload))
            {
                return new DownloadedArtifact(payload, ".wasm");
            }

            lastJsonPayload = payload;
            if (TryExtractDownloadUri(payload, normalizedServer, out var downloadUri))
            {
                using var nestedResponse = await SendAnonymousGetAsync(httpClient, downloadUri).ConfigureAwait(false);
                if (!nestedResponse.IsSuccessStatusCode)
                {
                    throw new EditorCodegenFailureException(
                        $"FAILED — could not reach server: {(int)nestedResponse.StatusCode} {nestedResponse.ReasonPhrase}",
                        $"GET {downloadUri} returned {(int)nestedResponse.StatusCode} {nestedResponse.ReasonPhrase}.");
                }

                var nestedPayload = await nestedResponse.Content.ReadAsByteArrayAsync().ConfigureAwait(false);
                if (IsJsonResponse(nestedResponse, nestedPayload))
                {
                    lastJsonPayload = nestedPayload;
                    continue;
                }

                return new DownloadedArtifact(nestedPayload, ".wasm");
            }
        }

        if (lastJsonPayload is not null)
        {
            var tempJsonPath = WriteArtifactToTempFile(new DownloadedArtifact(lastJsonPayload, ".json"));
            TryDeleteFile(tempJsonPath);
            throw new EditorCodegenFailureException(
                "FAILED — generation error (see recovery guidance)",
                "The server returned JSON metadata or schema but no downloadable wasm artifact. " +
                "The pinned spacetime generate flow requires a wasm artifact for --bin-path.");
        }

        throw new EditorCodegenFailureException(
            "FAILED — could not reach server: module endpoint not found",
            lastNon404Error ??
            $"No supported module endpoint was found under {new Uri(normalizedServer, modulePath)}.");
    }

    private static Uri NormalizeServerUrl(string serverUrl)
    {
        var candidate = serverUrl.Contains("://", StringComparison.Ordinal)
            ? serverUrl
            : $"http://{serverUrl}";

        if (!Uri.TryCreate(candidate, UriKind.Absolute, out var uri) ||
            (uri.Scheme != Uri.UriSchemeHttp && uri.Scheme != Uri.UriSchemeHttps))
        {
            throw new EditorCodegenFailureException(
                "FAILED — could not reach server: invalid server URL",
                $"'{serverUrl}' is not a valid http(s) server URL.");
        }

        var uriText = uri.ToString();
        if (!uriText.EndsWith("/", StringComparison.Ordinal))
        {
            uriText += "/";
        }

        return new Uri(uriText, UriKind.Absolute);
    }

    private static async Task<HttpResponseMessage> SendAnonymousGetAsync(HttpClient httpClient, Uri uri)
    {
        try
        {
            var response = await httpClient.GetAsync(uri, HttpCompletionOption.ResponseHeadersRead).ConfigureAwait(false);
            if (response.StatusCode == HttpStatusCode.Unauthorized || response.StatusCode == HttpStatusCode.Forbidden)
            {
                response.Dispose();
                throw new EditorCodegenFailureException(
                    "FAILED — server requires authentication",
                    "In-editor codegen only supports anonymous schema access.");
            }

            return response;
        }
        catch (TaskCanceledException ex)
        {
            throw new EditorCodegenFailureException(
                "FAILED — could not reach server: request timed out",
                $"HTTP fetch timed out after {HttpTimeout.TotalSeconds:0} seconds.\n{ex.Message}");
        }
        catch (HttpRequestException ex)
        {
            throw new EditorCodegenFailureException(
                $"FAILED — could not reach server: {CollapseWhitespace(ex.Message)}",
                $"Check server URL and ensure the server is running.\n{ex.Message}");
        }
    }

    private bool TryResolveOutputDirectory(string outputDir, out string absoluteOutputDir, out string errorDetail)
    {
        absoluteOutputDir = ResolvePath(outputDir);
        var relativeOutputDir = Path.GetRelativePath(_projectRoot, absoluteOutputDir)
            .Replace(Path.AltDirectorySeparatorChar, Path.DirectorySeparatorChar);
        var isKnownGeneratedRoot =
            IsSameOrDescendant(absoluteOutputDir, Path.Combine(_projectRoot, "demo", "generated")) ||
            IsSameOrDescendant(absoluteOutputDir, Path.Combine(_projectRoot, "tests", "fixtures", "generated"));

        if (isKnownGeneratedRoot)
        {
            errorDetail = string.Empty;
            return true;
        }

        if (string.Equals(absoluteOutputDir, _projectRoot, StringComparison.OrdinalIgnoreCase))
        {
            errorDetail = $"Output must be under a 'generated' path. Current: {outputDir}";
            return false;
        }

        foreach (var blockedRelativePath in new[]
                 {
                     "addons",
                     "src",
                     "tests",
                     "docs",
                     "scripts",
                     ".github",
                 })
        {
            var blockedPath = Path.Combine(_projectRoot, blockedRelativePath);
            if (IsSameOrDescendant(absoluteOutputDir, blockedPath))
            {
                errorDetail = $"Output must be under a 'generated' path. Current: {outputDir}";
                return false;
            }
        }

        var segments = relativeOutputDir.Split(Path.DirectorySeparatorChar, StringSplitOptions.RemoveEmptyEntries);
        var containsGeneratedSegment = false;
        foreach (var segment in segments)
        {
            if (string.Equals(segment, "generated", StringComparison.OrdinalIgnoreCase))
            {
                containsGeneratedSegment = true;
                break;
            }
        }

        if (!containsGeneratedSegment && !isKnownGeneratedRoot)
        {
            errorDetail = $"Output must be under a 'generated' path. Current: {outputDir}";
            return false;
        }

        errorDetail = string.Empty;
        return true;
    }

    private void PrepareOutputDirectory(string absoluteOutputDir)
    {
        if (Directory.Exists(absoluteOutputDir))
        {
            Directory.Delete(absoluteOutputDir, recursive: true);
        }

        Directory.CreateDirectory(absoluteOutputDir);
    }

    private static bool IsJsonResponse(HttpResponseMessage response, byte[] payload)
    {
        var mediaType = response.Content.Headers.ContentType?.MediaType;
        if (!string.IsNullOrEmpty(mediaType) &&
            mediaType.Contains("json", StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        var preview = Encoding.UTF8.GetString(payload, 0, Math.Min(payload.Length, 32)).TrimStart();
        return preview.StartsWith("{", StringComparison.Ordinal) || preview.StartsWith("[", StringComparison.Ordinal);
    }

    private static bool TryExtractDownloadUri(byte[] jsonPayload, Uri baseUri, out Uri downloadUri)
    {
        using var document = JsonDocument.Parse(jsonPayload);
        if (TryExtractDownloadUri(document.RootElement, baseUri, out downloadUri))
        {
            return true;
        }

        downloadUri = null!;
        return false;
    }

    private static bool TryExtractDownloadUri(JsonElement element, Uri baseUri, out Uri downloadUri)
    {
        if (element.ValueKind == JsonValueKind.Object)
        {
            foreach (var property in element.EnumerateObject())
            {
                if (property.Value.ValueKind == JsonValueKind.String &&
                    LooksLikeArtifactUrlKey(property.Name) &&
                    TryCreateUri(baseUri, property.Value.GetString(), out downloadUri))
                {
                    return true;
                }
            }

            foreach (var property in element.EnumerateObject())
            {
                if (TryExtractDownloadUri(property.Value, baseUri, out downloadUri))
                {
                    return true;
                }
            }
        }

        if (element.ValueKind == JsonValueKind.Array)
        {
            foreach (var item in element.EnumerateArray())
            {
                if (TryExtractDownloadUri(item, baseUri, out downloadUri))
                {
                    return true;
                }
            }
        }

        downloadUri = null!;
        return false;
    }

    private static bool LooksLikeArtifactUrlKey(string propertyName)
    {
        return propertyName.Contains("wasm", StringComparison.OrdinalIgnoreCase) ||
               propertyName.Contains("download", StringComparison.OrdinalIgnoreCase) ||
               propertyName.Contains("artifact", StringComparison.OrdinalIgnoreCase) ||
               propertyName.Contains("module", StringComparison.OrdinalIgnoreCase);
    }

    private static bool TryCreateUri(Uri baseUri, string? uriText, out Uri uri)
    {
        if (string.IsNullOrWhiteSpace(uriText))
        {
            uri = null!;
            return false;
        }

        if (Uri.TryCreate(uriText, UriKind.Absolute, out var absoluteUri))
        {
            uri = absoluteUri;
            return true;
        }

        if (Uri.TryCreate(baseUri, uriText, out var relativeUri))
        {
            uri = relativeUri;
            return true;
        }

        uri = null!;
        return false;
    }

    private string WriteArtifactToTempFile(DownloadedArtifact artifact)
    {
        var tempFilePath = Path.Combine(Path.GetTempPath(), $"{Guid.NewGuid():N}{artifact.Extension}");
        File.WriteAllBytes(tempFilePath, artifact.Content);
        return tempFilePath;
    }

    private async Task<ProcessExecutionResult> RunProcessAsync(string executable, IReadOnlyList<string> arguments)
    {
        var startInfo = new ProcessStartInfo
        {
            FileName = executable,
            WorkingDirectory = _projectRoot,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };

        foreach (var argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        try
        {
            using var process = new Process
            {
                StartInfo = startInfo,
            };

            if (!process.Start())
            {
                throw new EditorCodegenFailureException(
                    "FAILED — generation error (see recovery guidance)",
                    $"Failed to start process '{executable}'.");
            }

            var stdoutTask = process.StandardOutput.ReadToEndAsync();
            var stderrTask = process.StandardError.ReadToEndAsync();

            await process.WaitForExitAsync().ConfigureAwait(false);

            return new ProcessExecutionResult(
                process.ExitCode,
                await stdoutTask.ConfigureAwait(false),
                await stderrTask.ConfigureAwait(false));
        }
        catch (Win32Exception) when (string.Equals(executable, "spacetime", StringComparison.Ordinal))
        {
            throw new EditorCodegenFailureException(
                "FAILED — spacetime CLI not found in PATH",
                "Install spacetime CLI 2.1+ and ensure it is in PATH.");
        }
        catch (Win32Exception ex) when (string.Equals(executable, "python3", StringComparison.Ordinal))
        {
            throw new EditorCodegenFailureException(
                "FAILED — generation error (see recovery guidance)",
                $"python3 not found in PATH.\n{ex.Message}");
        }
    }

    private static string BuildProcessErrorDetail(
        string headline,
        ProcessExecutionResult result,
        string guidance)
    {
        var builder = new StringBuilder();
        builder.AppendLine(headline);
        builder.AppendLine($"Exit code: {result.ExitCode}");
        if (!string.IsNullOrWhiteSpace(result.Stdout))
        {
            builder.AppendLine();
            builder.AppendLine("stdout:");
            builder.AppendLine(result.Stdout.Trim());
        }

        if (!string.IsNullOrWhiteSpace(result.Stderr))
        {
            builder.AppendLine();
            builder.AppendLine("stderr:");
            builder.AppendLine(result.Stderr.Trim());
        }

        if (!string.IsNullOrWhiteSpace(guidance))
        {
            builder.AppendLine();
            builder.AppendLine(guidance);
        }

        return builder.ToString().Trim();
    }

    private static string CollapseWhitespace(string value)
    {
        var builder = new StringBuilder(value.Length);
        var previousWasWhitespace = false;
        foreach (var ch in value)
        {
            if (char.IsWhiteSpace(ch))
            {
                if (previousWasWhitespace)
                {
                    continue;
                }

                builder.Append(' ');
                previousWasWhitespace = true;
                continue;
            }

            builder.Append(ch);
            previousWasWhitespace = false;
        }

        return builder.ToString().Trim();
    }

    private static void AlignGodotCompanionNamespaces(string typesDirectory, string generatedNamespace)
    {
        if (!Directory.Exists(typesDirectory) ||
            string.Equals(generatedNamespace, DefaultGeneratedNamespace, StringComparison.Ordinal))
        {
            return;
        }

        foreach (var companionPath in Directory.EnumerateFiles(typesDirectory, "*.godot.g.cs", SearchOption.TopDirectoryOnly))
        {
            var content = File.ReadAllText(companionPath);
            var updatedContent = content.Replace(
                $"namespace {DefaultGeneratedNamespace}",
                $"namespace {generatedNamespace}",
                StringComparison.Ordinal);

            if (!string.Equals(content, updatedContent, StringComparison.Ordinal))
            {
                File.WriteAllText(companionPath, updatedContent);
            }
        }
    }

    private string ResolvePath(string pathText)
    {
        if (Path.IsPathRooted(pathText))
        {
            return Path.GetFullPath(pathText);
        }

        return Path.GetFullPath(Path.Combine(_projectRoot, pathText));
    }

    private static bool IsSameOrDescendant(string candidatePath, string rootPath)
    {
        var normalizedCandidate = EnsureTrailingSeparator(Path.GetFullPath(candidatePath));
        var normalizedRoot = EnsureTrailingSeparator(Path.GetFullPath(rootPath));
        return normalizedCandidate.StartsWith(normalizedRoot, StringComparison.OrdinalIgnoreCase);
    }

    private static string EnsureTrailingSeparator(string path)
    {
        if (path.EndsWith(Path.DirectorySeparatorChar) || path.EndsWith(Path.AltDirectorySeparatorChar))
        {
            return path;
        }

        return path + Path.DirectorySeparatorChar;
    }

    private static void TryDeleteFile(string path)
    {
        try
        {
            if (File.Exists(path))
            {
                File.Delete(path);
            }
        }
        catch (IOException)
        {
        }
        catch (UnauthorizedAccessException)
        {
        }
    }

    private sealed class EditorCodegenFailureException : Exception
    {
        internal EditorCodegenFailureException(string statusMessage, string errorDetail)
            : base(statusMessage)
        {
            StatusMessage = statusMessage;
            ErrorDetail = errorDetail;
        }

        internal string StatusMessage { get; }

        internal string ErrorDetail { get; }
    }

    private readonly record struct DownloadedArtifact(byte[] Content, string Extension);

    private readonly record struct ProcessExecutionResult(int ExitCode, string Stdout, string Stderr);
}
#endif

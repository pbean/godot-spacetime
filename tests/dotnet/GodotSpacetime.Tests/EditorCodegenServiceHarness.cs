using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using GodotSpacetime.Editor.Codegen;
using Xunit;

namespace GodotSpacetime.Tests;

/// <summary>
/// Story 10.2 D3 — headless verification harness for the in-editor codegen path.
///
/// This drives the REAL <see cref="EditorCodegenService.GenerateBindingsAsync"/> C#
/// method (source-linked into this assembly under the TOOLS define — see
/// <c>GodotSpacetime.Tests.csproj</c>), closing the gap where the substantive logic
/// behind the editor "Generate from Server" button was only ever proved by a Python
/// replica (<c>tests/test_story_10_2_editor_codegen_integration.py</c>). The harness
/// covers the generation path; the ~30s human visual dock-render glance (Story 10.2
/// Task 7.5) remains the irreducible manual residual and is NOT closed here.
///
/// The live <see cref="Fact"/> is environment-gated and SKIPS (never fails) when the
/// <c>spacetime</c> CLI or a reachable local SpacetimeDB server is absent, mirroring the
/// <c>probe_spacetime_cli</c>/<c>probe_local_runtime</c> skip-gate semantics from
/// <c>tests/fixtures/spacetime_runtime.py</c>. The two safety-guardrail facts are pure
/// (no server) and always run.
///
/// Each fact maps to a row of the spec's I/O &amp; Edge-Case Matrix.
/// </summary>
public sealed class EditorCodegenServiceHarness
{
    private const string GeneratedNamespace = "Spacetime" + "DB.Types";
    private const string SchemaVersion = "9";

    // Resolve the repo root from the test assembly location: the test DLL lives under
    // tests/dotnet/GodotSpacetime.Tests/bin/<config>/<tfm>/, so the repo root is six
    // directories up. ProjectRoot is what EditorCodegenService treats as the safe
    // output-boundary anchor and as the cwd for the post-processor.
    private static string ProjectRoot { get; } = ResolveProjectRoot();

    [Fact]
    public async Task GenerateBindingsAsync_AgainstLiveServer_ProducesGodotBindings_MatchingCliModulePath()
    {
        // serverNickname is only needed inside ResolveLiveRuntimeOrSkip for the ping/list
        // probes; publish/delete below target the resolved URL via the isolated config.
        var (cliPath, _, serverHost) = ResolveLiveRuntimeOrSkip();

        var dashName = $"smoke-test-d3-{Guid.NewGuid():N}"[..("smoke-test-d3-".Length + 8)];
        var modulePath = Path.Combine(ProjectRoot, "spacetime", "modules", "smoke_test");

        // Harness output (the real C# service) and the parity baseline (direct CLI
        // --module-path). Both land under tests/fixtures/generated/d3-harness*, which is
        // inside the service's safe boundary; the finally-block deletes both trees so the
        // harness leaves no residue under the repo's `generated` boundary.
        var harnessOutDir = Path.Combine("tests", "fixtures", "generated", "d3-harness");
        var absHarnessOutDir = Path.Combine(ProjectRoot, harnessOutDir);
        var absCliOutDir = Path.Combine(ProjectRoot, "tests", "fixtures", "generated", "d3-harness-cli");

        // Per-run isolated CLI config. The minted-identity login below writes ONLY here,
        // never the user's ~/.config/spacetime/cli.toml. Declared before the try so the
        // finally can always remove it. (verified: `login` reports saving to this path.)
        var tempConfigDir = Path.Combine(Path.GetTempPath(), "d3-harness-cfg-" + Guid.NewGuid().ToString("N"));
        var tempConfig = Path.Combine(tempConfigDir, "cli.toml");

        try
        {
            // (1) Mint a fresh server identity+token (POST /v1/identity, no auth). The
            // harness OWNS this identity, so the finally can authenticate the cleanup
            // delete as the owner. An --anonymous publish instead yields an ephemeral
            // owner whose token is never surfaced, so a plain delete 401s (see Design Notes).
            var token = await TryMintTokenAsync(serverHost);
            if (token is null)
            {
                Assert.Skip("SpacetimeDB runtime unavailable: could not mint an identity token from POST /v1/identity");
            }

            // (2) Log that token into the ISOLATED config (never the user's global config).
            Directory.CreateDirectory(tempConfigDir);
            var login = await RunProcessAsync(
                cliPath,
                ["--config-path", tempConfig, "login", "--token", token!],
                ProjectRoot);
            if (login.ExitCode != 0)
            {
                Assert.Skip(
                    "SpacetimeDB runtime unavailable: isolated `login --token` failed: " +
                    Truncate((login.Stderr.Length > 0 ? login.Stderr : login.Stdout).Trim(), 240));
            }

            // (3) Publish the smoke_test module under a unique DASH name, OWNED by the
            // minted identity (no --anonymous). Dash name because the pinned 2.1.0
            // CLI/server reject underscores in DB names; --server takes the resolved URL
            // since the isolated config carries no nicknames (verified live — see Design Notes).
            var publish = await RunProcessAsync(
                cliPath,
                ["--config-path", tempConfig, "publish", "--server", serverHost, "--module-path", modulePath, "--yes", dashName],
                ProjectRoot);
            if (publish.ExitCode != 0)
            {
                Assert.Skip(
                    "SpacetimeDB runtime unavailable: smoke_test publish failed: " +
                    Truncate((publish.Stderr.Length > 0 ? publish.Stderr : publish.Stdout).Trim(), 240));
            }

            // (4) Drive the REAL production generation path. The schema GET stays
            // anonymous and returns 200 even for an owned DB (verified), so the service
            // is unchanged.
            var result = await new EditorCodegenService(ProjectRoot)
                .GenerateBindingsAsync(serverHost, dashName, harnessOutDir, GeneratedNamespace);

            // The local dev server is anonymous; an auth rejection means this lane cannot
            // be exercised here, so skip rather than fail (matrix row: 401/403).
            if (result.StatusMessage == "FAILED — server requires authentication")
            {
                Assert.Skip("SpacetimeDB runtime unavailable: anonymous schema access rejected");
            }

            // (5) Assert the production path succeeded with the OK status contract.
            Assert.True(
                result.IsSuccess,
                $"GenerateBindingsAsync did not succeed. Status: {result.StatusMessage}\nDetail: {result.ErrorDetail}");
            Assert.StartsWith("OK — bindings generated from ", result.StatusMessage);

            // (6) Assert .g.cs files exist under the out-dir.
            var harnessTree = HashTree(absHarnessOutDir);
            Assert.NotEmpty(harnessTree);
            Assert.Contains(harnessTree.Keys, path => path.EndsWith(".g.cs", StringComparison.Ordinal));

            // Byte-parity against a direct CLI --module-path + detect-godot-types.py run,
            // mirroring tests/test_story_10_2_editor_codegen_integration.py's parity
            // guarantee (the Story 10.2 definition of "generate correctly").
            await RunCliModulePathCodegenAsync(cliPath, modulePath, absCliOutDir);
            var cliTree = HashTree(absCliOutDir);
            Assert.Equal(cliTree, harnessTree);
        }
        finally
        {
            TryDeleteDirectory(absHarnessOutDir);
            TryDeleteDirectory(absCliOutDir);
            // Delete the published DB authenticating as its minted owner via the isolated
            // config, so successful runs don't accumulate orphaned databases on the
            // local/CI server. Best-effort and guarded (publish/login may not have run),
            // mirroring TryDeleteDirectory's swallow-on-failure contract.
            TryDeleteDatabase(cliPath, tempConfig, serverHost, dashName);
            // Remove the isolated config so no per-run auth state lingers on disk.
            TryDeleteDirectory(tempConfigDir);
        }
    }

    [Fact]
    public async Task GenerateBindingsAsync_OutputDirOutsideGeneratedBoundary_IsBlocked_AndWritesNothing()
    {
        // outputDir="src" is a rejected non-generated source directory; the service must
        // block before dispatching any subprocess (matrix row: output dir outside boundary).
        var absSrcDir = Path.Combine(ProjectRoot, "src");
        var existedBefore = Directory.Exists(absSrcDir);
        // Snapshot the contents, not just existence: `src` already exists in the repo, so an
        // existence-only check is trivially satisfied even if the service wrote files *into*
        // it. The matrix row demands "no stray writes", so compare the full file set before
        // and after to actually catch the harmful behavior the guardrail must prevent.
        var contentsBefore = SnapshotEntries(absSrcDir);

        var result = await new EditorCodegenService(ProjectRoot)
            .GenerateBindingsAsync("http://127.0.0.1:3000", "smoke-test-blocked", "src", GeneratedNamespace);

        Assert.False(result.IsSuccess);
        Assert.Equal("BLOCKED — output directory outside safe boundary", result.StatusMessage);
        // The block must not have created the rejected directory nor written anything into it.
        Assert.Equal(existedBefore, Directory.Exists(absSrcDir));
        Assert.Equal(contentsBefore, SnapshotEntries(absSrcDir));
    }

    [Fact]
    public async Task GenerateBindingsAsync_EmptyOutputDir_IsBlocked()
    {
        // An empty output dir is the degenerate boundary case and must also block.
        var result = await new EditorCodegenService(ProjectRoot)
            .GenerateBindingsAsync("http://127.0.0.1:3000", "smoke-test-blocked", "", GeneratedNamespace);

        Assert.False(result.IsSuccess);
        Assert.Equal("BLOCKED — output directory outside safe boundary", result.StatusMessage);
    }

    /// <summary>
    /// Resolve the live runtime (CLI + reachable server) or <see cref="Assert.Skip"/>
    /// with a reason naming the missing prerequisite, mirroring the Python probe pattern:
    /// CLI discoverable + runnable (`spacetime --version`), the chosen server nickname
    /// configured (`spacetime server list`), and online (`spacetime server ping` reports
    /// `Server is online: &lt;host&gt;`).
    /// </summary>
    private static (string CliPath, string ServerNickname, string ServerHost) ResolveLiveRuntimeOrSkip()
    {
        var cliPath = WhichSpacetime();
        if (cliPath is null)
        {
            Assert.Skip("spacetime CLI not available on PATH: spacetime not found on PATH");
        }

        var version = TryRunProcess(cliPath!, ["--version"], timeout: TimeSpan.FromSeconds(10));
        if (version is null || version.Value.ExitCode != 0)
        {
            Assert.Skip("spacetime CLI not available on PATH: spacetime --version did not succeed");
        }

        var server = Environment.GetEnvironmentVariable("SPACETIME_SERVER");
        if (string.IsNullOrWhiteSpace(server))
        {
            server = "local";
        }

        var list = TryRunProcess(cliPath!, ["server", "list"], timeout: TimeSpan.FromSeconds(10));
        if (list is null || list.Value.ExitCode != 0)
        {
            Assert.Skip("SpacetimeDB runtime unavailable: spacetime server list did not succeed");
        }

        if (!ServerNicknameConfigured(list!.Value.Stdout, server))
        {
            Assert.Skip($"SpacetimeDB runtime unavailable: spacetime CLI has no server nicknamed '{server}' configured");
        }

        var ping = TryRunProcess(cliPath!, ["server", "ping", server], timeout: TimeSpan.FromSeconds(10));
        if (ping is null || ping.Value.ExitCode != 0)
        {
            Assert.Skip($"SpacetimeDB runtime unavailable: server '{server}' not reachable");
        }

        var host = ParsePingHost(ping!.Value.Stdout);
        if (string.IsNullOrEmpty(host))
        {
            Assert.Skip($"SpacetimeDB runtime unavailable: spacetime server ping {server} did not report a host URL");
        }

        // The live lane post-processes generated bindings with `python3 detect-godot-types.py`
        // — both on the production-service side (EditorCodegenService) and in the direct-CLI
        // parity baseline below. The spec's Always-constraint requires skipping (never
        // failing) when python3 or detect-godot-types.py is unavailable, so gate them here
        // before the [Fact] proceeds. Without this probe a host missing only python3 would
        // surface a hard FAIL (Assert.True(result.IsSuccess) on the service's FAILED result)
        // or an uncaught Win32Exception ERROR (the parity branch's RunProcessAsync), both of
        // which violate the skip-not-fail contract.
        var python = TryRunProcess("python3", ["--version"], timeout: TimeSpan.FromSeconds(10));
        if (python is null || python.Value.ExitCode != 0)
        {
            Assert.Skip("SpacetimeDB runtime unavailable: python3 not available on PATH (required by detect-godot-types.py post-processing)");
        }

        var detectGodotTypesScript = Path.Combine(ProjectRoot, "scripts", "codegen", "detect-godot-types.py");
        if (!File.Exists(detectGodotTypesScript))
        {
            Assert.Skip($"SpacetimeDB runtime unavailable: codegen post-processor not found at {detectGodotTypesScript}");
        }

        return (cliPath!, server, host);
    }

    private async Task RunCliModulePathCodegenAsync(string cliPath, string modulePath, string absCliOutDir)
    {
        var generate = await RunProcessAsync(
            cliPath,
            [
                "generate",
                "--module-path", modulePath,
                "--lang", "csharp",
                "--out-dir", absCliOutDir,
                "--namespace", GeneratedNamespace,
                "-y",
            ],
            ProjectRoot,
            extraEnv: ("CARGO_NET_OFFLINE", "true")).ConfigureAwait(false);
        Assert.True(
            generate.ExitCode == 0,
            $"CLI --module-path generate failed.\nstdout:\n{generate.Stdout}\nstderr:\n{generate.Stderr}");

        var postProcess = await RunProcessAsync(
            "python3",
            [Path.Combine(ProjectRoot, "scripts", "codegen", "detect-godot-types.py"), Path.Combine(absCliOutDir, "Types")],
            ProjectRoot).ConfigureAwait(false);
        Assert.True(
            postProcess.ExitCode == 0,
            $"detect-godot-types.py failed.\nstdout:\n{postProcess.Stdout}\nstderr:\n{postProcess.Stderr}");
    }

    private static string ResolveProjectRoot()
    {
        // Walk up from the test assembly until we find the repo marker (the .sln file).
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "godot-spacetime.sln")))
            {
                return dir.FullName;
            }

            dir = dir.Parent;
        }

        throw new InvalidOperationException(
            "Could not locate the repo root (godot-spacetime.sln) from the test assembly location.");
    }

    private static string? WhichSpacetime()
    {
        var executable = OperatingSystem.IsWindows() ? "spacetime.exe" : "spacetime";
        var pathVar = Environment.GetEnvironmentVariable("PATH") ?? string.Empty;
        foreach (var segment in pathVar.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries))
        {
            var candidate = Path.Combine(segment, executable);
            if (File.Exists(candidate))
            {
                return candidate;
            }
        }

        return null;
    }

    private static bool ServerNicknameConfigured(string listStdout, string nickname)
    {
        foreach (var line in listStdout.Split('\n'))
        {
            var tokens = line.Split(new[] { ' ', '\t', '\r' }, StringSplitOptions.RemoveEmptyEntries);
            if (tokens.Contains(nickname))
            {
                return true;
            }
        }

        return false;
    }

    private static string ParsePingHost(string stdout)
    {
        const string marker = "Server is online:";
        foreach (var line in stdout.Split('\n'))
        {
            var stripped = line.Replace("\r", string.Empty).Trim();
            var idx = stripped.IndexOf(marker, StringComparison.Ordinal);
            if (idx != -1)
            {
                return stripped[(idx + marker.Length)..].Trim();
            }
        }

        return string.Empty;
    }

    private static IReadOnlyList<string> SnapshotEntries(string root)
    {
        if (!Directory.Exists(root))
        {
            return Array.Empty<string>();
        }

        var entries = Directory
            .EnumerateFileSystemEntries(root, "*", SearchOption.AllDirectories)
            .Select(entry => Path.GetRelativePath(root, entry).Replace(Path.DirectorySeparatorChar, '/'))
            .ToList();
        entries.Sort(StringComparer.Ordinal);
        return entries;
    }

    private static IReadOnlyDictionary<string, string> HashTree(string root)
    {
        var hashes = new SortedDictionary<string, string>(StringComparer.Ordinal);
        if (!Directory.Exists(root))
        {
            return hashes;
        }

        foreach (var file in Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories))
        {
            var relative = Path.GetRelativePath(root, file).Replace(Path.DirectorySeparatorChar, '/');
            hashes[relative] = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(file)));
        }

        return hashes;
    }

    private static async Task<ProcessResult> RunProcessAsync(
        string executable,
        IReadOnlyList<string> arguments,
        string workingDirectory,
        (string Key, string Value)? extraEnv = null)
    {
        var startInfo = new ProcessStartInfo
        {
            FileName = executable,
            WorkingDirectory = workingDirectory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };

        foreach (var argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        if (extraEnv is { } env)
        {
            startInfo.Environment[env.Key] = env.Value;
        }

        using var process = new Process { StartInfo = startInfo };
        process.Start();
        var stdoutTask = process.StandardOutput.ReadToEndAsync();
        var stderrTask = process.StandardError.ReadToEndAsync();
        await process.WaitForExitAsync().ConfigureAwait(false);

        return new ProcessResult(
            process.ExitCode,
            await stdoutTask.ConfigureAwait(false),
            await stderrTask.ConfigureAwait(false));
    }

    private static ProcessResult? TryRunProcess(string executable, IReadOnlyList<string> arguments, TimeSpan timeout)
    {
        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = executable,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
            };

            foreach (var argument in arguments)
            {
                startInfo.ArgumentList.Add(argument);
            }

            using var process = new Process { StartInfo = startInfo };
            process.Start();
            var stdout = process.StandardOutput.ReadToEndAsync();
            var stderr = process.StandardError.ReadToEndAsync();
            if (!process.WaitForExit((int)timeout.TotalMilliseconds))
            {
                try
                {
                    process.Kill(entireProcessTree: true);
                }
                catch (InvalidOperationException)
                {
                }

                // Observe the abandoned read tasks so a fault on the killed process'
                // redirected pipes does not resurface later as an UnobservedTaskException
                // in an unrelated test. The result is discarded — we are skipping anyway.
                ObserveAndIgnore(stdout);
                ObserveAndIgnore(stderr);

                return null;
            }

            return new ProcessResult(process.ExitCode, stdout.GetAwaiter().GetResult(), stderr.GetAwaiter().GetResult());
        }
        catch (Exception)
        {
            return null;
        }
    }

    private static void ObserveAndIgnore(Task task) =>
        task.ContinueWith(
            static t => { _ = t.Exception; },
            TaskContinuationOptions.OnlyOnFaulted | TaskContinuationOptions.ExecuteSynchronously);

    private static string Truncate(string value, int max) =>
        value.Length <= max ? value : value[..max];

    private static void TryDeleteDirectory(string path)
    {
        try
        {
            if (Directory.Exists(path))
            {
                Directory.Delete(path, recursive: true);
            }
        }
        catch (IOException)
        {
        }
        catch (UnauthorizedAccessException)
        {
        }
    }

    /// <summary>
    /// Best-effort, guarded deletion of the live-lane fixture database this run published,
    /// authenticating as its minted owner through the per-run isolated <paramref name="configPath"/>.
    /// Uses the pinned 2.1.0 CLI shape <c>spacetime --config-path &lt;cfg&gt; delete --server &lt;url&gt; --yes &lt;db&gt;</c>
    /// (<c>--yes</c> matches the publish call). Any failure, non-zero exit, or timeout is
    /// swallowed via <see cref="TryRunProcess"/> so cleanup never alters the test's
    /// skip/pass/fail outcome — deleting a never-published name is harmless.
    /// </summary>
    private static void TryDeleteDatabase(string cliPath, string configPath, string serverHost, string dashName)
    {
        _ = TryRunProcess(
            cliPath,
            ["--config-path", configPath, "delete", "--server", serverHost, "--yes", dashName],
            timeout: TimeSpan.FromSeconds(30));
    }

    /// <summary>
    /// Mint a fresh SpacetimeDB identity+token via an unauthenticated <c>POST /v1/identity</c>
    /// against <paramref name="serverHost"/>, returning the JWT <c>token</c> (the same pinned
    /// 2.1.0 contract <c>mint_anonymous_identity</c> uses in <c>tests/fixtures/spacetime_runtime.py</c>).
    /// Returns <see langword="null"/> on any failure so the caller can SKIP (never fail) when
    /// the runtime is unavailable.
    /// </summary>
    private static async Task<string?> TryMintTokenAsync(string serverHost)
    {
        try
        {
            using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(10) };
            // No request body — matches the reference contract (`mint_anonymous_identity`
            // in tests/fixtures/spacetime_runtime.py) and avoids sending a spurious
            // text/plain Content-Type. The pinned 2.1.0 server returns 200 for a no-body POST.
            using var response = await client
                .PostAsync(serverHost.TrimEnd('/') + "/v1/identity", content: null)
                .ConfigureAwait(false);
            if (!response.IsSuccessStatusCode)
            {
                return null;
            }

            var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            using var doc = JsonDocument.Parse(body);
            if (doc.RootElement.TryGetProperty("token", out var tokenElement) &&
                tokenElement.ValueKind == JsonValueKind.String)
            {
                var token = tokenElement.GetString();
                return string.IsNullOrWhiteSpace(token) ? null : token;
            }

            return null;
        }
        catch (Exception)
        {
            return null;
        }
    }

    private readonly record struct ProcessResult(int ExitCode, string Stdout, string Stderr);
}

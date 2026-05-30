using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading;
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

    // The dash-named fixture DB prefix (the pinned 2.1.0 CLI/server reject underscores). Shared
    // by dashName construction and the guid8 slice so the two can never drift apart.
    private const string DashNamePrefix = "smoke-test-d3-";

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

        var dashName = $"{DashNamePrefix}{Guid.NewGuid():N}"[..(DashNamePrefix.Length + 8)];
        var modulePath = Path.Combine(ProjectRoot, "spacetime", "modules", "smoke_test");

        // Harness output (the real C# service) and the parity baseline (direct CLI
        // --module-path). Both land under tests/fixtures/generated/d3-harness*, which is
        // inside the service's safe boundary; the finally-block deletes both trees so the
        // harness leaves no residue under the repo's `generated` boundary. The dirs carry
        // the SAME guid8 suffix as dashName, so two test processes against one checkout never
        // share a tree — that is what makes the HashTree-mid-delete race structurally
        // impossible (the fixed-dir version let a concurrent run's PrepareOutputDirectory
        // recursive-delete this run's tree mid-hash). .gitignore covers any residue from a
        // hard-killed run, since this `generated` tree is not otherwise ignored.
        var guid8 = dashName[DashNamePrefix.Length..];
        var harnessOutDir = Path.Combine("tests", "fixtures", "generated", $"d3-harness-{guid8}");
        var absHarnessOutDir = Path.Combine(ProjectRoot, harnessOutDir);
        var absCliOutDir = Path.Combine(ProjectRoot, "tests", "fixtures", "generated", $"d3-harness-cli-{guid8}");

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

    // ===== Server-independent guardrail facts for the harness's pure helpers =====
    // These pin the I/O matrix's pure rows and run on EVERY host (incl. non-runtime CI),
    // unlike the live [Fact] above which skips when the runtime is absent.

    // A real pinned-2.1.0 identity (64-hex) and an eyJ-prefixed two-dot JWT skeleton. `const`
    // so they can be concatenated inside [InlineData] (a constant-expression requirement).
    private const string Hex64 = "c20096dc305b6e28a60c9867ecbe8103c0555714da646919e92de9c546b46775";
    private const string JwtOk = "eyJ0eXAiOiJKV1Q.eyJoZXhfaWRl.bKFbd66orK4o";

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    [InlineData("0")]
    [InlineData("-5")]
    [InlineData("abc")]
    [InlineData("NaN")]
    [InlineData("Infinity")]
    public void ResolveDefaultTimeout_UnsetOrInvalid_FallsBackTo300(string? env)
    {
        Assert.Equal(TimeSpan.FromSeconds(300), ResolveDefaultTimeout(env));
    }

    [Fact]
    public void ResolveDefaultTimeout_PositiveValue_IsHonored()
    {
        Assert.Equal(TimeSpan.FromSeconds(600), ResolveDefaultTimeout("600"));
        Assert.Equal(TimeSpan.FromSeconds(45.5), ResolveDefaultTimeout("45.5"));
    }

    [Fact]
    public void ResolveDefaultTimeout_ExtremeValue_IsClampedNotOverflowed()
    {
        // Finite but huge: must NOT throw OverflowException; clamped to the 24h ceiling.
        Assert.Equal(TimeSpan.FromSeconds(24 * 60 * 60), ResolveDefaultTimeout("1e308"));
    }

    [Theory]
    [InlineData("error: failed to download `foo v1.0`\nCaused by:\n  attempting to make an HTTP request, but `--offline` was specified")]
    [InlineData("error: no matching package; the lock file needs updating but CARGO_NET_OFFLINE is set")]
    [InlineData("error: failed to get `foo`: the package is not in the local cache")]
    public void LooksLikeColdCargoOfflineFailure_OfflineSignatures_AreDetected(string output)
    {
        Assert.True(LooksLikeColdCargoOfflineFailure(output));
    }

    [Theory]
    [InlineData("")]
    [InlineData("error[E0425]: cannot find value `foo` in this scope")]
    [InlineData("thread 'main' panicked at src/lib.rs:10:5")]
    [InlineData("error: failed to download `foo v1.0` from registry: 503 Service Unavailable")] // online network failure — must NOT skip
    [InlineData("Caused by:\n  unable to update registry `crates-io` (connection reset)")]      // online registry hiccup — must NOT skip
    public void LooksLikeColdCargoOfflineFailure_RealErrorsAndEmpty_AreNotMatched(string output)
    {
        Assert.False(LooksLikeColdCargoOfflineFailure(output));
    }

    [Fact]
    public void ParseMintedToken_ValidPinnedShape_ReturnsToken()
    {
        var token = ParseMintedToken("{\"identity\":\"" + Hex64 + "\",\"token\":\"" + JwtOk + "\"}");
        Assert.Equal(JwtOk, token);
    }

    [Theory]
    [InlineData("not json at all")]                                                    // non-JSON body
    [InlineData("[1,2,3]")]                                                            // non-object root
    [InlineData("{\"identity\":\"" + Hex64 + "\"}")]                                   // missing token
    [InlineData("{\"identity\":\"" + Hex64 + "\",\"token\":\"\"}")]                    // empty token
    [InlineData("{\"identity\":\"" + Hex64 + "\",\"token\":12345}")]                   // non-string token
    [InlineData("{\"identity\":\"" + Hex64 + "\",\"token\":\"abc.def.ghi\"}")]         // not eyJ-prefixed
    [InlineData("{\"identity\":\"" + Hex64 + "\",\"token\":\"eyJ.onedot\"}")]          // wrong dot count (1)
    [InlineData("{\"identity\":\"" + Hex64 + "\",\"token\":\"eyJa.b.c.d\"}")]          // eyJ-prefix but 3 dots
    [InlineData("{\"identity\":\"tooshort\",\"token\":\"" + JwtOk + "\"}")]            // identity not 64 chars
    [InlineData("{\"identity\":\"zzzz96dc305b6e28a60c9867ecbe8103c0555714da646919e92de9c546b46775\",\"token\":\"" + JwtOk + "\"}")] // 64 chars but non-hex
    public void ParseMintedToken_ShapeDrift_ThrowsFailLoud(string body)
    {
        Assert.Throws<SpacetimeIdentityShapeException>(() => ParseMintedToken(body));
    }

    [Fact]
    public void TryDeleteDirectory_ExistingDirectory_IsRemoved()
    {
        var dir = Path.Combine(Path.GetTempPath(), "d3-harness-del-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Path.Combine(dir, "nested"));
        File.WriteAllText(Path.Combine(dir, "nested", "f.txt"), "x");

        TryDeleteDirectory(dir);

        Assert.False(Directory.Exists(dir));
    }

    [Fact]
    public void TryDeleteDirectory_NonexistentPath_IsSilentNoOp()
    {
        var dir = Path.Combine(Path.GetTempPath(), "d3-harness-absent-" + Guid.NewGuid().ToString("N"));
        Assert.Null(Record.Exception(() => TryDeleteDirectory(dir)));
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
        if (generate.ExitCode != 0)
        {
            // The parity baseline compiles the Rust module OFFLINE (CARGO_NET_OFFLINE=true),
            // reusing the cache the online `publish` above just warmed. On a cold-offline cache
            // cargo fails fast — an environment-setup condition, NOT a parity/codegen regression,
            // and asymmetric with the online publish (which would simply fetch). Skip that case;
            // any OTHER non-zero exit (a genuine generate/codegen regression) still fails loud.
            if (LooksLikeColdCargoOfflineFailure(generate.Stdout + "\n" + generate.Stderr))
            {
                Assert.Skip(
                    "SpacetimeDB runtime unavailable: parity `generate` hit a cold offline cargo cache " +
                    "(CARGO_NET_OFFLINE) — warm the cache or raise SPACETIME_D3_TIMEOUT_SECONDS; not a parity regression");
            }

            Assert.Fail(
                $"CLI --module-path generate failed.\nstdout:\n{generate.Stdout}\nstderr:\n{generate.Stderr}");
        }

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

    private const int DefaultTimeoutSeconds = 300;

    // Far above any legitimate cold-build threshold (the live lane completes in ~2s). Exists only
    // so an extreme env value can't overflow TimeSpan.FromSeconds into an uncaught OverflowException.
    private const double MaxTimeoutSeconds = 24 * 60 * 60;

    /// <summary>
    /// Resolve the live-lane subprocess "obviously hung" threshold. The default is
    /// <see cref="DefaultTimeoutSeconds"/>s; <c>SPACETIME_D3_TIMEOUT_SECONDS</c> may RAISE it
    /// (or otherwise tune it) for a host whose cold cargo cache makes a valid build legitimately
    /// slow. Unset / blank / non-numeric / non-positive / non-finite values fall back to the
    /// default — the env var can only make the lane more robust, never trip it on a bad value.
    /// </summary>
    private static TimeSpan ResolveDefaultTimeout(string? envSeconds)
    {
        if (!string.IsNullOrWhiteSpace(envSeconds) &&
            double.TryParse(envSeconds, NumberStyles.Float, CultureInfo.InvariantCulture, out var seconds) &&
            double.IsFinite(seconds) && seconds > 0)
        {
            // Clamp the upper end so an extreme value (e.g. "1e308") can't overflow
            // TimeSpan.FromSeconds into an uncaught OverflowException on a path with no try/catch.
            return TimeSpan.FromSeconds(Math.Min(seconds, MaxTimeoutSeconds));
        }

        return TimeSpan.FromSeconds(DefaultTimeoutSeconds);
    }

    /// <summary>
    /// True when subprocess output carries a cargo "offline mode could not satisfy a dependency"
    /// signature. Matched conservatively against cargo-offline-SPECIFIC tokens so a genuine
    /// compile/codegen error (the regression the parity gate exists to catch) is NOT misread as
    /// an environment-setup condition.
    /// </summary>
    private static bool LooksLikeColdCargoOfflineFailure(string output)
    {
        if (string.IsNullOrEmpty(output))
        {
            return false;
        }

        // Require an UNAMBIGUOUS offline-mode marker. Cargo's cold-offline cache-miss errors always
        // echo the flag ("…but `--offline` was specified" / "…because `--offline` was specified", or
        // the CARGO_NET_OFFLINE env), and "not in the local cache" is offline-cache-specific phrasing.
        // Bare tokens like "failed to download" / "unable to update registry" ALSO appear on ONLINE
        // network failures and on build-script fetches, so matching them alone would mis-skip a
        // genuine regression — exactly what this parity gate must instead fail loud on.
        var lowered = output.ToLowerInvariant();
        return lowered.Contains("--offline")
            || lowered.Contains("cargo_net_offline")
            || lowered.Contains("not in the local cache");
    }

    private static async Task<ProcessResult> RunProcessAsync(
        string executable,
        IReadOnlyList<string> arguments,
        string workingDirectory,
        (string Key, string Value)? extraEnv = null,
        TimeSpan? timeout = null)
    {
        // A generous "obviously hung" threshold: real login/publish/generate/post-process
        // complete well inside this, so tripping it means the subprocess is stuck. Bounding
        // here converts an indefinite hang — which the CI suite-level timeout would otherwise
        // report as a FAIL — into the intended Assert.Skip, uniformly for every live-lane call.
        // The default is env-tunable (SPACETIME_D3_TIMEOUT_SECONDS) so a host with a cold cargo
        // cache can RAISE the bound rather than have a valid-but-slow build false-trip the skip.
        var effectiveTimeout = timeout
            ?? ResolveDefaultTimeout(Environment.GetEnvironmentVariable("SPACETIME_D3_TIMEOUT_SECONDS"));

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
        try
        {
            process.Start();
        }
        catch (Exception ex) when (ex is Win32Exception or IOException)
        {
            // Executable missing or not runnable: an environment problem, not a test
            // failure — skip rather than surface an uncaught ERROR up the live lane.
            Assert.Skip($"SpacetimeDB runtime unavailable: could not start '{executable}': {ex.Message}");
            throw; // unreachable — Assert.Skip always throws; satisfies the compiler.
        }

        var stdoutTask = process.StandardOutput.ReadToEndAsync();
        var stderrTask = process.StandardError.ReadToEndAsync();

        using var cts = new CancellationTokenSource(effectiveTimeout);
        try
        {
            await process.WaitForExitAsync(cts.Token).ConfigureAwait(false);

            // Bound the pipe drain by the SAME deadline. A grandchild that inherited the
            // redirected stdout/stderr handles and outlives the direct child keeps the write
            // end open, so ReadToEndAsync would otherwise block past the timeout (WaitForExit
            // only waits on the direct child) and resurface as a suite-level FAIL — the exact
            // outcome this bound exists to convert into a skip.
            var stdout = await stdoutTask.WaitAsync(cts.Token).ConfigureAwait(false);
            var stderr = await stderrTask.WaitAsync(cts.Token).ConfigureAwait(false);
            return new ProcessResult(process.ExitCode, stdout, stderr);
        }
        catch (Exception outer) when (outer is OperationCanceledException or IOException)
        {
            // Two infrastructure faults land here, both meaning "the subprocess is not
            // behaving — skip, never FAIL": the timeout (OperationCanceledException from the
            // cts firing) and a broken redirected pipe (IOException re-raised by a read task).
            // Unlike TryRunProcess, this method has no outer catch-all net, so the cleanup
            // below must itself be fault-contained or a secondary throw would defeat the skip.
            try
            {
                process.Kill(entireProcessTree: true);
            }
            catch (Exception ex) when (ex is InvalidOperationException or Win32Exception or AggregateException)
            {
                // Kill is best-effort — an already-exited process or an OS-refused tree kill
                // must NOT turn the skip into a suite-level FAIL. (These are the documented
                // Process.Kill(bool) failure modes.) ObserveAndIgnore still runs below.
            }

            // Observe the abandoned read tasks so a fault on the killed process' redirected
            // pipes cannot resurface later as an UnobservedTaskException in an unrelated test
            // (mirrors the TryRunProcess timeout branch). Runs regardless of the kill outcome.
            ObserveAndIgnore(stdoutTask);
            ObserveAndIgnore(stderrTask);

            var reason = outer is OperationCanceledException
                ? $"did not exit within {effectiveTimeout.TotalSeconds:0}s (treated as a hung subprocess)"
                : $"its redirected output pipe faulted ({outer.GetType().Name}: {outer.Message})";
            Assert.Skip($"SpacetimeDB runtime unavailable: '{executable}' {reason}");
            throw; // unreachable — Assert.Skip always throws; satisfies the compiler.
        }
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
        catch (Exception)
        {
            // Best-effort cleanup in a finally block: swallow EVERYTHING (not just IO/UAE) so an
            // exotic exception (ArgumentException, SecurityException, a CLI-held handle surfacing
            // a different type) can never replace the test's real skip/pass/fail outcome. Mirrors
            // the blanket catch in the sibling TryRunProcess / TryMintTokenAsync helpers.
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
        var result = TryRunProcess(
            cliPath,
            ["--config-path", configPath, "delete", "--server", serverHost, "--yes", dashName],
            timeout: TimeSpan.FromSeconds(30));

        // Observability only. The delete stays best-effort (deleting a never-published name
        // is harmless) and this must never alter the test's skip/pass/fail outcome — but a
        // genuine failure here silently re-introduces the orphaned-DB accumulation this
        // cleanup exists to prevent, so emit exactly one diagnostic when it does not cleanly
        // succeed. Never throws.
        if (result is null || result.Value.ExitCode != 0)
        {
            var reason = result is null
                ? "no result (timed out, killed, or failed to start)"
                : $"exit {result.Value.ExitCode}: " +
                  Truncate((result.Value.Stderr.Length > 0 ? result.Value.Stderr : result.Value.Stdout).Trim(), 240);
            Console.Error.WriteLine(
                $"[d3-harness] best-effort cleanup could not delete fixture DB '{dashName}': {reason}");
        }
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
                // Runtime unavailable / non-2xx: SKIP (the caller treats null as skip), mirroring
                // the Python reference's transient RuntimeError path.
                return null;
            }

            var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            // A 2xx body whose shape drifts from the pinned 2.1.0 contract is a real regression,
            // so ParseMintedToken THROWS SpacetimeIdentityShapeException — the one exception the
            // outer catch deliberately lets escape (fail loud, never silently skip a drift).
            return ParseMintedToken(body);
        }
        catch (Exception ex) when (ex is not SpacetimeIdentityShapeException)
        {
            // Any transient fault (network, timeout, IO, malformed URI) means the runtime is
            // unavailable → SKIP. A SpacetimeIdentityShapeException is NOT caught here: it signals
            // a 2xx-but-drifted contract and must fail loud per CLAUDE.md "measure the pinned runtime".
            return null;
        }
    }

    /// <summary>
    /// Validate a 2xx <c>POST /v1/identity</c> body against the pinned spacetime 2.1.0 contract
    /// and return the JWT <c>token</c>. Mirrors the canaries in <c>mint_anonymous_identity</c>
    /// (tests/fixtures/spacetime_runtime.py): <c>token</c> is an <c>eyJ</c>-prefixed JWT with
    /// exactly two dots (header.payload.signature) and <c>identity</c> is a 64-char hex string.
    /// Throws <see cref="SpacetimeIdentityShapeException"/> on any drift — a successful response
    /// with the wrong shape is a contract regression that must fail loud, not skip.
    /// </summary>
    private static string ParseMintedToken(string body)
    {
        JsonElement root;
        try
        {
            using var doc = JsonDocument.Parse(body);
            root = doc.RootElement.Clone();
        }
        catch (JsonException ex)
        {
            throw new SpacetimeIdentityShapeException(
                $"POST /v1/identity returned a non-JSON body: {Truncate(body, 120)}", ex);
        }

        if (root.ValueKind != JsonValueKind.Object ||
            !root.TryGetProperty("token", out var tokenElement) ||
            tokenElement.ValueKind != JsonValueKind.String)
        {
            throw new SpacetimeIdentityShapeException(
                "POST /v1/identity response drifted from pinned 2.1.0: missing string 'token'");
        }

        var token = tokenElement.GetString();
        if (string.IsNullOrWhiteSpace(token))
        {
            throw new SpacetimeIdentityShapeException("POST /v1/identity returned an empty 'token'");
        }

        // JWT shape canary: pinned 2.1.0 emits an ES256 JWT — eyJ-prefix + exactly two dots.
        if (!token.StartsWith("eyJ", StringComparison.Ordinal) || token.Count(c => c == '.') != 2)
        {
            throw new SpacetimeIdentityShapeException(
                $"POST /v1/identity 'token' is not a pinned-2.1.0 JWT (eyJ-prefix + two dots); " +
                $"prefix={Truncate(token, 8)}, dots={token.Count(c => c == '.')}");
        }

        if (!root.TryGetProperty("identity", out var identityElement) ||
            identityElement.ValueKind != JsonValueKind.String)
        {
            throw new SpacetimeIdentityShapeException(
                "POST /v1/identity response drifted from pinned 2.1.0: missing string 'identity'");
        }

        if (!IsSixtyFourHex(identityElement.GetString()?.Trim()))
        {
            throw new SpacetimeIdentityShapeException(
                "POST /v1/identity 'identity' is not a pinned-2.1.0 64-char hex string");
        }

        return token!;
    }

    private static bool IsSixtyFourHex(string? value)
    {
        if (value is null || value.Length != 64)
        {
            return false;
        }

        foreach (var c in value)
        {
            if (c is not (>= '0' and <= '9' or >= 'a' and <= 'f' or >= 'A' and <= 'F'))
            {
                return false;
            }
        }

        return true;
    }

    /// <summary>
    /// A 2xx <c>POST /v1/identity</c> response whose token/identity shape drifted from the pinned
    /// spacetime 2.1.0 contract — a fail-loud regression signal, NOT a runtime-unavailable skip.
    /// Mirrors <c>SpacetimeIdentityShapeError</c> in tests/fixtures/spacetime_runtime.py.
    /// </summary>
    private sealed class SpacetimeIdentityShapeException : Exception
    {
        public SpacetimeIdentityShapeException(string message)
            : base(message)
        {
        }

        public SpacetimeIdentityShapeException(string message, Exception inner)
            : base(message, inner)
        {
        }
    }

    private readonly record struct ProcessResult(int ExitCode, string Stdout, string Stderr);
}

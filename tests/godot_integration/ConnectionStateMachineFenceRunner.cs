using System;
using System.Collections.Generic;
using System.Text.Json;
using Godot;
using GodotSpacetime.Connection;
using GodotSpacetime.Runtime.Connection;

namespace GodotSpacetime.IntegrationTests;

// In-engine behavioral proof for the volatile-fence-backed
// ConnectionStateMachine.CurrentStatus. This MUST run inside the Godot runtime
// (godot-mono --headless) and CANNOT run in the plain xUnit GodotSpacetime.Tests
// host: CurrentStatus is a ConnectionStatus, which derives from Godot.RefCounted;
// constructing a RefCounted subclass without the engine bootstrap hard-crashes
// the process (SIGSEGV / exit 139) because GodotSharp's native interop pointers
// are null. Driven by tests/test_connection_state_machine_fence.py, which probes
// for godot-mono and skips when it is absent. Emits one "E2E-EVENT <json>" line
// per assertion plus a terminal done event, matching the repo's other
// godot_integration runners.
public partial class ConnectionStateMachineFenceRunner : Node
{
    private bool _allPassed = true;

    public override void _Ready()
    {
        try
        {
            // AC: a freshly constructed machine reports Disconnected before any Transition.
            var machine = new ConnectionStateMachine();
            var initial = machine.CurrentStatus;
            Check(
                "initial_status_disconnected",
                initial != null && initial.State == ConnectionState.Disconnected,
                new Dictionary<string, object?> { ["state"] = initial?.State.ToString() });

            // AC: StateChanged fires with the post-transition status each time, and the
            // getter round-trips each new state in order through the fenced field.
            var observed = new List<ConnectionStatus>();
            machine.StateChanged += status => observed.Add(status);

            machine.Transition(ConnectionState.Connecting, "CONNECTING — fence test");
            var afterConnecting = machine.CurrentStatus;
            Check(
                "transition_connecting_round_trips",
                afterConnecting != null
                    && afterConnecting.State == ConnectionState.Connecting
                    && !ReferenceEquals(afterConnecting, initial),
                new Dictionary<string, object?>
                {
                    ["state"] = afterConnecting?.State.ToString(),
                    ["new_reference"] = !ReferenceEquals(afterConnecting, initial),
                });

            machine.Transition(ConnectionState.Connected, "CONNECTED — fence test");
            var afterConnected = machine.CurrentStatus;
            Check(
                "transition_connected_round_trips",
                afterConnected != null && afterConnected.State == ConnectionState.Connected,
                new Dictionary<string, object?> { ["state"] = afterConnected?.State.ToString() });

            Check(
                "state_changed_fired_with_post_transition_status",
                observed.Count == 2
                    && observed[0].State == ConnectionState.Connecting
                    && observed[1].State == ConnectionState.Connected
                    && ReferenceEquals(observed[1], afterConnected),
                new Dictionary<string, object?>
                {
                    ["count"] = observed.Count,
                    ["payload_matches_current"] =
                        observed.Count == 2 && ReferenceEquals(observed[1], afterConnected),
                });

            // AC: an illegal transition (Disconnected -> Connected) throws
            // InvalidOperationException and leaves CurrentStatus unchanged.
            var illegalMachine = new ConnectionStateMachine();
            var before = illegalMachine.CurrentStatus;
            var threw = false;
            try
            {
                illegalMachine.Transition(ConnectionState.Connected, "CONNECTED — illegal");
            }
            catch (InvalidOperationException)
            {
                threw = true;
            }
            Check(
                "illegal_transition_throws_and_status_unchanged",
                threw && ReferenceEquals(illegalMachine.CurrentStatus, before),
                new Dictionary<string, object?>
                {
                    ["threw"] = threw,
                    ["status_unchanged"] = ReferenceEquals(illegalMachine.CurrentStatus, before),
                });
        }
        catch (Exception ex)
        {
            _allPassed = false;
            WriteJsonLine(new Dictionary<string, object?>
            {
                ["event"] = "step",
                ["name"] = "bootstrap",
                ["status"] = "error",
                ["reason"] = ex.GetType().Name + ": " + ex.Message,
            });
        }

        WriteJsonLine(new Dictionary<string, object?>
        {
            ["event"] = "done",
            ["status"] = _allPassed ? "pass" : "fail",
        });

        var tree = GetTree();
        var code = _allPassed ? 0 : 1;
        if (tree != null)
        {
            tree.Quit(code);
        }
        else
        {
            System.Environment.Exit(code);
        }
    }

    private void Check(string name, bool ok, Dictionary<string, object?>? extra)
    {
        if (!ok)
        {
            _allPassed = false;
        }

        var payload = new Dictionary<string, object?>
        {
            ["event"] = "step",
            ["name"] = name,
            ["status"] = ok ? "ok" : "error",
        };
        if (extra != null)
        {
            foreach (var kv in extra)
            {
                payload[kv.Key] = kv.Value;
            }
        }
        WriteJsonLine(payload);
    }

    private static void WriteJsonLine(object payload)
    {
        try
        {
            Console.WriteLine("E2E-EVENT " + JsonSerializer.Serialize(payload));
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(
                "ConnectionStateMachineFenceRunner: failed to serialize event: " + ex.Message);
        }
    }
}

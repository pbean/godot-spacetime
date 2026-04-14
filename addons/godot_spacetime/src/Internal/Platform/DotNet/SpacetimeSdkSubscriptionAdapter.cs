using SpacetimeDB;

namespace GodotSpacetime.Runtime.Platform.DotNet;

/// <summary>
/// Adapter for the SpacetimeDB .NET ClientSDK subscription layer.
///
/// This class is the ONLY location in the codebase where <c>SpacetimeDB.ClientSDK</c>
/// subscription types may be referenced directly. All higher-level internal services
/// and all public SDK surfaces depend on the <c>GodotSpacetime.*</c> contracts rather
/// than on <c>SpacetimeDB.*</c> types.
///
/// See <c>docs/runtime-boundaries.md</c> — "Internal/Platform/DotNet/ — The Runtime
/// Isolation Zone" for the architectural justification.
///
/// Runtime implementation (subscription builder wiring, applied event forwarding, etc.)
/// is added in Story 1.9.
/// </summary>
internal sealed class SpacetimeSdkSubscriptionAdapter
{
    // Stub — references IDbConnection to establish the isolation boundary.
    // Subscription management implementation is added in later stories.
    private IDbConnection? _dbConnection;
}

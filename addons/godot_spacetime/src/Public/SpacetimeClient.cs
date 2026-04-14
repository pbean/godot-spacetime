using Godot;

namespace GodotSpacetime;

/// <summary>
/// The top-level Godot-facing service boundary for the GodotSpacetime SDK.
///
/// Register this Node as an autoload in your <c>project.godot</c> to make it available
/// from any scene. Configure it with a <see cref="SpacetimeSettings"/> resource to point
/// it at your SpacetimeDB instance.
///
/// Concept vocabulary for all public SDK types is defined in
/// <c>docs/runtime-boundaries.md</c>. The intended workflow is:
/// <list type="bullet">
///   <item>Configure <see cref="SpacetimeSettings"/> (Host, Database)</item>
///   <item>Call Connect() — watch ConnectionState events for lifecycle transitions</item>
///   <item>Apply subscriptions — receive SubscriptionAppliedEvent when cache is ready</item>
///   <item>Read cache via generated bindings — invoke reducers as needed</item>
/// </list>
///
/// This stub establishes the type name and autoload contract.
/// Runtime behavior is added in Stories 1.6+.
/// </summary>
public partial class SpacetimeClient : Node
{
}

# Test Automation Summary — Story 3.3

## Gap-fill tests added to `tests/test_story_3_3_observe_row_level_changes.py`

### RowChangedEvent.cs — readonly properties and nullable types
- [x] `test_row_changed_event_table_name_is_get_only_property` — `TableName { get; }` has no setter
- [x] `test_row_changed_event_old_row_is_nullable_object` — `object? OldRow` declared as nullable
- [x] `test_row_changed_event_new_row_is_nullable_object` — `object? NewRow` declared as nullable

### SpacetimeSdkRowCallbackAdapter.cs — imports, guards, and helpers
- [x] `test_row_callback_adapter_imports_system_reflection` — `using System.Reflection;` present
- [x] `test_row_callback_adapter_imports_linq_expressions` — `using System.Linq.Expressions;` present
- [x] `test_row_callback_adapter_null_guards_arguments` — `ArgumentNullException.ThrowIfNull` guards
- [x] `test_row_callback_adapter_uses_public_instance_binding_flags` — `BindingFlags.Public | BindingFlags.Instance`
- [x] `test_row_callback_adapter_reads_public_fields_from_remote_tables` — `GetFields(BindingFlags.Public | BindingFlags.Instance)` present for generated field-backed table handles
- [x] `test_row_callback_adapter_keeps_property_support_for_future_generator_shapes` — `GetProperties(BindingFlags.Public | BindingFlags.Instance)` retained as forward-compatible support
- [x] `test_row_callback_adapter_tracks_registered_db_instances_to_avoid_duplicate_wiring` — `ConditionalWeakTable<object, RegistrationMarker>` tracks already-wired db objects
- [x] `test_row_callback_adapter_short_circuits_when_same_db_is_registered_twice` — duplicate registration guard present
- [x] `test_row_callback_adapter_dedupes_handles_seen_via_fields_and_properties` — `ReferenceEqualityComparer.Instance` prevents double-wiring the same handle through multiple member shapes
- [x] `test_row_callback_adapter_has_try_wire_update_event_helper` — `TryWireUpdateEvent` helper exists
- [x] `test_row_callback_adapter_has_try_wire_row_event_helper` — `TryWireRowEvent` helper exists
- [x] `test_row_callback_adapter_register_callbacks_is_internal_method` — `internal void RegisterCallbacks`

### Generated bindings sample — RemoteTables shape sanity checks
- [x] `test_demo_generated_remote_tables_exposes_table_handles_as_public_fields` — sample generated bindings use public field-backed table handles
- [x] `test_demo_generated_db_connection_exposes_db_as_single_property_instance` — sample generated `DbConnection` exposes a stable `Db` property

### SpacetimeConnectionService.cs — invocation semantics
- [x] `test_connection_service_calls_register_callbacks_on_adapter_field` — `_rowCallbackAdapter.RegisterCallbacks`
- [x] `test_connection_service_calls_register_callbacks_with_this_as_sink` — `RegisterCallbacks(db, this)`
- [x] `test_connection_service_invokes_on_row_changed_event` — `OnRowChanged?.Invoke` pattern
- [x] `test_connection_service_insert_sets_null_old_row_and_row_as_new_row` — `RowChangeType.Insert, null, row`
- [x] `test_connection_service_delete_sets_row_as_old_row_and_null_new_row` — `RowChangeType.Delete, row, null`
- [x] `test_connection_service_update_passes_old_row_then_new_row` — `RowChangeType.Update, oldRow, newRow`

### SpacetimeClient.cs — delegate signature and thread-safe dispatch
- [x] `test_spacetime_client_row_changed_delegate_accepts_row_changed_event_param` — `RowChangedEventHandler(RowChangedEvent`
- [x] `test_spacetime_client_handle_row_changed_uses_signal_adapter_dispatch` — `_signalAdapter.Dispatch`

### docs/runtime-boundaries.md — section content and code examples
- [x] `test_runtime_boundaries_has_observing_live_cache_updates_section` — section heading present
- [x] `test_runtime_boundaries_has_row_changed_subscription_example` — `RowChanged +=` example
- [x] `test_runtime_boundaries_has_switch_on_change_type_example` — `switch (e.ChangeType)` example
- [x] `test_runtime_boundaries_documents_null_for_insert_old_row` — null semantics for Insert documented
- [x] `test_runtime_boundaries_documents_null_for_delete_new_row` — null semantics for Delete documented

## Coverage

| Component | Before | After | New |
|-----------|--------|-------|-----|
| RowChangeType.cs | 7 | 7 | 0 |
| RowChangedEvent.cs | 10 | 13 | +3 |
| SpacetimeSdkRowCallbackAdapter.cs | 14 | 26 | +12 |
| Generated bindings sample | 0 | 2 | +2 |
| SpacetimeConnectionService.cs | 13 | 19 | +6 |
| SpacetimeClient.cs | 7 | 9 | +2 |
| docs/runtime-boundaries.md | 9 | 14 | +5 |
| Regression guards | 27 | 27 | 0 |
| **Total** | **87** | **117** | **+30** |

## Results

```
948 passed  (full suite — zero regressions)
117 passed  (story 3.3 file only)
```

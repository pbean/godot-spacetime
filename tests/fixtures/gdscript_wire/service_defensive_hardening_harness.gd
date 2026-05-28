extends SceneTree

const ServiceScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd")
const SubscriptionHandleScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_subscription_handle.gd")


class DummyRegistry:
	extends RefCounted

	var handles_by_id: Dictionary = {}
	var handles_by_query_set_id: Dictionary = {}

	func try_get_handle(handle_id: int) -> Object:
		return handles_by_id.get(handle_id)

	func find_by_query_set_id(query_set_id: int) -> Object:
		for handle in handles_by_id.values():
			if handle != null and int(handle.query_set_id) == query_set_id:
				return handle
		return handles_by_query_set_id.get(query_set_id)

	func register(handle: Object) -> void:
		if handle == null:
			return
		handles_by_id[int(handle.handle_id)] = handle
		handles_by_query_set_id[int(handle.query_set_id)] = handle

	func unregister(handle_id: int) -> Dictionary:
		if not handles_by_id.has(handle_id):
			return {}
		var handle = handles_by_id[handle_id]
		handles_by_id.erase(handle_id)
		if handle != null:
			handles_by_query_set_id.erase(int(handle.query_set_id))
		return {
			"handle": handle,
		}

	func clear() -> void:
		for handle in handles_by_id.values():
			if handle != null and handle.has_method("close"):
				handle.close()
		handles_by_id.clear()
		handles_by_query_set_id.clear()


class DummyReconnectPolicy:
	extends RefCounted

	var max_attempts: int = 3

	func try_begin_retry() -> Dictionary:
		return {
			"ok": true,
			"attempt_number": 1,
			"delay_seconds": 0.25,
		}

	func reset() -> void:
		pass


class DummyCacheStore:
	extends RefCounted

	var applied_query_set_ids: Array = []

	func build_snapshot(query_rows: Array) -> Dictionary:
		return {
			"query_rows": query_rows,
		}

	func commit_snapshot(_snapshot: Dictionary) -> Array:
		return []

	func apply_transaction_updates(query_set_updates: Array) -> Array:
		for query_set_update_variant in query_set_updates:
			var query_set_update: Dictionary = query_set_update_variant
			applied_query_set_ids.append(query_set_update.get("query_set_id"))
		return []

	func clear() -> void:
		applied_query_set_ids.clear()


var _row_changed_events: Array = []
var _reducer_success_events: Array = []
var _reducer_failure_events: Array = []
var _subscription_failed_events: Array = []
var _reentrant_unsubscribe_count: int = 0
var _reentrant_subscribe_handler_fired: bool = false
var _reentrant_subscribe_returned_null: bool = false
var _reentrant_subscribe_pending_delta: int = 0
var _reentrant_subscribe_armed: bool = true
var _reentrant_subscribe_attempt_count: int = 0
var _reentrant_replace_armed: bool = true
var _reentrant_replace_handler_fired: bool = false
var _reentrant_replace_returned_null: bool = false
# Sentinel `true`: a deferred `subscription_failed` handler overwrites it with the
# reentrance-guard value it observes, which must be `false` (teardown completed
# and the guard was restored before any handler ran).
var _guard_seen_inside_handler: bool = true


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 1:
		_emit_error("missing mode argument")
		quit(2)
		return

	match String(args[0]):
		"transaction_update_non_numeric_id":
			_run_transaction_update_non_numeric_id()
		"reducer_result_non_numeric_id":
			_run_reducer_result_non_numeric_id()
		"authoritative_negative_query_set_id":
			_run_authoritative_negative_query_set_id()
		"malformed_bundle_warning_storm_cap":
			_run_malformed_bundle_warning_storm_cap()
		"bundle_truncation_cap_transaction_update":
			_run_bundle_truncation_cap_transaction_update()
		"bundle_truncation_cap_reducer_result":
			_run_bundle_truncation_cap_reducer_result()
		"bundle_at_cap_emits_no_warning":
			_run_bundle_at_cap_emits_no_warning()
		"reserve_request_id_wraps_forces_disconnect":
			_run_reserve_request_id_wraps_forces_disconnect()
		"unsubscribe_null_socket_does_not_burn_request_id":
			_run_unsubscribe_null_socket_does_not_burn_request_id()
		"unsubscribe_send_failure_does_not_record_pending":
			_run_unsubscribe_send_failure_does_not_record_pending()
		"unsubscribe_applied_erases_pending_entry":
			_run_unsubscribe_applied_erases_pending_entry()
		"reset_subscription_runtime_emits_synthetic_failure":
			_run_reset_subscription_runtime_emits_synthetic_failure()
		"reset_subscription_runtime_fails_pending_replacement_old_handle":
			_run_reset_subscription_runtime_fails_pending_replacement_old_handle()
		"reset_subscription_runtime_missing_old_handle_does_not_crash":
			_run_reset_subscription_runtime_missing_old_handle_does_not_crash()
		"reset_subscription_runtime_dedupes_duplicate_replacement_old_handles":
			_run_reset_subscription_runtime_dedupes_duplicate_replacement_old_handles()
		"reset_subscription_runtime_reentrant_old_failure_still_fails_new_handle":
			_run_reset_subscription_runtime_reentrant_old_failure_still_fails_new_handle()
		"reset_subscription_runtime_shares_single_failed_at_unix_time":
			_run_reset_subscription_runtime_shares_single_failed_at_unix_time()
		"subscribe_rejected_while_degraded_adds_no_pending":
			_run_subscribe_rejected_while_degraded_adds_no_pending()
		"reentrant_subscribe_during_teardown_rejected":
			_run_reentrant_subscribe_during_teardown_rejected()
		"retry_teardown_resets_subscription_runtime":
			_run_retry_teardown_resets_subscription_runtime()
		"reducer_result_non_integer_request_id":
			_run_reducer_result_non_integer_request_id()
		"request_id_persists_across_reset":
			_run_request_id_persists_across_reset()
		"subscribe_applied_rebinds_query_set_id":
			_run_subscribe_applied_rebinds_query_set_id()
		"reset_subscription_runtime_survives_malformed_pending_entry":
			_run_reset_subscription_runtime_survives_malformed_pending_entry()
		"replace_subscription_rejected_during_disconnect_teardown":
			_run_replace_subscription_rejected_during_disconnect_teardown()
		"replace_subscription_rejected_while_degraded":
			_run_replace_subscription_rejected_while_degraded()
		"reset_subscription_runtime_handler_runs_after_guard_cleared":
			_run_reset_subscription_runtime_handler_runs_after_guard_cleared()
		_:
			_emit_error("unknown mode: %s" % args[0])
			quit(2)


func _new_service_context() -> Dictionary:
	var service = ServiceScript.new()
	var registry = DummyRegistry.new()
	var cache = DummyCacheStore.new()
	service._subscription_registry = registry
	service._cache_store = cache
	service.row_changed.connect(_on_row_changed)
	service.reducer_call_succeeded.connect(_on_reducer_succeeded)
	service.reducer_call_failed.connect(_on_reducer_failed)
	service.subscription_failed.connect(_on_subscription_failed)
	return {
		"service": service,
		"registry": registry,
		"cache": cache,
	}


func _reset_events() -> void:
	_row_changed_events.clear()
	_reducer_success_events.clear()
	_reducer_failure_events.clear()
	_subscription_failed_events.clear()
	_reentrant_unsubscribe_count = 0
	_reentrant_subscribe_handler_fired = false
	_reentrant_subscribe_returned_null = false
	_reentrant_subscribe_pending_delta = 0
	_reentrant_subscribe_armed = true
	_reentrant_subscribe_attempt_count = 0
	_reentrant_replace_armed = true
	_reentrant_replace_handler_fired = false
	_reentrant_replace_returned_null = false


func _run_transaction_update_non_numeric_id() -> void:
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	var cache = ctx["cache"]
	var authoritative_handle = SubscriptionHandleScript.new(1, 0, 0)
	registry.handles_by_id[1] = authoritative_handle
	registry.handles_by_query_set_id[0] = authoritative_handle
	service._authoritative_handle_id = 1
	service._handle_transaction_update({
		"query_sets": [
			{
				"query_set_id": "abc",
				"tables": [],
			},
		],
	})
	_emit_result({
		"applied_query_set_ids": _jsonify(cache.applied_query_set_ids),
		"row_changed_events": _jsonify(_row_changed_events),
	})
	quit(0)


func _run_reducer_result_non_numeric_id() -> void:
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	var cache = ctx["cache"]
	var authoritative_handle = SubscriptionHandleScript.new(1, 5, 5)
	registry.handles_by_id[1] = authoritative_handle
	registry.handles_by_query_set_id[5] = authoritative_handle
	service._authoritative_handle_id = 1
	service._pending_reducer_calls[7] = {
		"invocation_id": "inv-7",
		"reducer_name": "ping",
		"called_at": 1.0,
	}
	service._handle_reducer_result({
		"request_id": 7,
		"status": "Committed",
		"query_sets": [
			{
				"query_set_id": "abc",
				"tables": [],
			},
			{
				"query_set_id": 5,
				"tables": [],
			},
		],
	})
	_emit_result({
		"applied_query_set_ids": _jsonify(cache.applied_query_set_ids),
		"row_changed_events": _jsonify(_row_changed_events),
		"success_events": _jsonify(_reducer_success_events),
		"failure_events": _jsonify(_reducer_failure_events),
	})
	quit(0)


func _run_authoritative_negative_query_set_id() -> void:
	# Stale / future-refactored sentinel case: a registered handle whose
	# `query_set_id` is `-1`. A naive `qs_id == int(authoritative_handle.query_set_id)`
	# comparison with a bundled entry whose `query_set_id` was also `-1` (e.g.
	# a malformed server frame that defaulted to `-1` via `get(..., -1)`) would
	# false-match; the authoritative-side guard must short-circuit before any
	# bundled-entry comparison runs.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	var cache = ctx["cache"]
	var authoritative_handle = SubscriptionHandleScript.new(1, -1, -1)
	registry.handles_by_id[1] = authoritative_handle
	registry.handles_by_query_set_id[-1] = authoritative_handle
	service._authoritative_handle_id = 1
	service._handle_transaction_update({
		"query_sets": [
			{
				"query_set_id": 0,
				"tables": [],
			},
		],
	})
	_emit_result({
		"applied_query_set_ids": _jsonify(cache.applied_query_set_ids),
		"row_changed_events": _jsonify(_row_changed_events),
	})
	quit(0)


func _run_malformed_bundle_warning_storm_cap() -> void:
	# Five mixed-malformed entries (2 non-Dictionary, 2 missing `query_set_id`,
	# 1 non-integer `query_set_id`) plus one valid entry for the authoritative
	# handle. The post-round behaviour: exactly one summary `push_warning`
	# naming the count "5"; no per-entry warnings for the three malformed
	# categories. The valid entry still reaches the cache.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	var cache = ctx["cache"]
	var authoritative_handle = SubscriptionHandleScript.new(1, 42, 42)
	registry.handles_by_id[1] = authoritative_handle
	registry.handles_by_query_set_id[42] = authoritative_handle
	service._authoritative_handle_id = 1
	service._handle_transaction_update({
		"query_sets": [
			"not-a-dict",                             # non-Dictionary #1
			12345,                                    # non-Dictionary #2
			{"tables": []},                           # missing query_set_id #1
			{"tables": [], "other": "field"},         # missing query_set_id #2
			{"query_set_id": "abc", "tables": []},    # non-integer #1
			{"query_set_id": 42, "tables": []},       # valid, matches authoritative
		],
	})
	_emit_result({
		"applied_query_set_ids": _jsonify(cache.applied_query_set_ids),
		"row_changed_events": _jsonify(_row_changed_events),
	})
	quit(0)


func _run_bundle_truncation_cap_transaction_update() -> void:
	# Send `MAX_BUNDLED_QUERY_SETS + 100` entries — all matching the
	# authoritative handle so they would ALL be applied absent the cap. The
	# truncation must process exactly the first MAX_BUNDLED_QUERY_SETS entries
	# and emit exactly one summary warning containing `"Clamping"`.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	var cache = ctx["cache"]
	var authoritative_handle = SubscriptionHandleScript.new(1, 77, 77)
	registry.handles_by_id[1] = authoritative_handle
	registry.handles_by_query_set_id[77] = authoritative_handle
	service._authoritative_handle_id = 1
	var overflow: int = 100
	var total_entries: int = ServiceScript.MAX_BUNDLED_QUERY_SETS + overflow
	var query_sets: Array = []
	query_sets.resize(total_entries)
	for i in range(total_entries):
		query_sets[i] = {
			"query_set_id": 77,
			"tables": [],
			"tick": i,
		}
	service._handle_transaction_update({
		"query_sets": query_sets,
	})
	_emit_result({
		"total_entries": total_entries,
		"cap": ServiceScript.MAX_BUNDLED_QUERY_SETS,
		"overflow": overflow,
		"applied_count": cache.applied_query_set_ids.size(),
	})
	quit(0)


func _run_bundle_truncation_cap_reducer_result() -> void:
	# Same truncation contract on the ReducerResult path. Register one handle so
	# every capped entry applies through the cache; emit the summary warning
	# exactly once.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	var cache = ctx["cache"]
	var authoritative_handle = SubscriptionHandleScript.new(1, 9, 9)
	registry.handles_by_id[1] = authoritative_handle
	registry.handles_by_query_set_id[9] = authoritative_handle
	service._authoritative_handle_id = 1
	service._pending_reducer_calls[11] = {
		"invocation_id": "inv-11",
		"reducer_name": "bulk_apply",
		"called_at": 1.0,
	}
	var overflow: int = 100
	var total_entries: int = ServiceScript.MAX_BUNDLED_QUERY_SETS + overflow
	var query_sets: Array = []
	query_sets.resize(total_entries)
	for i in range(total_entries):
		query_sets[i] = {
			"query_set_id": 9,
			"tables": [],
			"tick": i,
		}
	service._handle_reducer_result({
		"request_id": 11,
		"status": "Committed",
		"reducer_name": "bulk_apply",
		"query_sets": query_sets,
	})
	_emit_result({
		"total_entries": total_entries,
		"cap": ServiceScript.MAX_BUNDLED_QUERY_SETS,
		"overflow": overflow,
		"applied_count": cache.applied_query_set_ids.size(),
		"success_events": _jsonify(_reducer_success_events),
	})
	quit(0)


func _run_bundle_at_cap_emits_no_warning() -> void:
	# Bundle size exactly equal to the cap: all entries processed, zero
	# truncation warning. The `bundle_size > MAX_BUNDLED_QUERY_SETS` gate uses
	# strict `>`, so at-cap is the boundary that must NOT emit. Uses the
	# TransactionUpdate path as a single representative lane (the two handlers
	# share the gate shape).
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	var cache = ctx["cache"]
	var authoritative_handle = SubscriptionHandleScript.new(1, 88, 88)
	registry.handles_by_id[1] = authoritative_handle
	registry.handles_by_query_set_id[88] = authoritative_handle
	service._authoritative_handle_id = 1
	var at_cap: int = ServiceScript.MAX_BUNDLED_QUERY_SETS
	var query_sets: Array = []
	query_sets.resize(at_cap)
	for i in range(at_cap):
		query_sets[i] = {
			"query_set_id": 88,
			"tables": [],
			"tick": i,
		}
	service._handle_transaction_update({
		"query_sets": query_sets,
	})
	_emit_result({
		"at_cap": at_cap,
		"applied_count": cache.applied_query_set_ids.size(),
	})
	quit(0)


func _run_reducer_result_non_integer_request_id() -> void:
	# Top-level `request_id` shaped as a Dictionary must not crash `int(...)`
	# and must not silently coerce to `0` (which would false-match a pending
	# call reserved at `request_id == 0`, had one existed). The handler must
	# push_warning once, return early, and NOT emit a reducer-success/failure
	# signal for the Dictionary-shaped request_id. We set up a pending call at
	# `request_id == 0` so any silent coercion would be observable — the
	# success/failure events stay empty to prove no match happened.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	service._pending_reducer_calls[0] = {
		"invocation_id": "inv-trap-zero",
		"reducer_name": "trap",
		"called_at": 1.0,
	}
	service._handle_reducer_result({
		"request_id": {"k": "v"},
		"status": "Committed",
		"query_sets": [],
	})
	_emit_result({
		"row_changed_events": _jsonify(_row_changed_events),
		"success_events": _jsonify(_reducer_success_events),
		"failure_events": _jsonify(_reducer_failure_events),
		"pending_still_holds_zero": service._pending_reducer_calls.has(0),
	})
	quit(0)


func _run_request_id_persists_across_reset() -> void:
	# Reserve multiple ids, tear the subscription runtime down via the same
	# path a disconnect walks, then reserve again. `post_reset_id` must be
	# strictly greater than the LAST pre-reset id — a re-introduced
	# `_next_request_id = 1` inside `_reset_subscription_runtime()` would emit
	# `post_reset_id = 2` which is greater than the FIRST reserved id (1) but
	# not greater than the last (3), so the test catches a silent regression.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var pre_reset_ids: Array = []
	pre_reset_ids.append(service._reserve_request_id())
	pre_reset_ids.append(service._reserve_request_id())
	pre_reset_ids.append(service._reserve_request_id())
	service._reset_subscription_runtime()
	var post_reset_id: int = service._reserve_request_id()
	_emit_result({
		"pre_reset_ids": pre_reset_ids,
		"post_reset_id": post_reset_id,
	})
	quit(0)


func _run_subscribe_applied_rebinds_query_set_id() -> void:
	# The pending handle starts with `query_set_id == request_id` so the
	# request-id keyed pending map can correlate the subscribe ack. When the
	# server echoes a distinct live `query_set_id`, `_handle_subscribe_applied()`
	# must copy that id onto the handle before later ReducerResult bundle lookups
	# run through `find_by_query_set_id(...)`.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	var cache = ctx["cache"]
	var handle = SubscriptionHandleScript.new(1, 17, 17, ["SELECT * FROM smoke_test"])
	registry.handles_by_id[1] = handle
	service._pending_subscriptions[17] = handle
	service._handle_subscribe_applied({
		"request_id": 17,
		"query_set_id": 23,
		"tables": [],
	})
	service._pending_reducer_calls[99] = {
		"invocation_id": "inv-99",
		"reducer_name": "ping",
		"called_at": 1.0,
	}
	service._handle_reducer_result({
		"request_id": 99,
		"status": "Committed",
		"query_sets": [
			{
				"query_set_id": 23,
				"tables": [],
			},
		],
	})
	var resolved_handle = registry.find_by_query_set_id(23)
	_emit_result({
		"handle_query_set_id": int(handle.query_set_id),
		"resolved_handle_id": -1 if resolved_handle == null else int(resolved_handle.handle_id),
		"applied_query_set_ids": _jsonify(cache.applied_query_set_ids),
		"authoritative_handle_id": int(service._authoritative_handle_id),
	})
	quit(0)


func _run_reserve_request_id_wraps_forces_disconnect() -> void:
	# Seed `_next_request_id` at the u32 boundary (`0xFFFFFFFF`). Calling
	# `_reserve_request_id()` must push an error and schedule a retry/disconnect
	# (because the NEXT reservation would wrap on the wire and could false-match
	# a pending entry from the counter's start). The returned value is still the
	# last valid u32; the subsequent disconnect tears down `_pending_*` state so
	# the potentially-doomed value cannot false-match.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	service._current_status = service._make_status(
		ServiceScript.STATE_CONNECTED,
		"CONNECTED — harness transport",
		ServiceScript.AUTH_NONE
	)
	service._reconnect_policy = DummyReconnectPolicy.new()
	service._socket = WebSocketPeer.new()
	service._next_request_id = 0xFFFFFFFF
	var returned_id: int = service._reserve_request_id()
	_emit_result({
		"returned_id": returned_id,
		"next_request_id_after": int(service._next_request_id),
		"current_state": String(service._current_status.get("state", "")),
		"socket_cleared": service._socket == null,
	})
	quit(0)


func _run_unsubscribe_null_socket_does_not_burn_request_id() -> void:
	# State is CONNECTED but `_socket == null` (observed when a handler nulled
	# the socket synchronously). The new null-socket check BEFORE
	# `_reserve_request_id()` must keep the counter unchanged and the pending
	# map empty.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	service._current_status = service._make_status(
		ServiceScript.STATE_CONNECTED,
		"CONNECTED — harness transport",
		ServiceScript.AUTH_NONE
	)
	service._socket = null
	var before: int = int(service._next_request_id)
	service._send_unsubscribe_for_query_set(5)
	var after: int = int(service._next_request_id)
	_emit_result({
		"next_request_id_before": before,
		"next_request_id_after": after,
		"pending_unsubscribes_size": (service._pending_unsubscribes as Dictionary).size(),
	})
	quit(0)


func _run_unsubscribe_applied_erases_pending_entry() -> void:
	# Seed `_pending_unsubscribes` with a known entry; dispatch a matching
	# `UnsubscribeApplied` frame; observe the entry erased. Also cover mismatch
	# and late/stale cases — mismatched query_set_id must not erase, and an
	# unknown request_id must silently no-op (not push_error, not crash).
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	service._pending_unsubscribes[17] = 5
	service._pending_unsubscribes[42] = 9
	service._handle_unsubscribe_applied({"kind": "UnsubscribeApplied", "request_id": 17, "query_set_id": 6})
	var size_after_mismatch: int = (service._pending_unsubscribes as Dictionary).size()
	var still_has_17_after_mismatch: bool = (service._pending_unsubscribes as Dictionary).has(17)
	service._handle_unsubscribe_applied({"kind": "UnsubscribeApplied", "request_id": 17, "query_set_id": 5})
	var size_after_match: int = (service._pending_unsubscribes as Dictionary).size()
	var still_has_42: bool = (service._pending_unsubscribes as Dictionary).has(42)
	# Stale / unknown request_id — must silently no-op.
	service._handle_unsubscribe_applied({"kind": "UnsubscribeApplied", "request_id": 999, "query_set_id": 999})
	var size_after_stale: int = (service._pending_unsubscribes as Dictionary).size()
	_emit_result({
		"size_after_mismatch": size_after_mismatch,
		"still_has_17_after_mismatch": still_has_17_after_mismatch,
		"size_after_match": size_after_match,
		"still_has_42": still_has_42,
		"size_after_stale": size_after_stale,
	})
	quit(0)


func _run_unsubscribe_send_failure_does_not_record_pending() -> void:
	# A non-open WebSocketPeer makes `put_packet` return non-OK. The request_id
	# has been reserved at that point, but the pending-unsubscribe map must not
	# record an entry that can never receive a server ack.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	service._current_status = service._make_status(
		ServiceScript.STATE_CONNECTED,
		"CONNECTED — harness transport",
		ServiceScript.AUTH_NONE
	)
	service._socket = WebSocketPeer.new()
	var before: int = int(service._next_request_id)
	service._send_unsubscribe_for_query_set(5)
	_emit_result({
		"next_request_id_before": before,
		"next_request_id_after": int(service._next_request_id),
		"pending_unsubscribes_size": (service._pending_unsubscribes as Dictionary).size(),
	})
	quit(0)


func _run_reset_subscription_runtime_emits_synthetic_failure() -> void:
	# Seed `_pending_subscriptions` with a handle so `_reset_subscription_runtime`
	# can observe a pending entry. Call the reset; the new synthetic-failure
	# loop must emit a `subscription_failed` signal with the handle_id of the
	# pending entry BEFORE clearing the map.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var pending_handle = SubscriptionHandleScript.new(42, 11, 11)
	service._pending_subscriptions[11] = pending_handle
	# Also seed a pending unsubscribe to verify it gets cleared WITHOUT a
	# synthetic signal (Ask First scoped that out).
	service._pending_unsubscribes[88] = 7
	service._reset_subscription_runtime()
	await _settle_deferred()
	_emit_result({
		"subscription_failed_events": _jsonify(_subscription_failed_events),
		"handle_status_after": String(pending_handle.status),
		"pending_subscriptions_size_after": (service._pending_subscriptions as Dictionary).size(),
		"pending_unsubscribes_size_after": (service._pending_unsubscribes as Dictionary).size(),
	})
	quit(0)


func _run_reset_subscription_runtime_fails_pending_replacement_old_handle() -> void:
	# Seed both `_pending_subscriptions` (new handle id=43) AND
	# `_pending_replacements[43] = 42` with the old handle registered. Teardown
	# must emit a synthetic `subscription_failed` for the OLD handle FIRST (from
	# the new `_pending_replacements.values()` loop) and then for the NEW handle
	# (from the existing `_pending_subscriptions` iteration).
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	var old_handle = SubscriptionHandleScript.new(42, 7, 7)
	registry.handles_by_id[42] = old_handle
	registry.handles_by_query_set_id[7] = old_handle
	var new_handle = SubscriptionHandleScript.new(43, 11, 11)
	service._pending_subscriptions[11] = new_handle
	service._pending_replacements[43] = 42
	service._reset_subscription_runtime()
	await _settle_deferred()
	_emit_result({
		"subscription_failed_events": _jsonify(_subscription_failed_events),
		"old_handle_status_after": String(old_handle.status),
		"new_handle_status_after": String(new_handle.status),
		"pending_subscriptions_size_after": (service._pending_subscriptions as Dictionary).size(),
		"pending_replacements_size_after": (service._pending_replacements as Dictionary).size(),
	})
	quit(0)


func _run_reset_subscription_runtime_missing_old_handle_does_not_crash() -> void:
	# Edge: `_pending_replacements[43] = 42` but id=42 is NOT registered (e.g.
	# racing superseded path already unregistered it). Teardown must still emit
	# the synthetic failure for id=42, skip the `close()` call (no handle to
	# close), and not crash. No pending-subscribe entry in this scenario — the
	# `_pending_replacements` entry alone drives emission.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	service._pending_replacements[43] = 42
	service._reset_subscription_runtime()
	await _settle_deferred()
	_emit_result({
		"subscription_failed_events": _jsonify(_subscription_failed_events),
		"pending_subscriptions_size_after": (service._pending_subscriptions as Dictionary).size(),
		"pending_replacements_size_after": (service._pending_replacements as Dictionary).size(),
	})
	quit(0)


func _run_reset_subscription_runtime_dedupes_duplicate_replacement_old_handles() -> void:
	# Defensive edge: not constructible through the public API today, but the reset
	# path promises at-most-once synthetic failure per old handle id.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	var old_handle = SubscriptionHandleScript.new(42, 7, 7)
	registry.handles_by_id[42] = old_handle
	registry.handles_by_query_set_id[7] = old_handle
	service._pending_replacements[43] = 42
	service._pending_replacements[44] = 42
	service._reset_subscription_runtime()
	await _settle_deferred()
	_emit_result({
		"subscription_failed_events": _jsonify(_subscription_failed_events),
		"old_handle_status_after": String(old_handle.status),
		"pending_replacements_size_after": (service._pending_replacements as Dictionary).size(),
	})
	quit(0)


func _run_reset_subscription_runtime_reentrant_old_failure_still_fails_new_handle() -> void:
	# Reentrant listener: on the old-handle synthetic failure, unsubscribe the
	# replacement handle from the deferred handler. Reset still emits the new-handle
	# terminal failure — both events are queued up front from the pre-emission
	# snapshot, so a reentrant unsubscribe cannot drop the second.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	var old_handle = SubscriptionHandleScript.new(42, 7, 7)
	registry.handles_by_id[42] = old_handle
	registry.handles_by_query_set_id[7] = old_handle
	var new_handle = SubscriptionHandleScript.new(43, 11, 11)
	registry.handles_by_id[43] = new_handle
	registry.handles_by_query_set_id[11] = new_handle
	service._pending_subscriptions[11] = new_handle
	service._pending_replacements[43] = 42
	service.subscription_failed.connect(
		_on_subscription_failed_reentrant_unsubscribe.bind(service, new_handle)
	)
	service._reset_subscription_runtime()
	await _settle_deferred()
	_emit_result({
		"subscription_failed_events": _jsonify(_subscription_failed_events),
		"reentrant_unsubscribe_count": _reentrant_unsubscribe_count,
		"old_handle_status_after": String(old_handle.status),
		"new_handle_status_after": String(new_handle.status),
		"pending_subscriptions_size_after": (service._pending_subscriptions as Dictionary).size(),
		"pending_replacements_size_after": (service._pending_replacements as Dictionary).size(),
	})
	quit(0)


func _run_reset_subscription_runtime_shares_single_failed_at_unix_time() -> void:
	# Spec spec-gdscript-wire-teardown-emission-hardening (item 412): a single
	# teardown stamps every synthetic `subscription_failed` with the SAME
	# `failed_at_unix_time`. Seed one pending replacement (old handle) PLUS one
	# pending subscribe (new handle) so the reset emits both loops; assert the two
	# events carry an identical, non-zero wall-clock timestamp. Emission order is
	# unchanged (old-handle first), pinned elsewhere.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	var old_handle = SubscriptionHandleScript.new(42, 7, 7)
	registry.handles_by_id[42] = old_handle
	registry.handles_by_query_set_id[7] = old_handle
	var new_handle = SubscriptionHandleScript.new(43, 11, 11)
	service._pending_subscriptions[11] = new_handle
	service._pending_replacements[43] = 42
	service._reset_subscription_runtime()
	await _settle_deferred()
	_emit_result({
		"subscription_failed_events": _jsonify(_subscription_failed_events),
		"event_count": _subscription_failed_events.size(),
	})
	quit(0)


func _run_subscribe_rejected_while_degraded_adds_no_pending() -> void:
	# Spec spec-gdscript-wire-teardown-emission-hardening (item 413): a
	# synchronous `subscribe()` during teardown (state DEGRADED, socket non-null on
	# the retry path) is rejected by the public `subscribe()` Connected-state gate.
	# Force DEGRADED, call `subscribe(...)`, and assert it returns null and adds NO
	# `_pending_subscriptions` entry. The connected-state half of the
	# `_send_subscribe_request` guard is the deeper protection; this exercises the
	# public-API gate that callers actually hit.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	service._current_status = service._make_status(
		ServiceScript.STATE_DEGRADED,
		"DEGRADED — harness teardown in progress",
		ServiceScript.AUTH_NONE
	)
	service._socket = WebSocketPeer.new()
	var pending_before: int = (service._pending_subscriptions as Dictionary).size()
	var result = service.subscribe(["SELECT * FROM smoke_test"])
	var pending_after: int = (service._pending_subscriptions as Dictionary).size()
	_emit_result({
		"subscribe_returned_null": result == null,
		"pending_subscriptions_size_before": pending_before,
		"pending_subscriptions_size_after": pending_after,
		"current_state": String(service._current_status.get("state", "")),
	})
	quit(0)


func _run_reentrant_subscribe_during_teardown_rejected() -> void:
	# Deferred-emission reentrant flow: a `subscription_failed` handler that calls
	# `subscribe()` from the deferred emission (state is DEGRADED here — the retry
	# path) must be rejected by the public `subscribe()` Connected-state gate, so the
	# in-handler re-subscribe returns null and leaks NO `_pending_subscriptions`
	# entry. Higher fidelity than `subscribe_rejected_while_degraded_adds_no_pending`
	# (which calls `subscribe()` standalone): here the reject happens from inside a
	# real teardown's deferred handler, with both synthetic events delivered.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	service._current_status = service._make_status(
		ServiceScript.STATE_DEGRADED,
		"DEGRADED — harness reentrant",
		ServiceScript.AUTH_NONE
	)
	# Real, non-null socket — the retry-path condition (state DEGRADED, socket live).
	service._socket = WebSocketPeer.new()
	# Seed BOTH a pending replacement (old handle) and a pending subscribe (new
	# handle) so teardown emits TWO synthetic `subscription_failed` events. The
	# reentrant handler re-subscribes only on the first (its one-shot
	# `_reentrant_subscribe_armed` guard suppresses the second), so the two-event
	# setup is what actually exercises that guard — a single-emission seed would
	# leave the disarm path dead and prove nothing about repeated re-entry.
	var ctx_registry = ctx["registry"]
	var old_handle = SubscriptionHandleScript.new(42, 7, 7)
	ctx_registry.handles_by_id[42] = old_handle
	ctx_registry.handles_by_query_set_id[7] = old_handle
	service._pending_subscriptions[11] = SubscriptionHandleScript.new(43, 11, 11)
	service._pending_replacements[43] = 42
	service.subscription_failed.connect(
		_on_subscription_failed_reentrant_subscribe.bind(service)
	)
	service._reset_subscription_runtime()
	await _settle_deferred()
	_emit_result({
		"handler_fired": _reentrant_subscribe_handler_fired,
		"reentrant_subscribe_returned_null": _reentrant_subscribe_returned_null,
		"pending_added_by_reentrant_subscribe": _reentrant_subscribe_pending_delta,
		"reentrant_subscribe_attempt_count": _reentrant_subscribe_attempt_count,
		"emission_count": _subscription_failed_events.size(),
		"current_state": String(service._current_status.get("state", "")),
	})
	quit(0)


func _run_retry_teardown_resets_subscription_runtime() -> void:
	# Degraded retry starts a fresh wire session; this service does not replay
	# subscriptions across that session boundary. Retry scheduling must therefore
	# run the same subscription-runtime reset as a final disconnect.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	service._current_status = service._make_status(
		ServiceScript.STATE_CONNECTED,
		"CONNECTED — harness transport",
		ServiceScript.AUTH_NONE
	)
	service._reconnect_policy = DummyReconnectPolicy.new()
	service._socket = WebSocketPeer.new()
	var pending_handle = SubscriptionHandleScript.new(42, 11, 11)
	service._pending_subscriptions[11] = pending_handle
	service._pending_unsubscribes[88] = 7
	service._schedule_retry_or_disconnect("harness retry")
	await _settle_deferred()
	_emit_result({
		"subscription_failed_events": _jsonify(_subscription_failed_events),
		"handle_status_after": String(pending_handle.status),
		"current_state": String(service._current_status.get("state", "")),
		"socket_cleared": service._socket == null,
		"pending_subscriptions_size_after": (service._pending_subscriptions as Dictionary).size(),
		"pending_unsubscribes_size_after": (service._pending_unsubscribes as Dictionary).size(),
	})
	quit(0)


func _run_reset_subscription_runtime_survives_malformed_pending_entry() -> void:
	# Item A (exception safety): the pending-subscribe emission loop must not raise
	# on a malformed `_pending_subscriptions` value. A primitive (exercises the
	# `else null` probe branch), a bare Object lacking `handle_id` (exercises the
	# missing-property probe), and a freed Object (exercises the `is_instance_valid`
	# guard) are all skipped with a warning; the valid handle still fails. GDScript
	# has no try/finally, so a raise here would skip the
	# `_resetting_subscription_runtime = false` bookend and wedge every later
	# teardown — so we also confirm the guard is restored AND a second teardown
	# still emits for a freshly-seeded handle.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	service._pending_subscriptions[10] = 123
	service._pending_subscriptions[11] = RefCounted.new()
	# A freed Object still reports typeof == TYPE_OBJECT; the `is_instance_valid`
	# half of the probe is what stops `.get("handle_id")` from raising on it.
	var freed_object := Object.new()
	freed_object.free()
	service._pending_subscriptions[12] = freed_object
	service._pending_subscriptions[13] = SubscriptionHandleScript.new(42, 13, 13)
	service._reset_subscription_runtime()
	await _settle_deferred()
	var first_failed_events = _jsonify(_subscription_failed_events)
	var guard_after_first = service._resetting_subscription_runtime
	var pending_after_first: int = (service._pending_subscriptions as Dictionary).size()
	# A stuck guard would make this second teardown early-return and emit nothing.
	_subscription_failed_events.clear()
	service._pending_subscriptions[14] = SubscriptionHandleScript.new(99, 14, 14)
	service._reset_subscription_runtime()
	await _settle_deferred()
	_emit_result({
		"first_failed_events": first_failed_events,
		"guard_after_first": guard_after_first,
		"pending_subscriptions_size_after_first": pending_after_first,
		"second_failed_events": _jsonify(_subscription_failed_events),
		"guard_after_second": service._resetting_subscription_runtime,
	})
	quit(0)


func _run_replace_subscription_rejected_during_disconnect_teardown() -> void:
	# Item B (deferred-emission contract): on the disconnect teardown path
	# `_finish_disconnect` disposes the socket, runs `_reset_subscription_runtime`
	# (which now emits deferred), then transitions to DISCONNECTED. By the time the
	# deferred `subscription_failed` handler runs the session is terminal
	# (DISCONNECTED), so a handler that calls `replace_subscription()` is rejected up
	# front by its own Connected-state gate — it never reaches the wire and leaks no
	# pending entry. We reproduce that ordering by transitioning to DISCONNECTED
	# after the reset, mirroring `_finish_disconnect`.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	service._current_status = service._make_status(
		ServiceScript.STATE_CONNECTED,
		"CONNECTED — harness disconnect-teardown window",
		ServiceScript.AUTH_NONE
	)
	service._socket = null
	var auth_handle = SubscriptionHandleScript.new(50, 5, 5)
	registry.handles_by_id[50] = auth_handle
	registry.handles_by_query_set_id[5] = auth_handle
	service._authoritative_handle_id = 50
	service._pending_subscriptions[11] = SubscriptionHandleScript.new(43, 11, 11)
	service.subscription_failed.connect(
		_on_subscription_failed_reentrant_replace.bind(service, auth_handle)
	)
	service._reset_subscription_runtime()
	# Drive the DISCONNECTED transition through `_transition_to` (as `_finish_disconnect`
	# does) rather than assigning `_current_status` directly, so the harness emits
	# `state_changed` exactly like production and faithfully reproduces the ordering the
	# deferred handler observes.
	service._transition_to(
		ServiceScript.STATE_DISCONNECTED,
		"DISCONNECTED — harness disconnect-teardown",
		ServiceScript.AUTH_NONE
	)
	await _settle_deferred()
	_emit_result({
		"subscription_failed_events": _jsonify(_subscription_failed_events),
		"replace_handler_fired": _reentrant_replace_handler_fired,
		"replace_returned_null": _reentrant_replace_returned_null,
		"pending_subscriptions_size_after": (service._pending_subscriptions as Dictionary).size(),
		"pending_replacements_size_after": (service._pending_replacements as Dictionary).size(),
		"current_state": String(service._current_status.get("state", "")),
	})
	quit(0)


func _run_replace_subscription_rejected_while_degraded() -> void:
	# I/O matrix (retry-teardown row): a `replace_subscription()` issued while state is
	# DEGRADED is rejected up front by `replace_subscription`'s own Connected-state gate
	# — before it touches `_begin_subscription` or reserves anything — so it returns null
	# and adds no pending replacement/subscription entry. Distinct from the
	# disconnect-window path (state Connected, socket null), which is rejected deeper in
	# `_send_subscribe_request`.
	_reset_events()
	var ctx := _new_service_context()
	var service = ctx["service"]
	var registry = ctx["registry"]
	service._current_status = service._make_status(
		ServiceScript.STATE_DEGRADED,
		"DEGRADED — harness retry-path replace",
		ServiceScript.AUTH_NONE
	)
	service._socket = WebSocketPeer.new()
	var auth_handle = SubscriptionHandleScript.new(50, 5, 5)
	registry.handles_by_id[50] = auth_handle
	registry.handles_by_query_set_id[5] = auth_handle
	service._authoritative_handle_id = 50
	var pending_before: int = (service._pending_subscriptions as Dictionary).size()
	var result = service.replace_subscription(auth_handle, ["SELECT * FROM smoke_test"])
	_emit_result({
		"replace_returned_null": result == null,
		"pending_subscriptions_size_before": pending_before,
		"pending_subscriptions_size_after": (service._pending_subscriptions as Dictionary).size(),
		"pending_replacements_size_after": (service._pending_replacements as Dictionary).size(),
		"current_state": String(service._current_status.get("state", "")),
	})
	quit(0)


func _run_reset_subscription_runtime_handler_runs_after_guard_cleared() -> void:
	# Core wedge-safety proof. Synthetic `subscription_failed` is emitted DEFERRED,
	# so by the time a connected handler runs the synchronous teardown has fully
	# completed and `_resetting_subscription_runtime` is already `false`. A handler
	# that hard-errored therefore could not wedge the guard (it is already cleared)
	# nor observe a partial teardown. We record the guard value seen from inside the
	# handler, confirm the guard was restored synchronously, and confirm a SECOND
	# teardown still emits — i.e. the guard was never wedged.
	_reset_events()
	_guard_seen_inside_handler = true
	var ctx := _new_service_context()
	var service = ctx["service"]
	service.subscription_failed.connect(_on_subscription_failed_records_guard.bind(service))
	service._pending_subscriptions[11] = SubscriptionHandleScript.new(42, 11, 11)
	service._reset_subscription_runtime()
	var guard_immediately_after = service._resetting_subscription_runtime
	await _settle_deferred()
	var first_event_count := _subscription_failed_events.size()
	var guard_seen_first := _guard_seen_inside_handler
	# A stuck guard would make this second teardown early-return and emit nothing.
	_subscription_failed_events.clear()
	service._pending_subscriptions[12] = SubscriptionHandleScript.new(99, 12, 12)
	service._reset_subscription_runtime()
	await _settle_deferred()
	_emit_result({
		"guard_immediately_after_first": guard_immediately_after,
		"guard_seen_inside_handler_first": guard_seen_first,
		"first_event_count": first_event_count,
		"second_event_count": _subscription_failed_events.size(),
		"guard_after_second": service._resetting_subscription_runtime,
	})
	quit(0)


func _on_subscription_failed_records_guard(_event: Dictionary, service: Object) -> void:
	# Records the reentrance-guard value visible from inside a DEFERRED handler.
	# Does NOT append to `_subscription_failed_events` — the default
	# `_on_subscription_failed` listener already does, so the event count stays
	# accurate with both listeners connected.
	_guard_seen_inside_handler = service._resetting_subscription_runtime


func _on_subscription_failed_reentrant_replace(_event: Dictionary, service: Object, auth_handle: Object) -> void:
	# Fire exactly once: a synchronous `replace_subscription()` during the teardown
	# emitting this signal. The one-shot guard keeps a single attempt even if the
	# teardown emits more than once.
	if not _reentrant_replace_armed:
		return
	_reentrant_replace_armed = false
	_reentrant_replace_handler_fired = true
	var result = service.replace_subscription(auth_handle, ["SELECT * FROM smoke_test"])
	_reentrant_replace_returned_null = result == null


func _on_row_changed(event: Dictionary) -> void:
	_row_changed_events.append(event.duplicate(true))


func _on_reducer_succeeded(event: Dictionary) -> void:
	_reducer_success_events.append(event.duplicate(true))


func _on_reducer_failed(event: Dictionary) -> void:
	_reducer_failure_events.append(event.duplicate(true))


func _on_subscription_failed(event: Dictionary) -> void:
	_subscription_failed_events.append(event.duplicate(true))


func _on_subscription_failed_reentrant_unsubscribe(event: Dictionary, service: Object, handle: Object) -> void:
	if int(event.get("handle_id", -1)) != 42:
		return
	_reentrant_unsubscribe_count += 1
	service.unsubscribe(handle)


func _on_subscription_failed_reentrant_subscribe(_event: Dictionary, service: Object) -> void:
	# Fire exactly once: re-entrant `subscribe()` during the teardown that is
	# emitting this very `subscription_failed` signal. The one-shot guard prevents
	# a re-subscribe attempt on the SECOND (and any later) emission of the same
	# teardown — `_reentrant_subscribe_attempt_count` lets the test assert it held.
	if not _reentrant_subscribe_armed:
		return
	_reentrant_subscribe_armed = false
	_reentrant_subscribe_handler_fired = true
	_reentrant_subscribe_attempt_count += 1
	var before: int = (service._pending_subscriptions as Dictionary).size()
	var result = service.subscribe(["SELECT * FROM smoke_test"])
	var after: int = (service._pending_subscriptions as Dictionary).size()
	_reentrant_subscribe_returned_null = result == null
	_reentrant_subscribe_pending_delta = after - before


func _settle_deferred() -> void:
	# Synthetic `subscription_failed` events are emitted via `call_deferred`, so they
	# flush on a later idle frame rather than synchronously inside
	# `_reset_subscription_runtime`. Poll the MessageQueue (bounded) until the captured
	# event count holds steady across a full frame, then return. Polling-until-settled
	# rather than awaiting a fixed two frames means a handler that itself re-defers work
	# is drained to quiescence (not read mid-flush), while the frame cap keeps a
	# zero-emit teardown — or a pathologically re-deferring one — from spinning forever.
	const MAX_SETTLE_FRAMES := 8
	var previous_count := -1
	for _i in MAX_SETTLE_FRAMES:
		await process_frame
		var current_count := _subscription_failed_events.size()
		if current_count == previous_count:
			return
		previous_count = current_count


func _jsonify(v: Variant) -> Variant:
	var t := typeof(v)
	if t == TYPE_PACKED_BYTE_ARRAY:
		return (v as PackedByteArray).hex_encode()
	if t == TYPE_DICTIONARY:
		var d := {}
		for key in (v as Dictionary).keys():
			d[String(key)] = _jsonify((v as Dictionary)[key])
		return d
	if t == TYPE_ARRAY:
		var arr := []
		for entry in (v as Array):
			arr.append(_jsonify(entry))
		return arr
	return v


func _emit_result(payload: Variant) -> void:
	print("WIRE-HARNESS %s" % JSON.stringify({
		"ok": true,
		"data": payload,
	}))


func _emit_error(msg: String) -> void:
	print("WIRE-HARNESS %s" % JSON.stringify({
		"ok": false,
		"error": msg,
	}))

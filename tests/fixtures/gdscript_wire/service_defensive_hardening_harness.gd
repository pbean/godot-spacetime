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
		"reducer_result_non_integer_request_id":
			_run_reducer_result_non_integer_request_id()
		"request_id_persists_across_reset":
			_run_request_id_persists_across_reset()
		"subscribe_applied_rebinds_query_set_id":
			_run_subscribe_applied_rebinds_query_set_id()
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
	return {
		"service": service,
		"registry": registry,
		"cache": cache,
	}


func _reset_events() -> void:
	_row_changed_events.clear()
	_reducer_success_events.clear()
	_reducer_failure_events.clear()


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


func _on_row_changed(event: Dictionary) -> void:
	_row_changed_events.append(event.duplicate(true))


func _on_reducer_succeeded(event: Dictionary) -> void:
	_reducer_success_events.append(event.duplicate(true))


func _on_reducer_failed(event: Dictionary) -> void:
	_reducer_failure_events.append(event.duplicate(true))


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

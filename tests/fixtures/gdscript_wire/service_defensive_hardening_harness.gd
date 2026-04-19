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
		return handles_by_query_set_id.get(query_set_id)


class DummyCacheStore:
	extends RefCounted

	var applied_query_set_ids: Array = []

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
	var authoritative_handle = SubscriptionHandleScript.new(1, 0)
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
	var authoritative_handle = SubscriptionHandleScript.new(1, 5)
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


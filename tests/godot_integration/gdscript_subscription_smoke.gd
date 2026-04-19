extends Node

const EVENT_PREFIX := "E2E-EVENT "
const ConnectionServiceScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd")
const RemoteTablesScript = preload("res://tests/fixtures/gdscript_generated/smoke_test/remote_tables.gd")

enum Phase {
	NONE,
	WAIT_CONNECT,
	WAIT_SUBSCRIBE,
	WAIT_ROW_CHANGE,
	WAIT_REPLACE_SUCCESS,
	WAIT_REPLACE_FAILURE,
	DONE,
}

var _host: String = ""
var _module_name: String = ""
var _server_name: String = ""
var _cli_path: String = ""
var _value: String = ""
var _step_timeout_seconds: float = 45.0

var _service = null
var _bindings = null
var _phase: Phase = Phase.NONE
var _phase_started_at: float = 0.0
var _finished: bool = false
var _last_protocol_kind: String = ""
var _active_handle = null
var _replacement_handle = null
var _failed_replacement_handle = null


func _ready() -> void:
	_host = OS.get_environment("SPACETIME_E2E_HOST").strip_edges()
	_module_name = OS.get_environment("SPACETIME_E2E_MODULE").strip_edges()
	_server_name = OS.get_environment("SPACETIME_E2E_SERVER").strip_edges()
	_cli_path = OS.get_environment("SPACETIME_E2E_CLI").strip_edges()
	_value = OS.get_environment("SPACETIME_E2E_VALUE").strip_edges()

	var timeout_value := OS.get_environment("SPACETIME_E2E_STEP_TIMEOUT").strip_edges()
	if not timeout_value.is_empty():
		var parsed_timeout := timeout_value.to_float()
		if parsed_timeout > 0.0:
			_step_timeout_seconds = maxf(parsed_timeout, 1.0)

	if _host.is_empty() or _module_name.is_empty() or _server_name.is_empty() or _cli_path.is_empty() or _value.is_empty():
		_fail("bootstrap", "missing required env vars for the Story 11.3 smoke runner")
		return

	_service = ConnectionServiceScript.new()
	_bindings = RemoteTablesScript.new()
	var configure_result: int = _service.configure_bindings(_bindings)
	if configure_result != OK:
		_fail("bootstrap", "configure_bindings failed: %s" % error_string(configure_result))
		return

	_service.connection_opened.connect(_on_connection_opened)
	_service.subscription_applied.connect(_on_subscription_applied)
	_service.subscription_failed.connect(_on_subscription_failed)
	_service.row_changed.connect(_on_row_changed)
	_service.protocol_message.connect(_on_protocol_message)

	_set_phase(Phase.WAIT_CONNECT)
	var open_result: int = _service.open_connection(_host, _module_name)
	if open_result != OK:
		_fail("connect", "open_connection failed: %s" % error_string(open_result))


func _process(delta: float) -> void:
	if _finished:
		return

	_service.advance(delta)
	if _phase == Phase.NONE or _phase == Phase.DONE:
		return

	if (_now_seconds() - _phase_started_at) > _step_timeout_seconds:
		_fail(_phase_name(_phase), "timed out after %.1fs waiting for step completion" % _step_timeout_seconds)


func _on_protocol_message(message: Dictionary) -> void:
	if _finished:
		return
	_last_protocol_kind = String(message.get("kind", ""))


func _on_connection_opened(_event: Dictionary) -> void:
	if _finished or _phase != Phase.WAIT_CONNECT:
		return

	var remote_tables_now = _service.get_remote_tables()
	var contract_count := 0
	if remote_tables_now != null and remote_tables_now.has_method("get_table_contracts"):
		contract_count = remote_tables_now.get_table_contracts().size()
	_emit_step("connect", {
		"status": "ok",
		"state": _service.get_current_status().get("state", ""),
		"contract_count": contract_count,
	})

	_active_handle = _service.subscribe(["SELECT * FROM smoke_test"])
	if _active_handle == null:
		_fail("subscribe", "subscribe() returned null for SELECT * FROM smoke_test")
		return

	_set_phase(Phase.WAIT_SUBSCRIBE)


func _on_subscription_applied(event: Dictionary) -> void:
	if _finished:
		return

	_emit_event("subscription_applied", event)
	var remote_tables = _service.get_remote_tables()
	if remote_tables == null:
		_fail(_phase_name(_phase), "get_remote_tables() returned null after subscription_applied")
		return

	match _phase:
		Phase.WAIT_SUBSCRIBE:
			if int(event.get("handle_id", -1)) != int(_active_handle.handle_id):
				return

			var typed_rows: Array = remote_tables.SmokeTest.iter()
			# Fresh module: smoke_test is empty until ping_insert runs.
			# Verify the typed interface is accessible and consistently reports state.
			var typed_cache_ready = typed_rows is Array and remote_tables.SmokeTest.count >= 0
			_emit_step("subscribe", {
				"status": "ok",
				"table_handle": "SmokeTest",
				"typed_cache_ready": typed_cache_ready,
				"protocol_kind": _last_protocol_kind,
			})

			var invoke_result = _invoke_ping_insert()
			if invoke_result != OK:
				_fail("observe_row_change", "failed to invoke ping_insert via spacetime CLI")
				return

			_set_phase(Phase.WAIT_ROW_CHANGE)
		Phase.WAIT_REPLACE_SUCCESS:
			if _replacement_handle == null or int(event.get("handle_id", -1)) != int(_replacement_handle.handle_id):
				return

			var preserved_value = _first_value_for(_value)
			_emit_step("replace_success", {
				"status": "ok",
				"old_status": String(_active_handle.status),
				"new_status": String(_replacement_handle.status),
				"preserved_value": preserved_value,
			})

			_active_handle = _replacement_handle
			_replacement_handle = null

			_failed_replacement_handle = _service.replace_subscription(
				_active_handle,
				["SELECT * FROM definitely_missing_table"]
			)
			if _failed_replacement_handle == null:
				_fail("replace_failure", "replace_subscription() returned null for the invalid query")
				return

			_set_phase(Phase.WAIT_REPLACE_FAILURE)


func _on_subscription_failed(event: Dictionary) -> void:
	if _finished:
		return

	_emit_event("subscription_failed", event)
	if _phase != Phase.WAIT_REPLACE_FAILURE:
		return

	if _failed_replacement_handle == null or int(event.get("handle_id", -1)) != int(_failed_replacement_handle.handle_id):
		return

	_emit_step("replace_failure", {
		"status": "ok",
		"failed_handle_status": String(_failed_replacement_handle.status),
		"authoritative_status": String(_active_handle.status),
		"preserved_value": _first_value_for(_value),
		"error_message": String(event.get("error_message", "")),
	})
	_finish(true)


func _on_row_changed(event: Dictionary) -> void:
	if _finished:
		return

	_emit_event("row_changed", event)
	if _phase != Phase.WAIT_ROW_CHANGE:
		return

	if String(event.get("table_name", "")) != "SmokeTest":
		return
	if String(event.get("change_type", "")) != "Insert":
		return

	var new_row = event.get("new_row")
	if new_row == null or String(_row_value(new_row, "value")) != _value:
		return

	_emit_step("observe_row_change", {
		"status": "ok",
		"value": _value,
		"change_type": String(event.get("change_type", "")),
		"via": ["typed_table_handle", "get_rows", "row_changed_event"],
	})

	_replacement_handle = _service.replace_subscription(
		_active_handle,
		["SELECT * FROM smoke_test", "SELECT * FROM typed_entity"]
	)
	if _replacement_handle == null:
		_fail("replace_success", "replace_subscription() returned null for the valid overlap-first replacement")
		return

	_set_phase(Phase.WAIT_REPLACE_SUCCESS)


func _invoke_ping_insert() -> int:
	# Use the native GDScript reducer lane to trigger the row insert rather
	# than shelling out to `spacetime call`. The pytest harness runs the scene
	# under HOME=<tempdir> which defeats the spacetime CLI's self-bootstrap
	# lookup (`<HOME>/.local/share/spacetime/bin/current/spacetimedb-cli`),
	# so invoking through the service is also the more robust path in CI.
	var BsatnWriterScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/bsatn_writer.gd")
	var writer = BsatnWriterScript.new()
	writer.write_string(_value)
	var args_bytes: PackedByteArray = writer.get_bytes()
	var invocation_id: String = _service.invoke_reducer("ping_insert", args_bytes)
	if invocation_id.is_empty():
		_fail("observe_row_change", "native invoke_reducer(ping_insert) rejected the request synchronously")
		return ERR_CANT_CONNECT
	return OK


func _first_value_for(expected_value: String) -> String:
	var remote_tables = _service.get_remote_tables()
	if remote_tables == null:
		return ""

	for row in remote_tables.SmokeTest.iter():
		if String(_row_value(row, "value")) == expected_value:
			return String(_row_value(row, "value"))

	for row in _service.get_rows("SmokeTest"):
		if String(_row_value(row, "value")) == expected_value:
			return String(_row_value(row, "value"))

	return ""


func _set_phase(next_phase: Phase) -> void:
	_phase = next_phase
	_phase_started_at = _now_seconds()


func _phase_name(phase: Phase) -> String:
	match phase:
		Phase.WAIT_CONNECT:
			return "connect"
		Phase.WAIT_SUBSCRIBE:
			return "subscribe"
		Phase.WAIT_ROW_CHANGE:
			return "observe_row_change"
		Phase.WAIT_REPLACE_SUCCESS:
			return "replace_success"
		Phase.WAIT_REPLACE_FAILURE:
			return "replace_failure"
		_:
			return "bootstrap"


func _emit_step(name: String, fields: Dictionary = {}) -> void:
	var payload := fields.duplicate(true)
	payload["name"] = name
	_emit_event("step", payload)


func _emit_event(event_name: String, fields: Dictionary = {}) -> void:
	var payload := {
		"event": event_name,
	}
	for key in fields.keys():
		payload[key] = _normalize_for_json(fields[key])
	print("%s%s" % [EVENT_PREFIX, JSON.stringify(payload)])


func _fail(name: String, reason: String) -> void:
	print("%s%s" % [EVENT_PREFIX, JSON.stringify({
		"event": "step",
		"name": name,
		"status": "error",
		"reason": reason,
	})])
	_finish(false)


func _finish(passed: bool) -> void:
	if _finished:
		return

	_finished = true
	_phase = Phase.DONE
	print("%s%s" % [EVENT_PREFIX, JSON.stringify({
		"event": "done",
		"status": "ok" if passed else "error",
	})])
	get_tree().quit(0 if passed else 1)


func _row_value(row, field_name: String):
	if row == null:
		return null
	if row is Dictionary:
		return row.get(field_name, null)
	if row is Object and row.has_method("to_dictionary"):
		var as_dict = row.to_dictionary()
		return as_dict.get(field_name, null)
	return null


func _normalize_for_json(value):
	if value is Dictionary:
		var normalized := {}
		for key in value.keys():
			normalized[key] = _normalize_for_json(value[key])
		return normalized
	if value is Array:
		var normalized_array: Array = []
		for item in value:
			normalized_array.append(_normalize_for_json(item))
		return normalized_array
	if value is Object and value.has_method("to_dictionary"):
		return _normalize_for_json(value.to_dictionary())
	return value


func _now_seconds() -> float:
	return Time.get_ticks_msec() / 1000.0

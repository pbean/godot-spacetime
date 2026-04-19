extends Node

const EVENT_PREFIX := "E2E-EVENT "
const ConnectionServiceScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd")
const SpacetimeClientScript = preload("res://tests/fixtures/gdscript_generated/smoke_test/spacetimedb_client.gd")

enum Phase {
	NONE,
	WAIT_CONNECT,
	WAIT_SUBSCRIBE,
	WAIT_PING_RESULT,
	WAIT_PING_INSERT_RESULT,
	DONE,
}

var _host: String = ""
var _module_name: String = ""
var _server_name: String = ""
var _cli_path: String = ""
var _value: String = ""
var _step_timeout_seconds: float = 45.0

var _service = null
var _client = null
var _phase: Phase = Phase.NONE
var _phase_started_at: float = 0.0
var _finished: bool = false

var _ping_invocation_id: String = ""
var _ping_insert_invocation_id: String = ""
var _ping_succeeded: bool = false
var _ping_insert_succeeded: bool = false
var _ping_insert_row_observed: bool = false
var _ping_insert_reducer_name: String = ""


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
		_fail("bootstrap", "missing required env vars for the Story 11.4 smoke runner")
		return

	_service = ConnectionServiceScript.new()
	_client = SpacetimeClientScript.new(_service)
	var configure_result: int = _service.configure_bindings(_client)
	if configure_result != OK:
		_fail("bootstrap", "configure_bindings failed: %s" % error_string(configure_result))
		return

	_service.connection_opened.connect(_on_connection_opened)
	_service.subscription_applied.connect(_on_subscription_applied)
	_service.row_changed.connect(_on_row_changed)
	_service.reducer_call_succeeded.connect(_on_reducer_call_succeeded)
	_service.reducer_call_failed.connect(_on_reducer_call_failed)

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


func _on_connection_opened(_event: Dictionary) -> void:
	if _finished or _phase != Phase.WAIT_CONNECT:
		return

	_emit_step("connect", {
		"status": "ok",
		"state": _service.get_current_status().get("state", ""),
	})

	var remote_tables_now = _service.get_remote_tables()
	var contract_count := 0
	if remote_tables_now != null and remote_tables_now.has_method("get_table_contracts"):
		contract_count = remote_tables_now.get_table_contracts().size()

	_emit_step("configured_bindings", {
		"status": "ok",
		"contract_count": contract_count,
	})

	_set_phase(Phase.WAIT_SUBSCRIBE)
	var handle = _service.subscribe(["SELECT * FROM smoke_test"])
	if handle == null:
		_fail("subscribe", "subscribe() returned null")


func _on_subscription_applied(_event: Dictionary) -> void:
	if _finished or _phase != Phase.WAIT_SUBSCRIBE:
		return

	_emit_step("subscribe", {
		"status": "ok",
		"subscribed": true,
	})

	_set_phase(Phase.WAIT_PING_RESULT)
	_ping_invocation_id = _client.reducers.ping()
	if _ping_invocation_id.is_empty():
		_fail("invoke_ping", "reducers.ping() returned empty invocation_id")


func _on_reducer_call_succeeded(event: Dictionary) -> void:
	if _finished:
		return

	_emit_event("reducer_call_succeeded", event)
	var reducer_name := String(event.get("reducer_name", ""))
	var invocation_id := String(event.get("invocation_id", ""))

	if _phase == Phase.WAIT_PING_RESULT and invocation_id == _ping_invocation_id:
		_ping_succeeded = true
		_emit_step("invoke_ping", {
			"status": "ok",
			"reducer_name": reducer_name,
			"invocation_id": invocation_id,
			"succeeded": true,
		})

		_set_phase(Phase.WAIT_PING_INSERT_RESULT)
		_ping_insert_invocation_id = _client.reducers.ping_insert(_value)
		if _ping_insert_invocation_id.is_empty():
			_fail("invoke_ping_insert", "reducers.ping_insert(...) returned empty invocation_id")
		return

	if _phase == Phase.WAIT_PING_INSERT_RESULT and invocation_id == _ping_insert_invocation_id:
		_ping_insert_succeeded = true
		_ping_insert_reducer_name = reducer_name
		_check_ping_insert_complete()


func _on_reducer_call_failed(event: Dictionary) -> void:
	if _finished:
		return

	_emit_event("reducer_call_failed", event)
	var reducer_name := String(event.get("reducer_name", ""))
	var invocation_id := String(event.get("invocation_id", ""))
	var error_msg := String(event.get("error_message", ""))

	if _phase == Phase.WAIT_PING_RESULT and invocation_id == _ping_invocation_id:
		_fail("invoke_ping", "ping reducer failed: %s" % error_msg)
		return

	if _phase == Phase.WAIT_PING_INSERT_RESULT and invocation_id == _ping_insert_invocation_id:
		_fail("invoke_ping_insert", "ping_insert reducer failed reducer=%s: %s" % [reducer_name, error_msg])


func _on_row_changed(event: Dictionary) -> void:
	if _finished:
		return

	if _phase != Phase.WAIT_PING_INSERT_RESULT:
		return

	if String(event.get("table_name", "")) != "SmokeTest":
		return
	if String(event.get("change_type", "")) != "Insert":
		return

	var new_row = event.get("new_row")
	if new_row == null or String(_row_value(new_row, "value")) != _value:
		return

	_ping_insert_row_observed = true
	_check_ping_insert_complete()


func _check_ping_insert_complete() -> void:
	if not _ping_insert_succeeded or not _ping_insert_row_observed:
		return

	_emit_step("invoke_ping_insert", {
		"status": "ok",
		"reducer_name": _ping_insert_reducer_name,
		"invocation_id": _ping_insert_invocation_id,
		"succeeded": true,
		"row_observed": true,
	})

	_prove_fault_guard()


func _prove_fault_guard() -> void:
	var signal_received := false
	var success_lambda = func(_e): signal_received = true
	var fail_lambda = func(_e): signal_received = true

	_service.reducer_call_succeeded.connect(success_lambda)
	_service.reducer_call_failed.connect(fail_lambda)

	var guard_invocation_id: String = _service.invoke_reducer("", PackedByteArray())

	_service.reducer_call_succeeded.disconnect(success_lambda)
	_service.reducer_call_failed.disconnect(fail_lambda)

	var rejected_synchronously: bool = guard_invocation_id.is_empty()
	_emit_step("fault_guard_passed", {
		"status": "ok",
		"guard_triggered": not signal_received and rejected_synchronously,
		"returned_empty_invocation_id": rejected_synchronously,
	})

	_finish(not signal_received and rejected_synchronously)


func _set_phase(next_phase: Phase) -> void:
	_phase = next_phase
	_phase_started_at = _now_seconds()


func _phase_name(phase: Phase) -> String:
	match phase:
		Phase.WAIT_CONNECT:
			return "connect"
		Phase.WAIT_SUBSCRIBE:
			return "subscribe"
		Phase.WAIT_PING_RESULT:
			return "invoke_ping"
		Phase.WAIT_PING_INSERT_RESULT:
			return "invoke_ping_insert"
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
		payload[key] = fields[key]
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


func _now_seconds() -> float:
	return Time.get_ticks_msec() / 1000.0

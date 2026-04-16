extends Node

const EVENT_PREFIX := "E2E-EVENT "
const ConnectionServiceScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd")
const FileTokenStoreScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/file_token_store.gd")

enum Phase {
	NONE,
	CONNECT_ANONYMOUS,
	WAIT_CLEAN_DISCONNECT,
	WAIT_RECOVERY_CONNECT,
	WAIT_DEGRADED,
	WAIT_RECOVERED,
	WAIT_RECOVERY_DISCONNECT,
	WAIT_TOKEN_EXPIRED,
	WAIT_ANONYMOUS_FALLBACK,
	DONE,
}

var _host: String = ""
var _module_name: String = ""
var _token_path: String = "user://spacetime/test_story_11_2/token"
var _step_timeout_seconds: float = 30.0

var _service = null
var _token_store = null
var _phase: Phase = Phase.NONE
var _phase_started_at: float = 0.0
var _finished: bool = false


func _ready() -> void:
	_host = OS.get_environment("SPACETIME_E2E_HOST").strip_edges()
	_module_name = OS.get_environment("SPACETIME_E2E_MODULE").strip_edges()

	var timeout_value := OS.get_environment("SPACETIME_E2E_STEP_TIMEOUT").strip_edges()
	if not timeout_value.is_empty():
		var parsed_timeout := timeout_value.to_float()
		if parsed_timeout > 0.0:
			_step_timeout_seconds = maxf(parsed_timeout, 1.0)

	var token_path_value := OS.get_environment("SPACETIME_E2E_TOKEN_PATH").strip_edges()
	if not token_path_value.is_empty():
		_token_path = token_path_value

	if _host.is_empty() or _module_name.is_empty():
		_fail("bootstrap", "missing required env vars (SPACETIME_E2E_HOST, SPACETIME_E2E_MODULE)")
		return

	_token_store = FileTokenStoreScript.new(_token_path)
	_token_store.clear_token()

	_service = ConnectionServiceScript.new()
	_service.state_changed.connect(_on_state_changed)
	_service.connection_opened.connect(_on_connection_opened)
	_service.connection_closed.connect(_on_connection_closed)
	_service.protocol_message.connect(_on_protocol_message)

	_set_phase(Phase.CONNECT_ANONYMOUS)
	var open_result: int = _service.open_connection(_host, _module_name, {
		"token_store": _token_store,
	})
	if open_result != OK:
		_fail("bootstrap", "open_connection failed: %s" % error_string(open_result))


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


func _on_state_changed(status: Dictionary) -> void:
	if _finished:
		return

	var state := String(status.get("state", ""))
	_emit_event("state", {
		"phase": _phase_name(_phase),
		"state": state,
		"description": status.get("description", ""),
		"auth_state": status.get("auth_state", ""),
	})
	if _phase == Phase.WAIT_DEGRADED and state == "Degraded":
		_emit_step("observe_degraded", {
			"status": "ok",
			"description": status.get("description", ""),
			"auth_state": status.get("auth_state", ""),
		})
		_set_phase(Phase.WAIT_RECOVERED)
		return

	if _phase == Phase.WAIT_TOKEN_EXPIRED and state == "Disconnected":
		if String(status.get("auth_state", "")) != "TokenExpired":
			_fail("restored_token_rejected", "expected TokenExpired auth state, got %s" % status)
			return

		_emit_step("restored_token_rejected", {
			"status": "ok",
			"description": status.get("description", ""),
			"auth_state": status.get("auth_state", ""),
			"token_cleared": String(_token_store.get_token()).is_empty(),
		})
		_set_phase(Phase.WAIT_ANONYMOUS_FALLBACK)
		var fallback_result: int = _service.open_connection(_host, _module_name, {
			"token_store": _token_store,
		})
		if fallback_result != OK:
			_fail("anonymous_fallback", "fallback open_connection failed: %s" % error_string(fallback_result))
		return

	if state == "Disconnected" and _phase not in [
		Phase.WAIT_CLEAN_DISCONNECT,
		Phase.WAIT_RECOVERY_DISCONNECT,
		Phase.WAIT_TOKEN_EXPIRED,
	]:
		_fail(_phase_name(_phase), "unexpected disconnected state: %s" % status.get("description", ""))


func _on_connection_opened(event: Dictionary) -> void:
	if _finished:
		return

	match _phase:
		Phase.CONNECT_ANONYMOUS:
			_emit_step("connect_anonymous", {
				"status": "ok",
				"state": _service.get_current_status().get("state", ""),
				"description": _service.get_current_status().get("description", ""),
				"auth_state": _service.get_current_status().get("auth_state", ""),
				"identity": event.get("identity", ""),
			})
			_set_phase(Phase.WAIT_CLEAN_DISCONNECT)
			_service.close_connection()
		Phase.WAIT_RECOVERY_CONNECT:
			_service.force_transport_fault_for_testing("simulated transport fault")
			_set_phase(Phase.WAIT_DEGRADED)
		Phase.WAIT_RECOVERED:
			_emit_step("recover_connection", {
				"status": "ok",
				"description": _service.get_current_status().get("description", ""),
				"identity": event.get("identity", ""),
				"token_restored": not String(_token_store.get_token()).is_empty(),
			})
			_set_phase(Phase.WAIT_RECOVERY_DISCONNECT)
			_service.close_connection()
		Phase.WAIT_ANONYMOUS_FALLBACK:
			_emit_step("anonymous_fallback", {
				"status": "ok",
				"description": _service.get_current_status().get("description", ""),
				"identity": event.get("identity", ""),
				"auth_state": _service.get_current_status().get("auth_state", ""),
				"token_present": not String(_token_store.get_token()).is_empty(),
			})
			_finish(true)


func _on_connection_closed(event: Dictionary) -> void:
	if _finished:
		return

	_emit_event("connection_closed", {
		"phase": _phase_name(_phase),
		"close_reason": event.get("close_reason", ""),
		"error_message": event.get("error_message", ""),
	})

	match _phase:
		Phase.WAIT_CLEAN_DISCONNECT:
			if String(event.get("close_reason", "")) != "Clean":
				_fail("disconnect_clean", "expected clean disconnect, got %s" % event)
				return

			_emit_step("disconnect_clean", {
				"status": "ok",
				"close_reason": event.get("close_reason", ""),
			})
			_set_phase(Phase.WAIT_RECOVERY_CONNECT)
			var reconnect_result: int = _service.open_connection(_host, _module_name, {
				"token_store": _token_store,
			})
			if reconnect_result != OK:
				_fail("recover_connection", "recovery open_connection failed: %s" % error_string(reconnect_result))
		Phase.WAIT_RECOVERY_DISCONNECT:
			if String(event.get("close_reason", "")) != "Clean":
				_fail("disconnect_clean", "expected clean disconnect after recovery, got %s" % event)
				return

			var store_result: int = _token_store.store_token("not-a-valid-jwt")
			if store_result != OK:
				_fail("restored_token_rejected", "failed to seed invalid restored token: %s" % error_string(store_result))
				return

			_set_phase(Phase.WAIT_TOKEN_EXPIRED)
			var token_result: int = _service.open_connection(_host, _module_name, {
				"token_store": _token_store,
			})
			if token_result != OK:
				_fail("restored_token_rejected", "token-expired open_connection failed: %s" % error_string(token_result))


func _set_phase(next_phase: Phase) -> void:
	_phase = next_phase
	_phase_started_at = _now_seconds()


func _phase_name(phase: Phase) -> String:
	match phase:
		Phase.CONNECT_ANONYMOUS:
			return "connect_anonymous"
		Phase.WAIT_CLEAN_DISCONNECT:
			return "disconnect_clean"
		Phase.WAIT_RECOVERY_CONNECT:
			return "recover_connection"
		Phase.WAIT_DEGRADED:
			return "observe_degraded"
		Phase.WAIT_RECOVERED:
			return "recover_connection"
		Phase.WAIT_RECOVERY_DISCONNECT:
			return "disconnect_clean"
		Phase.WAIT_TOKEN_EXPIRED:
			return "restored_token_rejected"
		Phase.WAIT_ANONYMOUS_FALLBACK:
			return "anonymous_fallback"
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


func _now_seconds() -> float:
	return Time.get_ticks_msec() / 1000.0

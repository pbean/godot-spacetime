extends SceneTree

const ServiceScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd")


class DummyTokenStore:
	extends RefCounted

	var stored_token: String = ""
	var last_error_message: String = ""

	func get_token() -> String:
		return stored_token

	func store_token(token: String) -> int:
		stored_token = token
		return OK

	func clear_token() -> void:
		stored_token = ""


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 2:
		_emit_error("usage: simulate_initial_connection_token <token>")
		quit(2)
		return

	var mode := String(args[0])
	if mode != "simulate_initial_connection_token":
		_emit_error("unknown mode: %s" % mode)
		quit(2)
		return

	var token := String(args[1])
	var service = ServiceScript.new()
	var token_store := DummyTokenStore.new()
	service._token_store = token_store
	service._current_status = {
		"state": ServiceScript.STATE_CONNECTING,
		"description": "CONNECTING — token harness",
		"auth_state": ServiceScript.AUTH_NONE,
		"active_compression_mode": "None",
	}
	service._handle_initial_connection({
		"kind": "InitialConnection",
		"tag": 0,
		"identity": "",
		"connection_id": "",
		"token": token,
	})

	_emit_result({
		"session_token": String(service._session_token),
		"stored_token": String(token_store.stored_token),
		"state": String(service.get_current_status().get("state", "")),
		"auth_state": String(service.get_current_status().get("auth_state", "")),
	})
	quit(0)


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

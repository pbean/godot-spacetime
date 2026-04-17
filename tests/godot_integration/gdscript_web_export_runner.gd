extends Node

const ConnectionServiceScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd")
const ConnectionProtocolScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/connection_protocol.gd")
const SpacetimeClientScript = preload("res://tests/fixtures/gdscript_generated/smoke_test/spacetimedb_client.gd")
const StoryConfigScript = preload("res://tests/godot_integration/story_11_5_web_config.gd")
const ATTR_PHASE := "data-story-11-5-phase"
const ATTR_CONNECTED := "data-story-11-5-connected"
const ATTR_TRANSPORT_MODE := "data-story-11-5-transport-mode"
const ATTR_PROJECT_HAS_CSHARP := "data-story-11-5-project-has-csharp"
const ATTR_RENDERER := "data-story-11-5-renderer"
const ATTR_ERROR := "data-story-11-5-error"

enum Phase {
	NONE,
	WAIT_CONNECT,
	WAIT_SUBSCRIBE,
	DONE,
}

var _service = null
var _client = null
var _phase: Phase = Phase.NONE
var _phase_started_at: float = 0.0
var _finished: bool = false
var _connected: bool = false
var _transport_mode: String = ""
var _last_error: String = ""


func _ready() -> void:
	_publish_state("booted")

	_service = ConnectionServiceScript.new()
	_client = SpacetimeClientScript.new(_service)
	var configure_result: int = _service.configure_bindings(_client)
	if configure_result != OK:
		_fail("configure_bindings failed: %s" % error_string(configure_result))
		return

	_publish_state("bindings_configured", {
		"contract-count": str(_client.get_table_contracts().size()),
	})

	var transport_request := ConnectionProtocolScript.build_transport_request(
		StoryConfigScript.HOST,
		StoryConfigScript.MODULE_NAME,
		StoryConfigScript.QUERY_TOKEN,
		not OS.has_feature("web")
	)
	_transport_mode = String(transport_request.get("auth_mode", ""))
	_publish_state("transport_request_ready")
	if _transport_mode == "query-token":
		_publish_state("query_token_mode_confirmed")

	_service.connection_opened.connect(_on_connection_opened)
	_service.subscription_applied.connect(_on_subscription_applied)
	_service.subscription_failed.connect(_on_subscription_failed)

	_set_phase(Phase.WAIT_CONNECT)
	var open_result: int = _service.open_connection(
		StoryConfigScript.HOST,
		StoryConfigScript.MODULE_NAME,
		{
			"token_store": null,
			"credentials": StoryConfigScript.QUERY_TOKEN,
		}
	)
	if open_result != OK:
		_fail("open_connection failed: %s" % error_string(open_result))


func _process(delta: float) -> void:
	if _finished:
		return

	_service.advance(delta)
	if _phase == Phase.NONE or _phase == Phase.DONE:
		return
	if (Time.get_ticks_msec() / 1000.0) - _phase_started_at > 30.0:
		_fail("timed out waiting for Story 11.5 web export milestone")


func _on_connection_opened(_event: Dictionary) -> void:
	if _finished or _phase != Phase.WAIT_CONNECT:
		return

	_connected = true
	_publish_state("connected")

	_set_phase(Phase.WAIT_SUBSCRIBE)
	var handle = _service.subscribe(["SELECT * FROM smoke_test"])
	if handle == null:
		_fail("subscribe() returned null in the Story 11.5 web export runner")


func _on_subscription_applied(_event: Dictionary) -> void:
	if _finished or _phase != Phase.WAIT_SUBSCRIBE:
		return

	_publish_state("done")
	_finish(true)


func _on_subscription_failed(event: Dictionary) -> void:
	_fail("subscription failed in Story 11.5 web export runner: %s" % JSON.stringify(event))


func _set_phase(next_phase: Phase) -> void:
	_phase = next_phase
	_phase_started_at = Time.get_ticks_msec() / 1000.0


func _publish_state(phase_name: String, extra: Dictionary = {}) -> void:
	var state := {
		"phase": phase_name,
		"connected": "true" if _connected else "false",
		"transport-mode": _transport_mode,
		"project-has-csharp": "true" if _project_has_csharp() else "false",
		"renderer": StoryConfigScript.RENDERER_LABEL,
		"error": _last_error,
	}
	for key in extra.keys():
		state[key] = str(extra[key])
	_set_browser_attribute(ATTR_PHASE, String(state["phase"]))
	_set_browser_attribute(ATTR_CONNECTED, String(state["connected"]))
	_set_browser_attribute(ATTR_TRANSPORT_MODE, String(state["transport-mode"]))
	_set_browser_attribute(ATTR_PROJECT_HAS_CSHARP, String(state["project-has-csharp"]))
	_set_browser_attribute(ATTR_RENDERER, String(state["renderer"]))
	_set_browser_attribute(ATTR_ERROR, String(state["error"]))
	for key in extra.keys():
		_set_browser_attribute("data-story-11-5-%s" % key, String(state[key]))
	_set_browser_state_object(state)


func _set_browser_attribute(name: String, value: String) -> void:
	if not OS.has_feature("web"):
		return
	JavaScriptBridge.eval(
		"if (document.body) { document.body.setAttribute(%s, %s); }" % [
			JSON.stringify(name),
			JSON.stringify(value),
		],
		true
	)


func _set_browser_state_object(state: Dictionary) -> void:
	if not OS.has_feature("web"):
		return
	for key in state.keys():
		JavaScriptBridge.eval(
			"window.__story_11_5_state = window.__story_11_5_state || {}; window.__story_11_5_state[%s] = %s;" % [
				JSON.stringify(String(key)),
				JSON.stringify(String(state[key])),
			],
			true
		)


func _project_has_csharp() -> bool:
	var features = ProjectSettings.get_setting("application/config/features", PackedStringArray())
	for feature in features:
		if String(feature) == "C#":
			return true
	return false


func _fail(reason: String) -> void:
	_last_error = reason
	_publish_state("error")
	_finish(false)


func _finish(passed: bool) -> void:
	if _finished:
		return
	_finished = true
	_phase = Phase.DONE
	get_tree().quit(0 if passed else 1)

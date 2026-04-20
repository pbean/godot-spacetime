extends SceneTree

# Harness for spec-gdscript-wire-drain-packets-hardening runtime tests. Most
# modes drive `_update_backlog_saturation` directly across scripted tick
# sequences. The teardown mode runs `_drain_packets` against a real local
# WebSocket fixture so the contract is exercised end-to-end.

const ServiceScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd")


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


class DrainHarnessService:
	extends "res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd"

	var initial_connection_messages: Array = []

	func _handle_initial_connection(message: Dictionary) -> void:
		initial_connection_messages.append(message.duplicate(true))


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 1:
		_emit_error("missing mode argument")
		quit(2)
		return

	match String(args[0]):
		"transient_saturation_no_warning":
			_run_transient_saturation_no_warning()
		"sustained_saturation_single_warning":
			_run_sustained_saturation_single_warning()
		"recovery_re_arms_de_dup_flag":
			_run_recovery_re_arms_de_dup_flag()
		"below_watermark_suppresses_warning":
			_run_below_watermark_suppresses_warning()
		"reset_clears_saturation_state":
			_run_reset_clears_saturation_state()
		"retry_disconnect_clears_saturation_state":
			_run_retry_disconnect_clears_saturation_state()
		"teardown_treated_as_not_saturated":
			_run_teardown_treated_as_not_saturated()
		"mid_drain_teardown_disconnects_and_drops_remaining_packets":
			_run_mid_drain_teardown_disconnects_and_drops_remaining_packets()
		_:
			_emit_error("unknown mode: %s" % args[0])
			quit(2)


func _run_transient_saturation_no_warning() -> void:
	var service = ServiceScript.new()
	var timeline: Array = []
	var below_threshold := ServiceScript.BACKLOG_SATURATION_TICKS - 1
	for i in range(below_threshold):
		service._update_backlog_saturation(true, ServiceScript.BACKLOG_WATERMARK_PACKETS + 1024)
		timeline.append({
			"tick": i,
			"saturated": true,
			"counter": int(service._consecutive_saturated_ticks),
			"emitted": bool(service._backlog_warning_emitted),
		})
	service._update_backlog_saturation(false, 0)
	timeline.append({
		"tick": below_threshold,
		"saturated": false,
		"counter": int(service._consecutive_saturated_ticks),
		"emitted": bool(service._backlog_warning_emitted),
	})
	_emit_result({
		"timeline": timeline,
		"final_counter": int(service._consecutive_saturated_ticks),
		"final_emitted": bool(service._backlog_warning_emitted),
		"below_threshold": below_threshold,
	})
	quit(0)


func _run_sustained_saturation_single_warning() -> void:
	var service = ServiceScript.new()
	var tick_count := ServiceScript.BACKLOG_SATURATION_TICKS + 5
	var first_emit_tick := -1
	var emitted_history: Array = []
	for i in range(tick_count):
		service._update_backlog_saturation(true, ServiceScript.BACKLOG_WATERMARK_PACKETS + 2048)
		var emitted := bool(service._backlog_warning_emitted)
		emitted_history.append(emitted)
		if emitted and first_emit_tick == -1:
			first_emit_tick = i
	_emit_result({
		"first_emit_tick": first_emit_tick,
		"emitted_history": emitted_history,
		"final_counter": int(service._consecutive_saturated_ticks),
		"final_emitted": bool(service._backlog_warning_emitted),
		"threshold": ServiceScript.BACKLOG_SATURATION_TICKS,
	})
	quit(0)


func _run_recovery_re_arms_de_dup_flag() -> void:
	var service = ServiceScript.new()
	for _i in range(ServiceScript.BACKLOG_SATURATION_TICKS):
		service._update_backlog_saturation(true, ServiceScript.BACKLOG_WATERMARK_PACKETS + 1024)
	var episode1_counter := int(service._consecutive_saturated_ticks)
	var episode1_emitted := bool(service._backlog_warning_emitted)
	service._update_backlog_saturation(false, 0)
	var post_recovery_counter := int(service._consecutive_saturated_ticks)
	var post_recovery_emitted := bool(service._backlog_warning_emitted)
	for _i in range(ServiceScript.BACKLOG_SATURATION_TICKS):
		service._update_backlog_saturation(true, ServiceScript.BACKLOG_WATERMARK_PACKETS + 1024)
	var episode2_counter := int(service._consecutive_saturated_ticks)
	var episode2_emitted := bool(service._backlog_warning_emitted)
	_emit_result({
		"episode1": {"counter": episode1_counter, "emitted": episode1_emitted},
		"post_recovery": {"counter": post_recovery_counter, "emitted": post_recovery_emitted},
		"episode2": {"counter": episode2_counter, "emitted": episode2_emitted},
	})
	quit(0)


func _run_below_watermark_suppresses_warning() -> void:
	var service = ServiceScript.new()
	var tick_count := ServiceScript.BACKLOG_SATURATION_TICKS + 3
	for _i in range(tick_count):
		service._update_backlog_saturation(true, ServiceScript.BACKLOG_WATERMARK_PACKETS)
	_emit_result({
		"counter": int(service._consecutive_saturated_ticks),
		"emitted": bool(service._backlog_warning_emitted),
		"watermark": ServiceScript.BACKLOG_WATERMARK_PACKETS,
		"tick_count": tick_count,
	})
	quit(0)


func _run_reset_clears_saturation_state() -> void:
	var service = ServiceScript.new()
	for _i in range(ServiceScript.BACKLOG_SATURATION_TICKS + 2):
		service._update_backlog_saturation(true, ServiceScript.BACKLOG_WATERMARK_PACKETS + 4096)
	var pre_reset_counter := int(service._consecutive_saturated_ticks)
	var pre_reset_emitted := bool(service._backlog_warning_emitted)
	service._reset_subscription_runtime()
	var post_reset_counter := int(service._consecutive_saturated_ticks)
	var post_reset_emitted := bool(service._backlog_warning_emitted)
	_emit_result({
		"pre_reset": {"counter": pre_reset_counter, "emitted": pre_reset_emitted},
		"post_reset": {"counter": post_reset_counter, "emitted": post_reset_emitted},
	})
	quit(0)


func _run_retry_disconnect_clears_saturation_state() -> void:
	var service = ServiceScript.new()
	service._current_status = service._make_status(
		ServiceScript.STATE_CONNECTED,
		"CONNECTED — harness transport",
		ServiceScript.AUTH_NONE
	)
	service._consecutive_saturated_ticks = ServiceScript.BACKLOG_SATURATION_TICKS + 2
	service._backlog_warning_emitted = true
	service._reconnect_policy = DummyReconnectPolicy.new()
	service._socket = WebSocketPeer.new()
	service._schedule_retry_or_disconnect("simulated transport fault")
	_emit_result({
		"current_state": String(service._current_status.get("state", "")),
		"counter": int(service._consecutive_saturated_ticks),
		"emitted": bool(service._backlog_warning_emitted),
		"socket_cleared": service._socket == null,
		"next_retry_at_seconds": float(service._next_retry_at_seconds),
	})
	quit(0)


func _run_teardown_treated_as_not_saturated() -> void:
	var service = ServiceScript.new()
	for _i in range(ServiceScript.BACKLOG_SATURATION_TICKS - 1):
		service._update_backlog_saturation(true, ServiceScript.BACKLOG_WATERMARK_PACKETS + 128)
	var pre_teardown_counter := int(service._consecutive_saturated_ticks)
	service._update_backlog_saturation(false, 0)
	var post_teardown_counter := int(service._consecutive_saturated_ticks)
	var post_teardown_emitted := bool(service._backlog_warning_emitted)
	_emit_result({
		"pre_teardown_counter": pre_teardown_counter,
		"post_teardown_counter": post_teardown_counter,
		"post_teardown_emitted": post_teardown_emitted,
	})
	quit(0)


func _run_mid_drain_teardown_disconnects_and_drops_remaining_packets() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 2:
		_emit_error("mid-drain teardown mode requires a port argument")
		quit(2)
		return
	var port := int(args[1])
	var service = DrainHarnessService.new()
	var protocol_kinds: Array = []
	service.protocol_message.connect(
		func(message: Dictionary) -> void:
			protocol_kinds.append(String(message.get("kind", "")))
	)
	var open_result := service.open_connection("ws://127.0.0.1:%d" % port, "smoke_test")
	if open_result != OK:
		_emit_error("open_connection failed: %s" % error_string(open_result))
		quit(2)
		return
	var reached_disconnected := false
	for _i in range(120):
		service.advance()
		if String(service._current_status.get("state", "")) == ServiceScript.STATE_DISCONNECTED \
		and service._socket == null:
			reached_disconnected = true
			break
		OS.delay_msec(10)
	_emit_result({
		"protocol_kinds": protocol_kinds,
		"initial_connection_messages": service.initial_connection_messages.size(),
		"reached_disconnected": reached_disconnected,
		"socket_cleared": service._socket == null,
		"current_state": String(service._current_status.get("state", "")),
		"current_description": String(service._current_status.get("description", "")),
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

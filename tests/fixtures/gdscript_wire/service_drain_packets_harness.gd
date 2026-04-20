extends SceneTree

# Harness for spec-gdscript-wire-drain-packets-hardening runtime tests. Drives
# `_update_backlog_saturation` directly (the state-machine helper extracted
# from `_drain_packets`) across tick sequences so the saturation counter +
# de-dup flag transitions can be observed without faking WebSocketPeer.
#
# Each mode runs a scripted sequence of (saturated_this_tick, buffered_after)
# tuples, captures the counter + flag after each tick, and reports them to the
# pytest wrapper via the shared `WIRE-HARNESS` event protocol.

const ServiceScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd")


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
		"teardown_treated_as_not_saturated":
			_run_teardown_treated_as_not_saturated()
		_:
			_emit_error("unknown mode: %s" % args[0])
			quit(2)


func _run_transient_saturation_no_warning() -> void:
	# Saturate for fewer than BACKLOG_SATURATION_TICKS ticks, then recover.
	# Counter must increment during the saturated ticks and reset to 0 on the
	# first non-saturated tick. No warning should emit.
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
	# Recovery tick.
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
	# Run BACKLOG_SATURATION_TICKS + 5 saturated ticks, all with buffered_after
	# above the watermark. The flag must flip true on the BACKLOG_SATURATION_TICKS-th
	# tick and stay true (no re-emit) through the remaining 5 ticks.
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
	# Sustained saturation → warning fires; recover for one tick (flag clears);
	# re-saturate → a new warning must fire because the flag re-armed.
	var service = ServiceScript.new()
	# Episode 1: reach the threshold.
	for i in range(ServiceScript.BACKLOG_SATURATION_TICKS):
		service._update_backlog_saturation(true, ServiceScript.BACKLOG_WATERMARK_PACKETS + 1024)
	var episode1_counter := int(service._consecutive_saturated_ticks)
	var episode1_emitted := bool(service._backlog_warning_emitted)
	# Recovery tick.
	service._update_backlog_saturation(false, 0)
	var post_recovery_counter := int(service._consecutive_saturated_ticks)
	var post_recovery_emitted := bool(service._backlog_warning_emitted)
	# Episode 2: reach the threshold again. The flag must re-fire because
	# recovery cleared `_backlog_warning_emitted`.
	for i in range(ServiceScript.BACKLOG_SATURATION_TICKS):
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
	# Saturate past the tick threshold but hold `buffered_after` at or below
	# BACKLOG_WATERMARK_PACKETS. Counter must still climb, but the warning must
	# never emit because the buffer-size gate is not satisfied.
	var service = ServiceScript.new()
	var tick_count := ServiceScript.BACKLOG_SATURATION_TICKS + 3
	for i in range(tick_count):
		# Exactly at the watermark — the emit arm requires strict `>`.
		service._update_backlog_saturation(true, ServiceScript.BACKLOG_WATERMARK_PACKETS)
	_emit_result({
		"counter": int(service._consecutive_saturated_ticks),
		"emitted": bool(service._backlog_warning_emitted),
		"watermark": ServiceScript.BACKLOG_WATERMARK_PACKETS,
		"tick_count": tick_count,
	})
	quit(0)


func _run_reset_clears_saturation_state() -> void:
	# Reach the threshold → warning fires → flag set → counter pinned.
	# Call `_reset_subscription_runtime` → both fields must clear.
	var service = ServiceScript.new()
	for i in range(ServiceScript.BACKLOG_SATURATION_TICKS + 2):
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


func _run_teardown_treated_as_not_saturated() -> void:
	# Handler-induced teardown (saturated_this_tick = false in `_drain_packets`
	# when `_socket == null`) must be treated as not-saturated regardless of the
	# prior counter value. Prime the counter to just-below the threshold, then
	# simulate the teardown tick: counter must snap to 0 and flag must stay
	# false. This pins the contract that drives the `_socket != null` branch
	# of the call site in `_drain_packets`.
	var service = ServiceScript.new()
	for i in range(ServiceScript.BACKLOG_SATURATION_TICKS - 1):
		service._update_backlog_saturation(true, ServiceScript.BACKLOG_WATERMARK_PACKETS + 128)
	var pre_teardown_counter := int(service._consecutive_saturated_ticks)
	# Teardown tick — `_drain_packets` passes false for saturated_this_tick,
	# buffered_after is 0 because `_socket == null`.
	service._update_backlog_saturation(false, 0)
	var post_teardown_counter := int(service._consecutive_saturated_ticks)
	var post_teardown_emitted := bool(service._backlog_warning_emitted)
	_emit_result({
		"pre_teardown_counter": pre_teardown_counter,
		"post_teardown_counter": post_teardown_counter,
		"post_teardown_emitted": post_teardown_emitted,
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

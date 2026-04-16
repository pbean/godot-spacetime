class_name GdscriptReconnectPolicy

const DEFAULT_MAX_ATTEMPTS := 3

var max_attempts: int = DEFAULT_MAX_ATTEMPTS
var _attempts_used: int = 0


func _init(max_attempts_value: int = DEFAULT_MAX_ATTEMPTS) -> void:
	if max_attempts_value < 1:
		push_error("ReconnectPolicy requires at least one attempt.")
		max_attempts = DEFAULT_MAX_ATTEMPTS
		return

	max_attempts = max_attempts_value


func get_attempts_used() -> int:
	return _attempts_used


func reset() -> void:
	_attempts_used = 0


func try_begin_retry() -> Dictionary:
	if _attempts_used >= max_attempts:
		return {
			"ok": false,
			"attempt_number": _attempts_used,
			"delay_seconds": 0.0,
		}

	_attempts_used += 1
	var attempt_number := _attempts_used
	var delay_seconds := float(pow(2.0, attempt_number - 1))
	return {
		"ok": true,
		"attempt_number": attempt_number,
		"delay_seconds": delay_seconds,
	}

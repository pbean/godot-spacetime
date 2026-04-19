extends Node

const EVENT_PREFIX := "E2E-EVENT "
const BsatnWriterScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/bsatn_writer.gd")
const ProtocolScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/connection_protocol.gd")


func _ready() -> void:
	_emit_parsed("reducer_result_committed", ProtocolScript.parse_server_message(_build_reducer_result_committed()))
	_emit_parsed("reducer_result_failed", ProtocolScript.parse_server_message(_build_reducer_result_failed()))
	_emit_parsed("reducer_result_out_of_energy", ProtocolScript.parse_server_message(_build_reducer_result_out_of_energy()))
	_emit_parsed("reducer_result_unknown_status", ProtocolScript.parse_server_message(_build_reducer_result_unknown_status()))
	get_tree().quit(0)


func _emit_parsed(name: String, message: Dictionary) -> void:
	_emit_event("parsed", {
		"name": name,
		"kind": String(message.get("kind", "")),
		"request_id": int(message.get("request_id", -1)),
		"reducer_name": String(message.get("reducer_name", "")),
		"status": String(message.get("status", "")),
		"error_message": String(message.get("error_message", "")),
	})


# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb ReducerResult layout:
#   envelope_byte(u8=0) | variant(u8=6) | RequestId(u32) | Timestamp(u64) | ReducerOutcome
# ReducerOutcome variants (SDK declaration order):
#   [0]Ok(ReducerOk { RetValue(bytes), TransactionUpdate }) → status="Committed"
#   [1]OkEmpty(Unit) → status="Committed"
#   [2]Err(bytes) → status="Failed" (error_message="reducer returned error payload")
#   [3]InternalError(string) → status="Failed" (error_message carries the string)
# Any other outcome tag → status="Unknown".


func _build_reducer_result_committed() -> PackedByteArray:
	var writer = BsatnWriterScript.new()
	writer.write_u8(ProtocolScript.SERVER_ENVELOPE_NONE)
	writer.write_u8(ProtocolScript.SERVER_MESSAGE_REDUCER_RESULT)
	writer.write_u32(42)
	writer.write_u64(12345)
	# ReducerOutcome.Ok with empty ReducerOk(RetValue=bytes(0), TransactionUpdate.QuerySets=[])
	writer.write_u8(0)
	writer.write_bytes(PackedByteArray())
	writer.write_array_len(0)
	return writer.get_bytes()


func _build_reducer_result_failed() -> PackedByteArray:
	var writer = BsatnWriterScript.new()
	writer.write_u8(ProtocolScript.SERVER_ENVELOPE_NONE)
	writer.write_u8(ProtocolScript.SERVER_MESSAGE_REDUCER_RESULT)
	writer.write_u32(43)
	writer.write_u64(9876)
	# ReducerOutcome.InternalError(string) carries the error text.
	writer.write_u8(3)
	writer.write_string("validation error")
	return writer.get_bytes()


func _build_reducer_result_out_of_energy() -> PackedByteArray:
	var writer = BsatnWriterScript.new()
	writer.write_u8(ProtocolScript.SERVER_ENVELOPE_NONE)
	writer.write_u8(ProtocolScript.SERVER_MESSAGE_REDUCER_RESULT)
	writer.write_u32(44)
	writer.write_u64(0)
	# The declared SDK ReducerOutcome variant list does NOT include an
	# OutOfEnergy case. The service's `_handle_reducer_result` preserves the
	# OutOfEnergy failure_category branch for correlation with the C# lane's
	# ReducerOutcome.Err(bytes) shape — encode the probe as Err(bytes) and
	# assert the parser reports status=Failed (the OutOfEnergy distinction
	# is a service-side concern, not a wire-protocol concern).
	writer.write_u8(2)
	writer.write_bytes(PackedByteArray())
	return writer.get_bytes()


func _build_reducer_result_unknown_status() -> PackedByteArray:
	var writer = BsatnWriterScript.new()
	writer.write_u8(ProtocolScript.SERVER_ENVELOPE_NONE)
	writer.write_u8(ProtocolScript.SERVER_MESSAGE_REDUCER_RESULT)
	writer.write_u32(45)
	writer.write_u64(0)
	# Synthetic "future" ReducerOutcome variant the v2 parser falls back on.
	writer.write_u8(99)
	return writer.get_bytes()


func _emit_event(event_name: String, fields: Dictionary) -> void:
	var payload := {
		"event": event_name,
	}
	for key in fields.keys():
		payload[key] = fields[key]
	print("%s%s" % [EVENT_PREFIX, JSON.stringify(payload)])

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


func _build_reducer_result_committed() -> PackedByteArray:
	var writer = BsatnWriterScript.new()
	writer.write_u8(ProtocolScript.SERVER_MESSAGE_REDUCER_RESULT)
	writer.write_u32(42)
	writer.write_u64(12345)
	writer.write_string("ping")
	writer.write_u8(0)
	return writer.get_bytes()


func _build_reducer_result_failed() -> PackedByteArray:
	var writer = BsatnWriterScript.new()
	writer.write_u8(ProtocolScript.SERVER_MESSAGE_REDUCER_RESULT)
	writer.write_u32(43)
	writer.write_u64(9876)
	writer.write_string("insert_thing")
	writer.write_u8(1)
	writer.write_string("validation error")
	return writer.get_bytes()


func _build_reducer_result_out_of_energy() -> PackedByteArray:
	var writer = BsatnWriterScript.new()
	writer.write_u8(ProtocolScript.SERVER_MESSAGE_REDUCER_RESULT)
	writer.write_u32(44)
	writer.write_u64(0)
	writer.write_string("expensive_op")
	writer.write_u8(2)
	return writer.get_bytes()


func _build_reducer_result_unknown_status() -> PackedByteArray:
	var writer = BsatnWriterScript.new()
	writer.write_u8(ProtocolScript.SERVER_MESSAGE_REDUCER_RESULT)
	writer.write_u32(45)
	writer.write_u64(0)
	writer.write_string("future_reducer")
	writer.write_u8(99)
	return writer.get_bytes()


func _emit_event(event_name: String, fields: Dictionary) -> void:
	var payload := {
		"event": event_name,
	}
	for key in fields.keys():
		payload[key] = fields[key]
	print("%s%s" % [EVENT_PREFIX, JSON.stringify(payload)])

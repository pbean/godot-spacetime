extends Node

const EVENT_PREFIX := "E2E-EVENT "
const BsatnWriterScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/bsatn_writer.gd")
const ProtocolScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/connection_protocol.gd")


func _ready() -> void:
	_emit_parsed("subscribe_applied", ProtocolScript.parse_server_message(_build_subscribe_applied_frame()))
	_emit_parsed("subscription_error", ProtocolScript.parse_server_message(_build_subscription_error_frame()))
	_emit_parsed("transaction_update", ProtocolScript.parse_server_message(_build_transaction_update_frame()))
	get_tree().quit(0)


func _emit_parsed(name: String, message: Dictionary) -> void:
	match name:
		"subscribe_applied":
			var tables: Array = []
			for table_variant in message.get("tables", []):
				var table: Dictionary = table_variant
				tables.append({
					"table_name": String(table.get("table_name", "")),
					"row_count": (table.get("row_payloads", []) as Array).size(),
				})
			_emit_event("parsed", {
				"name": name,
				"kind": String(message.get("kind", "")),
				"request_id": int(message.get("request_id", -1)),
				"query_set_id": int(message.get("query_set_id", -1)),
				"tables": tables,
			})
		"subscription_error":
			_emit_event("parsed", {
				"name": name,
				"kind": String(message.get("kind", "")),
				"request_id": int(message.get("request_id", -1)),
				"query_set_id": int(message.get("query_set_id", -1)),
				"error_message": String(message.get("error_message", "")),
			})
		"transaction_update":
			var tables: Array = []
			var query_set_ids: Array = []
			for query_set_variant in message.get("query_sets", []):
				var query_set: Dictionary = query_set_variant
				query_set_ids.append(int(query_set.get("query_set_id", -1)))
				for table_variant in query_set.get("tables", []):
					var table: Dictionary = table_variant
					var variants: Array = []
					var insert_count := 0
					var delete_count := 0
					for update_variant in table.get("updates", []):
						var update_entry: Dictionary = update_variant
						variants.append(String(update_entry.get("variant", "")))
						insert_count += (update_entry.get("insert_row_payloads", []) as Array).size()
						delete_count += (update_entry.get("delete_row_payloads", []) as Array).size()
					tables.append({
						"table_name": String(table.get("table_name", "")),
						"variants": variants,
						"insert_count": insert_count,
						"delete_count": delete_count,
					})
			_emit_event("parsed", {
				"name": name,
				"kind": String(message.get("kind", "")),
				"query_set_ids": query_set_ids,
				"tables": tables,
			})


func _build_subscribe_applied_frame() -> PackedByteArray:
	var writer = BsatnWriterScript.new()
	writer.write_u8(ProtocolScript.SERVER_MESSAGE_SUBSCRIBE_APPLIED)
	writer.write_u32(55)
	writer.write_u32(77)
	writer.write_array_len(1)
	writer.write_string("smoke_test")
	_write_row_list_with_offsets(writer, [
		_encode_smoke_test_row(1, "alpha"),
		_encode_smoke_test_row(2, "bravo"),
	])
	return writer.get_bytes()


func _build_subscription_error_frame() -> PackedByteArray:
	var writer = BsatnWriterScript.new()
	writer.write_u8(ProtocolScript.SERVER_MESSAGE_SUBSCRIPTION_ERROR)
	writer.write_u8(1)
	writer.write_u32(55)
	writer.write_u32(77)
	writer.write_string("bad sql")
	return writer.get_bytes()


func _build_transaction_update_frame() -> PackedByteArray:
	var writer = BsatnWriterScript.new()
	writer.write_u8(ProtocolScript.SERVER_MESSAGE_TRANSACTION_UPDATE)
	writer.write_array_len(1)
	writer.write_u32(77)
	writer.write_array_len(1)
	writer.write_string("smoke_test")
	writer.write_array_len(1)
	writer.write_u8(0)
	_write_row_list_with_offsets(writer, [_encode_smoke_test_row(2, "charlie")])
	_write_row_list_with_offsets(writer, [_encode_smoke_test_row(2, "bravo")])
	return writer.get_bytes()


func _write_row_list_with_offsets(writer, row_payloads: Array) -> void:
	var combined := PackedByteArray()
	var offsets: Array = []
	var next_offset := 0
	for row_payload_variant in row_payloads:
		var row_payload: PackedByteArray = row_payload_variant
		next_offset += row_payload.size()
		offsets.append(next_offset)
		combined.append_array(row_payload)

	writer.write_u8(1)
	writer.write_array_len(offsets.size())
	for offset in offsets:
		writer.write_u64(int(offset))
	writer.write_bytes(combined)


func _encode_smoke_test_row(id: int, value: String) -> PackedByteArray:
	var writer = BsatnWriterScript.new()
	writer.write_u32(id)
	writer.write_string(value)
	return writer.get_bytes()


func _emit_event(event_name: String, fields: Dictionary) -> void:
	var payload := {
		"event": event_name,
	}
	for key in fields.keys():
		payload[key] = fields[key]
	print("%s%s" % [EVENT_PREFIX, JSON.stringify(payload)])

class_name GdscriptConnectionProtocol

const BsatnReaderScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/bsatn_reader.gd")
const BsatnWriterScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/bsatn_writer.gd")

const SUBPROTOCOL_BSATN := "v1.bsatn.spacetimedb"
const DEFAULT_QUERY_TOKEN_KEY := "token"

const CLIENT_MESSAGE_SUBSCRIBE := 0
const CLIENT_MESSAGE_UNSUBSCRIBE := 1
const CLIENT_MESSAGE_CALL_REDUCER := 2

const SERVER_MESSAGE_INITIAL_CONNECTION := 0
const SERVER_MESSAGE_SUBSCRIBE_APPLIED := 1
const SERVER_MESSAGE_UNSUBSCRIBE_APPLIED := 2
const SERVER_MESSAGE_SUBSCRIPTION_ERROR := 3
const SERVER_MESSAGE_TRANSACTION_UPDATE := 4
const SERVER_MESSAGE_ONE_OFF_QUERY_RESULT := 5
const SERVER_MESSAGE_REDUCER_RESULT := 6
const SERVER_MESSAGE_PROCEDURE_RESULT := 7


static func make_supported_protocols() -> PackedStringArray:
	return PackedStringArray([SUBPROTOCOL_BSATN])


static func normalize_host(host: String) -> String:
	var normalized := host.strip_edges()
	if normalized.begins_with("http://"):
		normalized = "ws://" + normalized.substr(7)
	elif normalized.begins_with("https://"):
		normalized = "wss://" + normalized.substr(8)
	elif not normalized.begins_with("ws://") and not normalized.begins_with("wss://"):
		normalized = "wss://" + normalized

	while normalized.ends_with("/"):
		normalized = normalized.substr(0, normalized.length() - 1)

	return normalized


static func build_transport_request(
	host: String,
	database: String,
	token: String,
	allow_header_auth: bool = true,
	prefer_query_token: bool = false,
	query_token_key: String = DEFAULT_QUERY_TOKEN_KEY
) -> Dictionary:
	var url := "%s/v1/database/%s/subscribe" % [normalize_host(host), database.strip_edges()]
	var headers := PackedStringArray()
	var auth_mode := "anonymous"

	if not token.is_empty():
		var use_query_token := prefer_query_token or not allow_header_auth
		if use_query_token:
			url += "?%s=%s" % [query_token_key, token]
			auth_mode = "query-token"
		else:
			headers.append("Authorization: Bearer %s" % token)
			auth_mode = "authorization-header"

	return {
		"url": url,
		"headers": headers,
		"auth_mode": auth_mode,
	}


static func encode_client_message(tag: int, payload_writer: Callable = Callable()) -> PackedByteArray:
	var writer = BsatnWriterScript.new()
	writer.write_u8(tag)
	if not payload_writer.is_null():
		payload_writer.call(writer)
	return writer.get_bytes()


static func parse_server_message(packet: PackedByteArray, is_compressed: bool = false) -> Dictionary:
	var payload := packet
	if is_compressed:
		payload = BsatnReaderScript.decompress_gzip(payload)

	var reader = BsatnReaderScript.new(payload)
	var tag := reader.read_u8()
	match tag:
		SERVER_MESSAGE_INITIAL_CONNECTION:
			var identity_bytes := reader.read_fixed_bytes(32)
			var connection_id_bytes := reader.read_fixed_bytes(16)
			var token := reader.read_string()
			return {
				"kind": "InitialConnection",
				"tag": tag,
				"identity": fixed_width_bytes_to_hex(identity_bytes),
				"connection_id": fixed_width_bytes_to_hex(connection_id_bytes),
				"token": token,
			}
		SERVER_MESSAGE_SUBSCRIBE_APPLIED:
			return _parse_subscribe_applied(tag, payload, reader)
		SERVER_MESSAGE_UNSUBSCRIBE_APPLIED:
			return _raw_message("UnsubscribeApplied", tag, payload)
		SERVER_MESSAGE_SUBSCRIPTION_ERROR:
			return _parse_subscription_error(tag, payload, reader)
		SERVER_MESSAGE_TRANSACTION_UPDATE:
			return _parse_transaction_update(tag, payload, reader)
		SERVER_MESSAGE_ONE_OFF_QUERY_RESULT:
			return _raw_message("OneOffQueryResult", tag, payload)
		SERVER_MESSAGE_REDUCER_RESULT:
			return _parse_reducer_result(tag, payload, reader)
		SERVER_MESSAGE_PROCEDURE_RESULT:
			return _raw_message("ProcedureResult", tag, payload)
		_:
			return _raw_message("Unknown", tag, payload)


static func fixed_width_bytes_to_hex(bytes: PackedByteArray) -> String:
	var pieces: Array[String] = []
	for index in range(bytes.size() - 1, -1, -1):
		pieces.append("%02X" % bytes[index])
	return "".join(pieces)


static func _parse_subscribe_applied(tag: int, payload: PackedByteArray, reader) -> Dictionary:
	return {
		"kind": "SubscribeApplied",
		"tag": tag,
		"request_id": reader.read_u32(),
		"query_set_id": reader.read_u32(),
		"tables": _parse_query_rows(reader),
		"raw_payload": payload.slice(1, payload.size()),
	}


static func _parse_subscription_error(tag: int, payload: PackedByteArray, reader) -> Dictionary:
	var request_id = null
	var has_request_id = reader.read_option_tag()
	if has_request_id:
		request_id = reader.read_u32()

	return {
		"kind": "SubscriptionError",
		"tag": tag,
		"request_id": request_id,
		"query_set_id": reader.read_u32(),
		"error_message": reader.read_string(),
		"raw_payload": payload.slice(1, payload.size()),
	}


static func _parse_transaction_update(tag: int, payload: PackedByteArray, reader) -> Dictionary:
	var query_set_count = reader.read_array_len()
	var query_sets: Array = []
	for _i in range(query_set_count):
		query_sets.append(_parse_query_set_update(reader))

	return {
		"kind": "TransactionUpdate",
		"tag": tag,
		"query_sets": query_sets,
		"raw_payload": payload.slice(1, payload.size()),
	}


static func _parse_query_rows(reader) -> Array:
	var table_count = reader.read_array_len()
	var tables: Array = []
	for _i in range(table_count):
		tables.append(_parse_single_table_rows(reader))
	return tables


static func _parse_single_table_rows(reader) -> Dictionary:
	var table_name = reader.read_string()
	var row_list = _parse_bsatn_row_list(reader)
	return {
		"table_name": table_name,
		"row_payloads": row_list.get("row_payloads", []),
		"rows_data": row_list.get("rows_data", PackedByteArray()),
		"size_hint": row_list.get("size_hint", {}),
	}


static func _parse_query_set_update(reader) -> Dictionary:
	var query_set_id = reader.read_u32()
	var table_count = reader.read_array_len()
	var tables: Array = []
	for _i in range(table_count):
		tables.append(_parse_table_update(reader))
	return {
		"query_set_id": query_set_id,
		"tables": tables,
	}


static func _parse_table_update(reader) -> Dictionary:
	var table_name = reader.read_string()
	var update_count = reader.read_array_len()
	var updates: Array = []
	for _i in range(update_count):
		updates.append(_parse_table_update_rows(reader))
	return {
		"table_name": table_name,
		"updates": updates,
	}


static func _parse_table_update_rows(reader) -> Dictionary:
	var variant_tag = reader.read_u8()
	match variant_tag:
		0:
			var inserts = _parse_bsatn_row_list(reader)
			var deletes = _parse_bsatn_row_list(reader)
			return {
				"variant": "PersistentTable",
				"insert_row_payloads": inserts.get("row_payloads", []),
				"delete_row_payloads": deletes.get("row_payloads", []),
			}
		1:
			var event_rows = _parse_bsatn_row_list(reader)
			return {
				"variant": "EventTable",
				"event_row_payloads": event_rows.get("row_payloads", []),
			}
		_:
			return {
				"variant": "Unknown",
				"tag": variant_tag,
			}


static func _parse_bsatn_row_list(reader) -> Dictionary:
	var size_hint = _parse_row_size_hint(reader)
	var rows_data = reader.read_bytes()
	return {
		"size_hint": size_hint,
		"rows_data": rows_data,
		"row_payloads": _split_bsatn_rows(rows_data, size_hint),
	}


static func _parse_row_size_hint(reader) -> Dictionary:
	var hint_tag = reader.read_u8()
	match hint_tag:
		0:
			return {
				"kind": "FixedSize",
				"size": reader.read_u16(),
			}
		1:
			var offset_count = reader.read_array_len()
			var offsets: Array = []
			for _i in range(offset_count):
				offsets.append(reader.read_u64())
			return {
				"kind": "RowOffsets",
				"offsets": offsets,
			}
		_:
			push_error("Unsupported BSATN row size hint tag %d." % hint_tag)
			return {
				"kind": "Unknown",
				"tag": hint_tag,
			}


static func _split_bsatn_rows(rows_data: PackedByteArray, size_hint: Dictionary) -> Array:
	var row_payloads: Array = []
	match String(size_hint.get("kind", "")):
		"FixedSize":
			var row_size := int(size_hint.get("size", 0))
			if row_size <= 0:
				return row_payloads

			if rows_data.size() % row_size != 0:
				push_error("FixedSize BSATN row data length %d is not divisible by row size %d." % [rows_data.size(), row_size])
				return row_payloads

			var row_count := rows_data.size() / row_size
			for index in range(row_count):
				var start := index * row_size
				row_payloads.append(rows_data.slice(start, start + row_size))
		"RowOffsets":
			var previous_offset := 0
			for offset_variant in size_hint.get("offsets", []):
				var offset := int(offset_variant)
				if offset < previous_offset or offset > rows_data.size():
					push_error("Invalid BSATN row offset %d for payload size %d." % [offset, rows_data.size()])
					return row_payloads
				row_payloads.append(rows_data.slice(previous_offset, offset))
				previous_offset = offset
		_:
			push_error("Unsupported BSATN row size hint kind %s." % String(size_hint.get("kind", "")))

	return row_payloads


static func _parse_reducer_result(tag: int, payload: PackedByteArray, reader) -> Dictionary:
	var request_id: int = reader.read_u32()
	var _unused: int = reader.read_u64()
	var reducer_name: String = reader.read_string()
	var status_tag: int = reader.read_u8()
	var status: String
	var error_message: String = ""
	match status_tag:
		0:
			status = "Committed"
		1:
			status = "Failed"
			error_message = reader.read_string()
		2:
			status = "OutOfEnergy"
		_:
			status = "Unknown"
	return {
		"kind": "ReducerResult",
		"tag": tag,
		"request_id": request_id,
		"reducer_name": reducer_name,
		"status": status,
		"error_message": error_message,
		"raw_payload": payload.slice(1, payload.size()),
	}


static func _raw_message(kind: String, tag: int, payload: PackedByteArray) -> Dictionary:
	return {
		"kind": kind,
		"tag": tag,
		"raw_payload": payload.slice(1, payload.size()),
	}

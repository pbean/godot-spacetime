class_name GdscriptConnectionProtocol

const BsatnReaderScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/bsatn_reader.gd")
const BsatnWriterScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/bsatn_writer.gd")

# Subprotocol advertised during the WebSocket handshake. The pinned upstream
# ClientSDK 2.1.0 NuGet negotiates `v2.bsatn.spacetimedb` and the pinned
# 2.1.0 server only accepts the SDK's own BSATN encodings on this subprotocol.
# The older `v1.bsatn.spacetimedb` remains alive on the server but uses a
# stale field ordering (Identity → extra byte → Token → ConnectionId for
# InitialConnection, no compression byte prefix on server frames) that differs
# from what the pinned SDK emits — matching the SDK is mandatory for
# Subscribe/CallReducer round-trips to succeed.
const SUBPROTOCOL_BSATN := "v2.bsatn.spacetimedb"
const DEFAULT_QUERY_TOKEN_KEY := "token"

# ClientMessage variant indices — observed against `spacetime 2.1.0` over
# `v2.bsatn.spacetimedb`. Order matches the SDK's `ClientMessage` declared
# variants: `[0]Subscribe, [1]Unsubscribe, [2]OneOffQuery, [3]CallReducer,
# [4]CallProcedure`. `CALL_REDUCER` used to be `2` on the legacy `v1` wire
# which collided with `OneOffQuery` and produced `"no such reducer"` errors
# whenever a reducer was invoked.
const CLIENT_MESSAGE_SUBSCRIBE := 0
const CLIENT_MESSAGE_UNSUBSCRIBE := 1
const CLIENT_MESSAGE_ONE_OFF_QUERY := 2
const CLIENT_MESSAGE_CALL_REDUCER := 3
const CLIENT_MESSAGE_CALL_PROCEDURE := 4

# ServerMessage variant indices — observed against `spacetime 2.1.0` over
# `v2.bsatn.spacetimedb`. Order matches the SDK's `ServerMessage` declared
# variants. Every server frame is prefixed with a compression byte (0=None,
# 1=Brotli, 2=Gzip) before the BSATN-encoded ServerMessage — the variant
# tag is therefore at byte[1] of the raw packet, not byte[0].
const SERVER_MESSAGE_INITIAL_CONNECTION := 0
const SERVER_MESSAGE_SUBSCRIBE_APPLIED := 1
const SERVER_MESSAGE_UNSUBSCRIBE_APPLIED := 2
const SERVER_MESSAGE_SUBSCRIPTION_ERROR := 3
const SERVER_MESSAGE_TRANSACTION_UPDATE := 4
const SERVER_MESSAGE_ONE_OFF_QUERY_RESULT := 5
const SERVER_MESSAGE_REDUCER_RESULT := 6
const SERVER_MESSAGE_PROCEDURE_RESULT := 7

# Frame envelope byte values at the head of every server frame (0=None,
# 1=Brotli, 2=Gzip). The decompression call itself lives in `BsatnReaderScript`
# to keep this module free of an inline second binary-parsing path.
const SERVER_ENVELOPE_NONE := 0
const SERVER_ENVELOPE_BROTLI := 1
const SERVER_ENVELOPE_GZIP := 2


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
			var normalized_query_token_key := query_token_key.strip_edges()
			if normalized_query_token_key.is_empty():
				normalized_query_token_key = DEFAULT_QUERY_TOKEN_KEY
			url += "?%s=%s" % [normalized_query_token_key.uri_encode(), token.uri_encode()]
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


# --- Pure static encoders — the oracle for `test_gdscript_wire_layouts.py`. ---
# Each encoder builds a ClientMessage byte-for-byte against the pinned 2.1.0
# wire and is invoked from `gdscript_connection_service.gd` via
# `send_protocol_message`. Keeping them static (not service-instance methods)
# lets the wire tests re-derive the exact bytes without stubbing a service.


static func encode_subscribe(request_id: int, query_set_id: int, query_sqls: Array) -> PackedByteArray:
	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb (see
	# tests/fixtures/gdscript_wire/subscribe_sent.bin):
	#
	#   tag(u8=0) | RequestId(u32) | QuerySetId(u32) | QueryStrings(array<string>)
	#
	# Field order matches the pinned SDK's declared `Subscribe { RequestId,
	# QuerySetId, QueryStrings }` struct — there is no leading reserved u32.
	return encode_client_message(
		CLIENT_MESSAGE_SUBSCRIBE,
		func(writer) -> void:
			writer.write_u32(int(request_id))
			writer.write_u32(int(query_set_id))
			writer.write_array_len(query_sqls.size())
			for sql_variant in query_sqls:
				writer.write_string(String(sql_variant))
	)


static func encode_unsubscribe(request_id: int, query_set_id: int, flags: int = 0) -> PackedByteArray:
	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb (see
	# tests/fixtures/gdscript_wire/unsubscribe_sent.bin):
	#
	#   tag(u8=1) | RequestId(u32) | QuerySetId(u32) | Flags(u8)
	return encode_client_message(
		CLIENT_MESSAGE_UNSUBSCRIBE,
		func(writer) -> void:
			writer.write_u32(int(request_id))
			writer.write_u32(int(query_set_id))
			writer.write_u8(int(flags))
	)


static func encode_call_reducer(request_id: int, reducer_name: String, args_bytes: PackedByteArray, flags: int = 0) -> PackedByteArray:
	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb (see
	# tests/fixtures/gdscript_wire/call_reducer_ping_insert_sent.bin):
	#
	#   tag(u8=3) | RequestId(u32) | Flags(u8) | Reducer(string) | Args(bytes)
	return encode_client_message(
		CLIENT_MESSAGE_CALL_REDUCER,
		func(writer) -> void:
			writer.write_u32(int(request_id))
			writer.write_u8(int(flags))
			writer.write_string(reducer_name)
			writer.write_bytes(args_bytes)
	)


static func parse_server_message(packet: PackedByteArray, is_compressed: bool = false) -> Dictionary:
	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb: every server frame is
	# prefixed with a compression byte (0=None, 1=Brotli, 2=Gzip). After
	# stripping (or decompressing) the envelope, the remaining bytes are the
	# BSATN-encoded ServerMessage whose first byte is the variant tag.
	#
	# `is_compressed` is retained for backward compatibility with the legacy
	# `v1.bsatn.spacetimedb` wire where the GDScript transport tracked a
	# separate `_active_compression_mode` flag; in v2 the envelope byte is
	# per-frame so callers can pass `false` and let this helper dispatch.
	if packet.is_empty():
		return _raw_message("Unknown", -1, packet)

	var payload := packet
	var compression_tag := packet[0]
	if is_compressed:
		# Legacy gate — `_active_compression_mode != "None"` was set globally
		# for the whole session. Fall back to decompressing the full packet
		# minus the envelope byte so existing callers keep working.
		payload = BsatnReaderScript.decompress_gzip(packet.slice(1, packet.size()))
	else:
		match compression_tag:
			SERVER_ENVELOPE_NONE:
				payload = packet.slice(1, packet.size())
			SERVER_ENVELOPE_GZIP, SERVER_ENVELOPE_BROTLI:
				# Brotli canonicalises to Gzip on the wire per upstream.
				payload = BsatnReaderScript.decompress_gzip(packet.slice(1, packet.size()))
			_:
				push_error("Unknown ServerMessage compression envelope byte 0x%02X" % compression_tag)
				return _raw_message("Unknown", compression_tag, packet)

	var reader = BsatnReaderScript.new(payload)
	var tag := reader.read_u8()
	match tag:
		SERVER_MESSAGE_INITIAL_CONNECTION:
			# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb (see
			# tests/fixtures/gdscript_wire/initial_connection_recv.bin):
			#
			#   variant(u8=0) | Identity(32) | ConnectionId(16) | Token(string)
			#
			# Matches the SDK's declared `InitialConnection { Identity,
			# ConnectionId, Token }` struct order. The earlier legacy-v1
			# "Identity → extra byte → Token → ConnectionId" ordering no
			# longer applies once the subprotocol moves to v2.
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
			return _parse_unsubscribe_applied(tag, payload, reader)
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
	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb (see
	# tests/fixtures/gdscript_wire/subscribe_applied_recv.bin):
	#
	#   variant(u8=1) | RequestId(u32) | QuerySetId(u32) | Rows(QueryRows)
	#   QueryRows = Tables(Vec<SingleTableRows>)
	return {
		"kind": "SubscribeApplied",
		"tag": tag,
		"request_id": reader.read_u32(),
		"query_set_id": reader.read_u32(),
		"tables": _parse_query_rows(reader),
		"raw_payload": payload.slice(1, payload.size()),
	}


static func _parse_unsubscribe_applied(tag: int, payload: PackedByteArray, reader) -> Dictionary:
	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb (see
	# tests/fixtures/gdscript_wire/unsubscribe_applied_recv.bin):
	#
	#   variant(u8=2) | RequestId(u32) | QuerySetId(u32) | trailing u8 flag
	#
	# The 11-byte captured ack ends with a single `0x01` byte whose meaning
	# is not documented in the SDK's `UnsubscribeApplied` struct declaration
	# but is included here so the round-trip length (11) matches.
	var request_id: int = reader.read_u32()
	var query_set_id: int = reader.read_u32()
	var trailing_flag := 0
	if reader.has_more():
		trailing_flag = reader.read_u8()
	return {
		"kind": "UnsubscribeApplied",
		"tag": tag,
		"request_id": request_id,
		"query_set_id": query_set_id,
		"trailing_flag": trailing_flag,
		"raw_payload": payload.slice(1, payload.size()),
	}


static func _parse_subscription_error(tag: int, payload: PackedByteArray, reader) -> Dictionary:
	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb: SDK declaration is
	# `SubscriptionError { RequestId: Option<u32>, QuerySetId, Error }`.
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
	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb: SDK declaration is
	# `TransactionUpdate { QuerySets: Vec<QuerySetUpdate> }`.
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
	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb (see
	# tests/fixtures/gdscript_wire/reducer_result_recv.bin):
	#
	#   variant(u8=6) | RequestId(u32) | Timestamp(u64) | ReducerOutcome
	#
	# ReducerOutcome variants (SDK declaration order):
	#   [0]Ok(ReducerOk { RetValue(bytes), TransactionUpdate })
	#   [1]OkEmpty(Unit)
	#   [2]Err(bytes)
	#   [3]InternalError(string)
	#
	# The bundled TransactionUpdate inside a successful ReducerResult is what
	# actually carries the inserted/deleted rows — the v2 server no longer
	# emits a standalone TransactionUpdate frame alongside ReducerResult.
	var request_id: int = reader.read_u32()
	var timestamp_micros: int = reader.read_u64()
	var outcome_tag: int = reader.read_u8()
	var status: String = "Unknown"
	var error_message: String = ""
	var query_sets: Array = []
	match outcome_tag:
		0:
			# Ok(ReducerOk { RetValue(bytes), TransactionUpdate })
			status = "Committed"
			var _ret_value: PackedByteArray = reader.read_bytes()
			var query_set_count: int = reader.read_array_len()
			for _i in range(query_set_count):
				query_sets.append(_parse_query_set_update(reader))
		1:
			status = "Committed"
		2:
			status = "Failed"
			var err_bytes: PackedByteArray = reader.read_bytes()
			var err_utf8: String = err_bytes.get_string_from_utf8()
			error_message = err_utf8 if err_utf8 != "" else err_bytes.hex_encode()
		3:
			status = "Failed"
			error_message = reader.read_string()
		_:
			status = "Unknown"
	# Historical API surface kept for `_handle_reducer_result` — the
	# `reducer_name` was available in the legacy-v1 ReducerResult frame but
	# is NOT in the v2 SDK declaration. The dispatcher correlates the result
	# with its `_pending_reducer_calls` entry via `request_id` and pulls the
	# name from there.
	return {
		"kind": "ReducerResult",
		"tag": tag,
		"request_id": request_id,
		"reducer_name": "",
		"status": status,
		"error_message": error_message,
		"timestamp_micros": timestamp_micros,
		"query_sets": query_sets,
		"raw_payload": payload.slice(1, payload.size()),
	}


static func _raw_message(kind: String, tag: int, payload: PackedByteArray) -> Dictionary:
	return {
		"kind": kind,
		"tag": tag,
		"raw_payload": payload.slice(1, payload.size()),
	}

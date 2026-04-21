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


static func _structured_server_message_requires_body(tag: int) -> bool:
	match tag:
		SERVER_MESSAGE_INITIAL_CONNECTION, SERVER_MESSAGE_SUBSCRIBE_APPLIED, SERVER_MESSAGE_UNSUBSCRIBE_APPLIED, SERVER_MESSAGE_SUBSCRIPTION_ERROR, SERVER_MESSAGE_TRANSACTION_UPDATE, SERVER_MESSAGE_REDUCER_RESULT:
			return true
		_:
			return false


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
	# `is_compressed` is retained only as a session-level hint from the service.
	# In v2 the envelope byte is authoritative even when compression was
	# requested for the whole session, so decoding always dispatches from
	# `packet[0]` instead of forcing the legacy whole-frame gzip path.
	# A valid v2 server frame is at minimum envelope(u8) + variant tag(u8) = 2
	# bytes. The earlier `packet.is_empty()` guard let 1-byte envelope-only
	# frames slip through into `BsatnReader.read_u8`, which tripped
	# `_fail → len(int)` and aborted the receive loop instead of producing a
	# routable ProtocolError for `_schedule_retry_or_disconnect`.
	if packet.size() < 2:
		var short_msg := (
			"Empty ServerMessage packet." if packet.is_empty()
			else "ServerMessage packet too short: %d byte(s), need >= 2." % packet.size()
		)
		return _protocol_error(short_msg, -1, packet)

	var payload := packet
	var compression_tag := packet[0]
	match compression_tag:
		SERVER_ENVELOPE_NONE:
			payload = packet.slice(1, packet.size())
		SERVER_ENVELOPE_GZIP, SERVER_ENVELOPE_BROTLI:
			# Brotli canonicalises to Gzip on the wire per upstream.
			var compressed_payload := packet.slice(1, packet.size())
			# Probe for gzip magic bytes (`1F 8B`) before handing the buffer to
			# `decompress_gzip`. That helper returns an empty `PackedByteArray`
			# on decode failure, which is indistinguishable at the post-
			# decompression size check from a well-formed stream that happens
			# to decompress to zero bytes. Routing corrupt envelopes through a
			# distinct protocol error gives operators a separable failure
			# signal. Magic-byte check covers the corrupt / truncated /
			# wrong-encoding cases at the call-site layer; the existing
			# `payload.size() < 1` guard below continues to cover the
			# well-formed-but-empty case.
			if compressed_payload.size() < 2 \
			or compressed_payload[0] != 0x1F \
			or compressed_payload[1] != 0x8B:
				return _protocol_error("Corrupt compressed envelope: missing gzip magic bytes.", -1, packet)
			payload = BsatnReaderScript.decompress_gzip(compressed_payload)
		_:
			var session_hint := "session expects compressed frames" if is_compressed else "session accepts uncompressed frames"
			return _protocol_error(
				"Unknown ServerMessage compression envelope byte 0x%02X (%s)." % [compression_tag, session_hint],
				-1,
				packet
			)

	# Post-decompression short-payload guard: after the envelope branch assigns
	# `payload`, the decoded buffer must be at least 1 byte so `read_u8()` can
	# consume the ServerMessage variant tag. A Gzip/Brotli stream that
	# decompresses to 0 bytes (observed in malformed/truncated compressed
	# frames) would otherwise reach `BsatnReader.new(payload)` and hit
	# `_fail → len(int)` on the first `read_u8()` call. Mirrors the raw-packet
	# `packet.size() < 2` guard above.
	if payload.size() < 1:
		return _protocol_error("Decompressed ServerMessage payload too short.", -1, packet)
	# A tag-only payload is still malformed for every currently-structured
	# ServerMessage variant. Reject it before any typed parser can walk into
	# `read_u32()` / `read_string()` and fabricate zero values after `_fail`.
	var tag_only := int(payload[0])
	if payload.size() == 1 and _structured_server_message_requires_body(tag_only):
		return _protocol_error("ServerMessage payload too short for variant tag %d." % tag_only, tag_only, packet)

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
			return _finalize_parsed_message({
				"kind": "InitialConnection",
				"tag": tag,
				"identity": fixed_width_bytes_to_hex(identity_bytes),
				"connection_id": fixed_width_bytes_to_hex(connection_id_bytes),
				"token": token,
			}, reader, tag, payload, "InitialConnection")
		SERVER_MESSAGE_SUBSCRIBE_APPLIED:
			return _finalize_parsed_message(
				_parse_subscribe_applied(tag, payload, reader),
				reader,
				tag,
				payload,
				"SubscribeApplied"
			)
		SERVER_MESSAGE_UNSUBSCRIBE_APPLIED:
			return _finalize_parsed_message(
				_parse_unsubscribe_applied(tag, payload, reader),
				reader,
				tag,
				payload,
				"UnsubscribeApplied"
			)
		SERVER_MESSAGE_SUBSCRIPTION_ERROR:
			return _finalize_parsed_message(
				_parse_subscription_error(tag, payload, reader),
				reader,
				tag,
				payload,
				"SubscriptionError"
			)
		SERVER_MESSAGE_TRANSACTION_UPDATE:
			return _finalize_parsed_message(
				_parse_transaction_update(tag, payload, reader),
				reader,
				tag,
				payload,
				"TransactionUpdate"
			)
		SERVER_MESSAGE_ONE_OFF_QUERY_RESULT:
			# Observed spacetime 2.1.0 fixture corpus: the smoke_test wire capture
			# does not emit OneOffQueryResult. Until an authoritative fixture exists,
			# keep the branch raw and document the gap in manifest.json rather than
			# guessing at a struct shape the pinned runtime has not proven.
			return _raw_message("OneOffQueryResult", tag, payload)
		SERVER_MESSAGE_REDUCER_RESULT:
			return _finalize_parsed_message(
				_parse_reducer_result(tag, payload, reader),
				reader,
				tag,
				payload,
				"ReducerResult"
			)
		SERVER_MESSAGE_PROCEDURE_RESULT:
			# Observed spacetime 2.1.0 fixture corpus: the smoke_test workflow has
			# no procedures, so no authoritative ProcedureResult capture exists yet.
			# Keep the branch raw until the fixture corpus proves its layout.
			return _raw_message("ProcedureResult", tag, payload)
		_:
			return _protocol_error("Unknown ServerMessage variant tag %d." % tag, tag, payload)


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
	#
	# Observed live replacement-failure frame against the pinned 2.1.0 server
	# also carries a second u32 slot after QuerySetId in the
	# `subscription_error_recv.bin` fixture. Its value matches the request/query
	# set id in the captured smoke_test session, so the parser consumes it when
	# the next two u32 values fit the pattern `<duplicate id><string len>`.
	var request_id = null
	var has_request_id = reader.read_option_tag()
	if has_request_id:
		request_id = reader.read_u32()
	var query_set_id: int = reader.read_u32()
	if reader.remaining_bytes() >= 8:
		var duplicate_id_candidate: int = reader.peek_u32()
		var string_len_after_duplicate: int = reader.peek_u32(4)
		var fits_duplicate_shape: bool = string_len_after_duplicate <= (reader.remaining_bytes() - 8)
		var duplicate_matches_id: bool = duplicate_id_candidate == query_set_id or (
			request_id != null and duplicate_id_candidate == int(request_id)
		)
		if duplicate_matches_id and fits_duplicate_shape:
			var duplicate_request_id: int = reader.read_u32()
			if request_id == null:
				request_id = duplicate_request_id

	return {
		"kind": "SubscriptionError",
		"tag": tag,
		"request_id": request_id,
		"query_set_id": query_set_id,
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
		if reader.parse_failed:
			break

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
		if reader.parse_failed:
			break
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
		if reader.parse_failed:
			break
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
		if reader.parse_failed:
			break
	return {
		"table_name": table_name,
		"updates": updates,
	}


static func _parse_table_update_rows(reader) -> Dictionary:
	var variant_tag = reader.read_u8()
	match variant_tag:
		0:
			var inserts = _parse_bsatn_row_list(reader)
			if reader.parse_failed:
				return {
					"variant": "PersistentTable",
					"insert_row_payloads": [],
					"delete_row_payloads": [],
				}
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
	if reader.parse_failed:
		return {
			"size_hint": size_hint,
			"rows_data": PackedByteArray(),
			"row_payloads": [],
		}
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
			# Observed pinned 2.1.0 wire: row-size-hint tag is either 0
			# (FixedSize) or 1 (RowOffsets). An unknown tag means the reader
			# has drifted; the existing `return {"kind":"Unknown"}` shape let
			# downstream iterations (`_split_bsatn_rows`, the surrounding
			# TransactionUpdate/ReducerResult loops) walk on garbage bytes.
			# Mark the reader so `_finalize_parsed_message` converts the
			# top-level result into a routable ProtocolError instead of a
			# best-effort-parsed frame.
			push_error("Unsupported BSATN row size hint tag %d." % hint_tag)
			reader.parse_failed = true
			reader.parse_error_message = "Unsupported BSATN row size hint tag %d." % hint_tag
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
				if reader.parse_failed:
					break
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


static func _finalize_parsed_message(message: Dictionary, reader, tag: int, payload: PackedByteArray, context: String) -> Dictionary:
	# Parse-failure propagation: `_parse_row_size_hint`'s unknown branch sets
	# `reader.parse_failed` so the top-level result becomes a routable
	# ProtocolError rather than a best-effort-parsed TransactionUpdate /
	# ReducerResult whose downstream iterations walked on garbage bytes.
	if reader.parse_failed:
		return _protocol_error(
			"%s parse failed: %s" % [context, String(reader.parse_error_message)],
			tag,
			payload
		)
	if reader.has_more():
		return _protocol_error(
			"%s parse drift: %d trailing byte(s) remain after decode." % [context, reader.remaining_bytes()],
			tag,
			payload
		)
	return message


static func _protocol_error(error_message: String, tag: int, payload: PackedByteArray) -> Dictionary:
	push_error(error_message)
	return {
		"kind": "ProtocolError",
		"tag": tag,
		"error_message": error_message,
		"raw_payload": payload.duplicate(),
	}


static func _raw_message(kind: String, tag: int, payload: PackedByteArray) -> Dictionary:
	return {
		"kind": kind,
		"tag": tag,
		"raw_payload": payload.slice(1, payload.size()),
	}

class_name GdscriptConnectionProtocol

const BsatnReaderScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/bsatn_reader.gd")
const BsatnWriterScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/bsatn_writer.gd")

const SUBPROTOCOL_BSATN := "v1.bsatn.spacetimedb"
const DEFAULT_QUERY_TOKEN_KEY := "token"

const CLIENT_MESSAGE_SUBSCRIBE := 0
const CLIENT_MESSAGE_UNSUBSCRIBE := 1

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
			return _raw_message("SubscribeApplied", tag, payload)
		SERVER_MESSAGE_UNSUBSCRIBE_APPLIED:
			return _raw_message("UnsubscribeApplied", tag, payload)
		SERVER_MESSAGE_SUBSCRIPTION_ERROR:
			return _raw_message("SubscriptionError", tag, payload)
		SERVER_MESSAGE_TRANSACTION_UPDATE:
			return _raw_message("TransactionUpdate", tag, payload)
		SERVER_MESSAGE_ONE_OFF_QUERY_RESULT:
			return _raw_message("OneOffQueryResult", tag, payload)
		SERVER_MESSAGE_REDUCER_RESULT:
			return _raw_message("ReducerResult", tag, payload)
		SERVER_MESSAGE_PROCEDURE_RESULT:
			return _raw_message("ProcedureResult", tag, payload)
		_:
			return _raw_message("Unknown", tag, payload)


static func fixed_width_bytes_to_hex(bytes: PackedByteArray) -> String:
	var pieces: Array[String] = []
	for index in range(bytes.size() - 1, -1, -1):
		pieces.append("%02X" % bytes[index])
	return "".join(pieces)


static func _raw_message(kind: String, tag: int, payload: PackedByteArray) -> Dictionary:
	return {
		"kind": kind,
		"tag": tag,
		"raw_payload": payload.slice(1, payload.size()),
	}

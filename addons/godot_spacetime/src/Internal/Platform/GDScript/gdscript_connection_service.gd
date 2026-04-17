class_name GdscriptConnectionService

signal state_changed(status)
signal connection_opened(event)
signal connection_closed(event)
signal protocol_message(message)
signal subscription_applied(event)
signal subscription_failed(event)
signal row_changed(event)
signal reducer_call_succeeded(event)
signal reducer_call_failed(event)

const ConnectionProtocolScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/connection_protocol.gd")
const FileTokenStoreScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/file_token_store.gd")
const ReconnectPolicyScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/reconnect_policy.gd")
const SubscriptionHandleScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_subscription_handle.gd")
const SubscriptionRegistryScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_subscription_registry.gd")
const CacheStoreScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_cache_store.gd")

const STATE_DISCONNECTED := "Disconnected"
const STATE_CONNECTING := "Connecting"
const STATE_CONNECTED := "Connected"
const STATE_DEGRADED := "Degraded"

const AUTH_NONE := "None"
const AUTH_TOKEN_RESTORED := "TokenRestored"
const AUTH_AUTH_FAILED := "AuthFailed"
const AUTH_CONNECT_FAILED := "ConnectFailed"
const AUTH_TOKEN_EXPIRED := "TokenExpired"

const CLOSE_REASON_CLEAN := "Clean"
const CLOSE_REASON_ERROR := "Error"

var _current_status: Dictionary = {}
var _reconnect_policy = ReconnectPolicyScript.new()
var _subscription_registry = SubscriptionRegistryScript.new()
var _cache_store = CacheStoreScript.new()
var _token_store = null
var _socket: WebSocketPeer = null
var _websocket_factory: Callable = Callable()
var _host: String = ""
var _database: String = ""
var _explicit_credentials: String = ""
var _session_token: String = ""
var _credentials_provided: bool = false
var _restored_from_store: bool = false
var _disconnect_requested: bool = false
var _disconnect_description: String = "DISCONNECTED — not connected to SpacetimeDB"
var _transport_request: Dictionary = {}
var _next_retry_at_seconds: float = -1.0
var _active_compression_mode: String = "None"
var _last_transport_error: String = ""
var _ever_connected_this_cycle: bool = false
var _prefer_query_token: bool = false
var _query_token_key: String = ConnectionProtocolScript.DEFAULT_QUERY_TOKEN_KEY
var _next_request_id: int = 1
var _next_handle_id: int = 1
# request_id -> handle
var _pending_subscriptions: Dictionary = {}
# new_handle_id -> old_handle_id
var _pending_replacements: Dictionary = {}
var _authoritative_handle_id: int = -1
# request_id -> {invocation_id: String, reducer_name: String, called_at: float}
var _pending_reducer_calls: Dictionary = {}
var _next_invocation_id: int = 1

const REDUCER_RECOVERY_GUIDANCE_FAILED := "Check the reducer inputs or server-side rules before retrying or showing a player-facing error."
const REDUCER_RECOVERY_GUIDANCE_OUT_OF_ENERGY := "Back off and retry later, or tell the player the action is temporarily unavailable."
const REDUCER_RECOVERY_GUIDANCE_UNKNOWN := "Do not retry automatically. Surface a safe generic error and capture diagnostics for follow-up."


func _init(websocket_factory: Callable = Callable()) -> void:
	_websocket_factory = websocket_factory
	_current_status = _make_status(
		STATE_DISCONNECTED,
		"DISCONNECTED — not connected to SpacetimeDB",
		AUTH_NONE
	)


func get_current_status() -> Dictionary:
	return _current_status.duplicate(true)


func get_transport_request() -> Dictionary:
	return _transport_request.duplicate(true)


func configure_bindings(binding_metadata: Variant) -> int:
	return _cache_store.configure_bindings(binding_metadata)


func get_remote_tables():
	return _cache_store.get_remote_tables()


func get_rows(table_name: String) -> Array:
	return _cache_store.get_rows(table_name)


func subscribe(query_sqls: Array) -> Object:
	if String(_current_status.get("state", STATE_DISCONNECTED)) != STATE_CONNECTED:
		push_error(
			"Subscribe() requires an active Connected session. " +
			"Call open_connection() and wait for Connected before applying subscriptions."
		)
		return null

	if not _cache_store.has_bindings():
		push_error("Subscribe() requires binding metadata. Call configure_bindings() before applying subscriptions.")
		return null

	if not _pending_subscriptions.is_empty():
		push_error(
			"Subscribe() requires no in-flight subscriptions. " +
			"Wait for the current subscription_applied event before calling subscribe() again."
		)
		return null

	if _authoritative_handle_id != -1:
		push_error(
			"Subscribe() requires no authoritative subscription. " +
			"Use replace_subscription() to overlap-first replace the live query set."
		)
		return null

	var clean_queries := _validate_query_sqls(query_sqls, "Subscribe()")
	if clean_queries.is_empty():
		return null

	return _begin_subscription(clean_queries)


func unsubscribe(handle: Object) -> void:
	var subscription_handle = _as_subscription_handle(handle, "Unsubscribe()")
	if subscription_handle == null:
		return

	if String(subscription_handle.status) in [
		SubscriptionHandleScript.STATUS_CLOSED,
		SubscriptionHandleScript.STATUS_SUPERSEDED,
	]:
		return

	_remove_pending_replacement_references(subscription_handle.handle_id)
	# query_set_id == request_id by construction (_begin_subscription passes request_id as query_set_id_value)
	_pending_subscriptions.erase(subscription_handle.query_set_id)
	_send_unsubscribe_for_query_set(subscription_handle.query_set_id)
	_subscription_registry.unregister(subscription_handle.handle_id)
	subscription_handle.close()

	if _authoritative_handle_id == subscription_handle.handle_id:
		_authoritative_handle_id = -1
		_cache_store.clear()


func replace_subscription(old_handle: Object, new_queries: Array) -> Object:
	if String(_current_status.get("state", STATE_DISCONNECTED)) != STATE_CONNECTED:
		push_error("ReplaceSubscription() requires an active Connected session.")
		return null

	var subscription_handle = _as_subscription_handle(old_handle, "ReplaceSubscription()")
	if subscription_handle == null:
		return null

	if String(subscription_handle.status) != SubscriptionHandleScript.STATUS_ACTIVE:
		push_error(
			"ReplaceSubscription() requires an Active subscription handle. " +
			"The provided handle is already terminal."
		)
		return null

	if _authoritative_handle_id != subscription_handle.handle_id:
		push_error(
			"ReplaceSubscription() requires the currently authoritative Active handle. " +
			"Use the live handle returned by subscribe() or the last successful replacement."
		)
		return null

	if _has_pending_replacement_for(subscription_handle.handle_id):
		push_error(
			"ReplaceSubscription() requires a currently authoritative handle without another " +
			"replacement already in flight."
		)
		return null

	var clean_queries := _validate_query_sqls(new_queries, "ReplaceSubscription()")
	if clean_queries.is_empty():
		return null

	return _begin_subscription(clean_queries, subscription_handle.handle_id)


func open_connection(host: String, database: String, options: Dictionary = {}) -> int:
	var clean_host := host.strip_edges()
	var clean_database := database.strip_edges()
	if clean_host.is_empty() or clean_database.is_empty():
		push_error("open_connection() requires non-empty host and database.")
		return ERR_INVALID_PARAMETER

	if String(_current_status.get("state", STATE_DISCONNECTED)) != STATE_DISCONNECTED:
		close_connection("DISCONNECTED — closing the previous session before reconnecting.")
		_dispose_socket_immediately()
		if String(_current_status.get("state", STATE_DISCONNECTED)) != STATE_DISCONNECTED:
			_finish_disconnect(
				"DISCONNECTED — closing the previous session before reconnecting.",
				AUTH_NONE,
				_ever_connected_this_cycle,
				CLOSE_REASON_CLEAN,
				""
			)

	_host = clean_host
	_database = clean_database
	_explicit_credentials = String(options.get("credentials", "")).strip_edges()
	_token_store = options.get("token_store", FileTokenStoreScript.new())
	_prefer_query_token = bool(options.get("prefer_query_token", false))
	_query_token_key = String(options.get("query_token_key", ConnectionProtocolScript.DEFAULT_QUERY_TOKEN_KEY))
	_active_compression_mode = _canonicalize_compression_mode(
		String(options.get("compression_mode", "None")).strip_edges()
	)
	_session_token = ""
	_last_transport_error = ""
	_disconnect_requested = false
	_disconnect_description = "DISCONNECTED — not connected to SpacetimeDB"
	_next_retry_at_seconds = -1.0
	_ever_connected_this_cycle = false
	_reconnect_policy.reset()

	_transition_to(
		STATE_CONNECTING,
		"CONNECTING — opening a session to %s/%s" % [_host, _database],
		AUTH_NONE
	)

	var token := _resolve_initial_connect_token()
	var start_result := _start_transport(token)
	if start_result != OK:
		_handle_connect_failure("failed to start the connection: %s" % error_string(start_result))
		return start_result

	return OK


func close_connection(description: String = "DISCONNECTED — not connected to SpacetimeDB") -> void:
	_disconnect_description = description
	if String(_current_status.get("state", STATE_DISCONNECTED)) == STATE_DISCONNECTED:
		return

	_disconnect_requested = true
	_next_retry_at_seconds = -1.0
	_reconnect_policy.reset()

	if _socket == null:
		_finish_disconnect(description, AUTH_NONE, _ever_connected_this_cycle, CLOSE_REASON_CLEAN, "")
		return

	if _socket.get_ready_state() == WebSocketPeer.STATE_CLOSED:
		_finish_disconnect(description, AUTH_NONE, _ever_connected_this_cycle, CLOSE_REASON_CLEAN, "")
		return

	_socket.close()


func advance(_delta: float = 0.0) -> void:
	if _socket != null:
		_socket.poll()
		_process_socket_state()

	if String(_current_status.get("state", STATE_DISCONNECTED)) == STATE_DEGRADED \
	and _socket == null \
	and _next_retry_at_seconds >= 0.0 \
	and _now_seconds() >= _next_retry_at_seconds:
		_next_retry_at_seconds = -1.0
		var retry_token := _resolve_retry_token()
		var retry_result := _start_transport(retry_token)
		if retry_result != OK:
			_schedule_retry_or_disconnect(
				"failed to start the connection: %s" % error_string(retry_result)
			)


func send_protocol_message(tag: int, payload_writer: Callable = Callable()) -> int:
	if _socket == null or String(_current_status.get("state", STATE_DISCONNECTED)) != STATE_CONNECTED:
		return ERR_UNAVAILABLE

	var payload := ConnectionProtocolScript.encode_client_message(tag, payload_writer)
	return _socket.put_packet(payload)


func invoke_reducer(reducer_name: String, args_bytes: PackedByteArray) -> String:
	if String(_current_status.get("state", STATE_DISCONNECTED)) != STATE_CONNECTED:
		push_error(
			"invoke_reducer() requires an active Connected session. " +
			"Call open_connection() and wait for Connected before invoking reducers."
		)
		return ""

	var clean_reducer_name := reducer_name.strip_edges()
	if clean_reducer_name.is_empty():
		push_error("invoke_reducer() requires a non-empty reducer_name.")
		return ""

	var invocation_id := str(_next_invocation_id)
	_next_invocation_id += 1

	var called_at := Time.get_unix_time_from_system()
	var request_id := _reserve_request_id()

	_pending_reducer_calls[request_id] = {
		"invocation_id": invocation_id,
		"reducer_name": clean_reducer_name,
		"called_at": called_at,
	}

	var send_result := send_protocol_message(
		ConnectionProtocolScript.CLIENT_MESSAGE_CALL_REDUCER,
		func(writer) -> void:
			writer.write_u32(request_id)
			writer.write_u32(0)
			writer.write_string(clean_reducer_name)
			writer.write_bytes(args_bytes)
	)
	if send_result != OK:
		_pending_reducer_calls.erase(request_id)
		push_error("invoke_reducer() failed to send the wire payload: %s" % error_string(send_result))
		return ""

	return invocation_id


func force_transport_fault_for_testing(reason: String = "simulated transport fault") -> void:
	if String(_current_status.get("state", STATE_DISCONNECTED)) not in [STATE_CONNECTED, STATE_DEGRADED]:
		return

	_schedule_retry_or_disconnect(reason)


func _process_socket_state() -> void:
	if _socket == null:
		return

	match _socket.get_ready_state():
		WebSocketPeer.STATE_OPEN:
			_drain_packets()
		WebSocketPeer.STATE_CLOSING:
			pass
		WebSocketPeer.STATE_CLOSED:
			var reason := _socket.get_close_reason().strip_edges()
			if reason.is_empty():
				var close_code := _socket.get_close_code()
				if close_code != -1:
					reason = "websocket closed with code %d" % close_code
			if reason.is_empty():
				reason = _last_transport_error if not _last_transport_error.is_empty() else "websocket closed"
			_handle_socket_closed(reason)


func _drain_packets() -> void:
	while _socket != null \
	and _socket.get_ready_state() == WebSocketPeer.STATE_OPEN \
	and _socket.get_available_packet_count() > 0:
		var packet := _socket.get_packet()
		var message := ConnectionProtocolScript.parse_server_message(packet, _active_compression_mode != "None")
		emit_signal("protocol_message", message.duplicate(true))
		match String(message.get("kind", "")):
			"InitialConnection":
				_handle_initial_connection(message)
			"SubscribeApplied":
				_handle_subscribe_applied(message)
			"SubscriptionError":
				_handle_subscription_error(message)
			"TransactionUpdate":
				_handle_transaction_update(message)
			"ReducerResult":
				_handle_reducer_result(message)


func _handle_initial_connection(message: Dictionary) -> void:
	_session_token = String(message.get("token", ""))
	if _token_store != null and not _session_token.is_empty():
		_token_store.store_token(_session_token)

	_ever_connected_this_cycle = true
	_reconnect_policy.reset()
	_last_transport_error = ""

	var auth_state := AUTH_TOKEN_RESTORED if _credentials_provided else AUTH_NONE
	_restored_from_store = false

	if String(_current_status.get("state", STATE_DISCONNECTED)) == STATE_DEGRADED:
		_transition_to(
			STATE_CONNECTED,
			"CONNECTED — active session established after recovery",
			auth_state
		)
	else:
		var description := "CONNECTED — active session established"
		if _credentials_provided:
			description = "CONNECTED — authenticated session established"
		_transition_to(STATE_CONNECTED, description, auth_state)

	emit_signal("connection_opened", {
		"host": _host,
		"database": _database,
		"identity": String(message.get("identity", "")),
		"connection_id": String(message.get("connection_id", "")),
		"connected_at_unix_time": Time.get_unix_time_from_system(),
	})


func _handle_socket_closed(reason: String) -> void:
	_socket = null
	if _disconnect_requested:
		_finish_disconnect(
			_disconnect_description,
			AUTH_NONE,
			_ever_connected_this_cycle,
			CLOSE_REASON_CLEAN,
			""
		)
		return

	if String(_current_status.get("state", STATE_DISCONNECTED)) == STATE_CONNECTING:
		_handle_connect_failure(reason)
		return

	if String(_current_status.get("state", STATE_DISCONNECTED)) in [STATE_CONNECTED, STATE_DEGRADED]:
		_schedule_retry_or_disconnect(reason)


func _handle_connect_failure(error_message: String) -> void:
	_last_transport_error = error_message
	_dispose_socket_immediately()

	if _restored_from_store:
		_clear_rejected_restored_token()
		_finish_disconnect(
			"DISCONNECTED — stored token was rejected: %s" % error_message,
			AUTH_TOKEN_EXPIRED,
			false,
			"",
			""
		)
		return

	if _credentials_provided:
		var auth_state := AUTH_AUTH_FAILED if _is_likely_auth_error(error_message) else AUTH_CONNECT_FAILED
		var label := "authentication failed" if auth_state == AUTH_AUTH_FAILED else "connection failed (credentials were provided but the cause is ambiguous)"
		_finish_disconnect(
			"DISCONNECTED — %s: %s" % [label, error_message],
			auth_state,
			false,
			"",
			""
		)
		return

	_finish_disconnect(
		"DISCONNECTED — failed to connect: %s" % error_message,
		AUTH_NONE,
		false,
		"",
		""
	)


func _schedule_retry_or_disconnect(error_message: String) -> void:
	_last_transport_error = error_message
	var retry := _reconnect_policy.try_begin_retry()
	if bool(retry.get("ok", false)):
		var attempt_number := int(retry.get("attempt_number", 0))
		var delay_seconds := float(retry.get("delay_seconds", 0.0))
		var degraded_description := "DEGRADED — session experiencing issues; reconnecting (attempt %d/%d, backoff %ss): %s" % [
			attempt_number,
			_reconnect_policy.max_attempts,
			_format_delay_seconds(delay_seconds),
			error_message,
		]
		if String(_current_status.get("state", STATE_DISCONNECTED)) == STATE_DEGRADED:
			_refresh_status(degraded_description, AUTH_NONE)
		else:
			_transition_to(STATE_DEGRADED, degraded_description, AUTH_NONE)

		_next_retry_at_seconds = _now_seconds() + delay_seconds
		_reset_pending_reducer_runtime()
		_dispose_socket_immediately()
		return

	var auth_state := _classify_disconnect_auth_state(error_message)
	_finish_disconnect(
		"DISCONNECTED — connection lost: %s" % error_message,
		auth_state,
		true,
		CLOSE_REASON_ERROR,
		error_message
	)


func _finish_disconnect(
	description: String,
	auth_state: String,
	emit_close_event: bool,
	close_reason: String,
	error_message: String
) -> void:
	_dispose_socket_immediately()
	_reconnect_policy.reset()
	_next_retry_at_seconds = -1.0
	_disconnect_requested = false
	_transport_request = {}
	_reset_subscription_runtime()
	_transition_to(STATE_DISCONNECTED, description, auth_state)

	if emit_close_event:
		emit_signal("connection_closed", {
			"close_reason": close_reason,
			"error_message": error_message,
			"closed_at_unix_time": Time.get_unix_time_from_system(),
		})

	_session_token = ""
	_credentials_provided = false
	_restored_from_store = false
	_ever_connected_this_cycle = false
	_last_transport_error = ""


func _start_transport(token: String) -> int:
	var allow_header_auth := not OS.has_feature("web")
	_transport_request = ConnectionProtocolScript.build_transport_request(
		_host,
		_database,
		token,
		allow_header_auth,
		_prefer_query_token,
		_query_token_key
	)

	var socket: WebSocketPeer = _create_socket()
	socket.supported_protocols = ConnectionProtocolScript.make_supported_protocols()
	var headers: PackedStringArray = _transport_request.get("headers", PackedStringArray())
	if not headers.is_empty():
		socket.handshake_headers = headers

	var connect_result := socket.connect_to_url(String(_transport_request.get("url", "")))
	if connect_result != OK:
		return connect_result

	_socket = socket
	return OK


func _resolve_initial_connect_token() -> String:
	_credentials_provided = false
	_restored_from_store = false

	if not _explicit_credentials.is_empty():
		_credentials_provided = true
		return _explicit_credentials

	if _token_store == null:
		return ""

	var stored_token := String(_token_store.get_token()).strip_edges()
	if _token_store.last_error_message.is_empty():
		if not stored_token.is_empty():
			_credentials_provided = true
			_restored_from_store = true
			return stored_token

	return ""


func _resolve_retry_token() -> String:
	_credentials_provided = false
	_restored_from_store = false

	if not _session_token.is_empty():
		_credentials_provided = true
		return _session_token

	if not _explicit_credentials.is_empty():
		_credentials_provided = true
		return _explicit_credentials

	return ""


func _classify_disconnect_auth_state(error_message: String) -> String:
	if not _credentials_provided:
		return AUTH_NONE
	if _restored_from_store:
		return AUTH_TOKEN_EXPIRED
	return AUTH_AUTH_FAILED if _is_likely_auth_error(error_message) else AUTH_CONNECT_FAILED


func _clear_rejected_restored_token() -> void:
	if _token_store != null:
		_token_store.clear_token()
	_session_token = ""


func _handle_subscribe_applied(message: Dictionary) -> void:
	var request_id := int(message.get("request_id", -1))
	var handle = _pending_subscriptions.get(request_id)
	if handle == null:
		return

	_pending_subscriptions.erase(request_id)

	var snapshot := _cache_store.build_snapshot(message.get("tables", []))
	var row_events := _cache_store.commit_snapshot(snapshot)

	if _pending_replacements.has(handle.handle_id):
		var old_handle_id := int(_pending_replacements[handle.handle_id])
		_pending_replacements.erase(handle.handle_id)
		var old_handle = _subscription_registry.try_get_handle(old_handle_id)
		if old_handle != null:
			_send_unsubscribe_for_query_set(old_handle.query_set_id)
			old_handle.supersede()
			_subscription_registry.unregister(old_handle_id)

	_authoritative_handle_id = handle.handle_id
	emit_signal("subscription_applied", {
		"handle_id": handle.handle_id,
		"applied_at_unix_time": Time.get_unix_time_from_system(),
	})
	_emit_row_changed_events(row_events)


func _handle_subscription_error(message: Dictionary) -> void:
	var handle = null
	var request_id = message.get("request_id")
	if request_id != null:
		handle = _pending_subscriptions.get(int(request_id))
		_pending_subscriptions.erase(int(request_id))

	if handle == null:
		handle = _subscription_registry.find_by_query_set_id(int(message.get("query_set_id", -1)))

	if handle == null:
		return

	_remove_pending_replacement_references(handle.handle_id)
	_send_unsubscribe_for_query_set(handle.query_set_id)
	_subscription_registry.unregister(handle.handle_id)
	handle.close()

	if _authoritative_handle_id == handle.handle_id:
		_authoritative_handle_id = -1
		_cache_store.clear()

	emit_signal("subscription_failed", {
		"handle_id": handle.handle_id,
		"error_message": String(message.get("error_message", "")),
		"failed_at_unix_time": Time.get_unix_time_from_system(),
	})


func _handle_transaction_update(message: Dictionary) -> void:
	if _authoritative_handle_id == -1:
		return

	var authoritative_handle = _subscription_registry.try_get_handle(_authoritative_handle_id)
	if authoritative_handle == null:
		return

	var relevant_updates: Array = []
	for query_set_update_variant in message.get("query_sets", []):
		var query_set_update: Dictionary = query_set_update_variant
		if int(query_set_update.get("query_set_id", -1)) == int(authoritative_handle.query_set_id):
			relevant_updates.append(query_set_update)

	if relevant_updates.is_empty():
		return

	_emit_row_changed_events(_cache_store.apply_transaction_updates(relevant_updates))


func _handle_reducer_result(message: Dictionary) -> void:
	var request_id := int(message.get("request_id", -1))
	var pending = _pending_reducer_calls.get(request_id)
	_pending_reducer_calls.erase(request_id)

	var invocation_id: String
	var reducer_name: String
	var called_at: float

	if pending != null:
		invocation_id = String(pending.get("invocation_id", "untracked"))
		reducer_name = String(pending.get("reducer_name", String(message.get("reducer_name", "unknown"))))
		called_at = float(pending.get("called_at", Time.get_unix_time_from_system()))
	else:
		invocation_id = "untracked-" + str(_next_invocation_id)
		_next_invocation_id += 1
		reducer_name = String(message.get("reducer_name", "unknown"))
		called_at = Time.get_unix_time_from_system()

	var now := Time.get_unix_time_from_system()
	var status := String(message.get("status", "Unknown"))
	match status:
		"Committed":
			emit_signal("reducer_call_succeeded", {
				"reducer_name": reducer_name,
				"invocation_id": invocation_id,
				"called_at_unix_time": called_at,
				"completed_at_unix_time": now,
			})
		"Failed":
			emit_signal("reducer_call_failed", {
				"reducer_name": reducer_name,
				"invocation_id": invocation_id,
				"called_at_unix_time": called_at,
				"failed_at_unix_time": now,
				"error_message": String(message.get("error_message", "Reducer failed")),
				"failure_category": "Failed",
				"recovery_guidance": REDUCER_RECOVERY_GUIDANCE_FAILED,
			})
		"OutOfEnergy":
			emit_signal("reducer_call_failed", {
				"reducer_name": reducer_name,
				"invocation_id": invocation_id,
				"called_at_unix_time": called_at,
				"failed_at_unix_time": now,
				"error_message": "Out of energy — reducer not executed",
				"failure_category": "OutOfEnergy",
				"recovery_guidance": REDUCER_RECOVERY_GUIDANCE_OUT_OF_ENERGY,
			})
		_:
			emit_signal("reducer_call_failed", {
				"reducer_name": reducer_name,
				"invocation_id": invocation_id,
				"called_at_unix_time": called_at,
				"failed_at_unix_time": now,
				"error_message": "Unexpected reducer status: %s" % status,
				"failure_category": "Unknown",
				"recovery_guidance": REDUCER_RECOVERY_GUIDANCE_UNKNOWN,
			})


func _begin_subscription(query_sqls: Array, replaced_handle_id: int = -1) -> Object:
	var request_id := _reserve_request_id()
	var handle_id := _next_handle_id
	_next_handle_id += 1

	var handle = SubscriptionHandleScript.new(handle_id, request_id, query_sqls)
	_pending_subscriptions[request_id] = handle
	_subscription_registry.register(handle)

	if replaced_handle_id != -1:
		_pending_replacements[handle.handle_id] = replaced_handle_id

	var send_result := _send_subscribe_request(handle)
	if send_result != OK:
		_pending_subscriptions.erase(request_id)
		_pending_replacements.erase(handle.handle_id)
		_subscription_registry.unregister(handle.handle_id)
		handle.close()
		push_error("Subscribe() failed to send the wire payload: %s" % error_string(send_result))
		return null

	return handle


func _send_subscribe_request(handle) -> int:
	return send_protocol_message(
		ConnectionProtocolScript.CLIENT_MESSAGE_SUBSCRIBE,
		func(writer) -> void:
			writer.write_u32(int(handle.query_set_id))
			writer.write_u32(int(handle.query_set_id))
			writer.write_array_len(handle.query_sqls.size())
			for sql_variant in handle.query_sqls:
				writer.write_string(String(sql_variant))
	)


func _send_unsubscribe_for_query_set(query_set_id: int) -> void:
	if query_set_id < 0:
		return

	if String(_current_status.get("state", STATE_DISCONNECTED)) != STATE_CONNECTED:
		return

	var request_id := _reserve_request_id()
	send_protocol_message(
		ConnectionProtocolScript.CLIENT_MESSAGE_UNSUBSCRIBE,
		func(writer) -> void:
			writer.write_u32(request_id)
			writer.write_u32(query_set_id)
			writer.write_u32(0)
	)


func _validate_query_sqls(query_sqls: Array, caller_name: String) -> Array:
	if query_sqls == null or query_sqls.is_empty():
		push_error("%s requires a non-empty query set." % caller_name)
		return []

	var clean_queries: Array = []
	for sql_variant in query_sqls:
		var sql := String(sql_variant).strip_edges()
		if sql.is_empty():
			push_error("%s requires every query string to be non-empty." % caller_name)
			return []
		clean_queries.append(sql)

	return clean_queries


func _reserve_request_id() -> int:
	var request_id := _next_request_id
	_next_request_id += 1
	return request_id


func _as_subscription_handle(handle: Object, caller_name: String):
	if handle == null:
		push_error("%s requires a valid subscription handle." % caller_name)
		return null

	for required_method in ["close", "supersede"]:
		if not handle.has_method(required_method):
			push_error("%s requires a valid subscription handle." % caller_name)
			return null

	for required_prop in ["handle_id", "query_set_id", "status"]:
		if not (required_prop in handle):
			push_error("%s requires a valid subscription handle." % caller_name)
			return null

	return handle


func _has_pending_replacement_for(old_handle_id: int) -> bool:
	return _pending_replacements.values().has(old_handle_id)


func _remove_pending_replacement_references(handle_id: int) -> void:
	var to_remove: Array = []
	for pending_handle_id_variant in _pending_replacements.keys():
		var pending_handle_id := int(pending_handle_id_variant)
		var replaced_handle_id := int(_pending_replacements[pending_handle_id_variant])
		if pending_handle_id == handle_id or replaced_handle_id == handle_id:
			to_remove.append(pending_handle_id)

	for pending_handle_id in to_remove:
		_pending_replacements.erase(pending_handle_id)


func _emit_row_changed_events(row_events: Array) -> void:
	for row_event_variant in row_events:
		emit_signal("row_changed", row_event_variant)


func _reset_subscription_runtime() -> void:
	_pending_subscriptions.clear()
	_pending_replacements.clear()
	_authoritative_handle_id = -1
	_next_request_id = 1
	_next_handle_id = 1
	_subscription_registry.clear()
	_cache_store.clear()
	_reset_pending_reducer_runtime()


func _reset_pending_reducer_runtime() -> void:
	_pending_reducer_calls.clear()
	_next_invocation_id = 1


func _create_socket() -> WebSocketPeer:
	if not _websocket_factory.is_null():
		return _websocket_factory.call()
	return WebSocketPeer.new()


func _dispose_socket_immediately() -> void:
	if _socket == null:
		return

	var socket := _socket
	_socket = null
	if socket.get_ready_state() != WebSocketPeer.STATE_CLOSED:
		socket.close(-1)


func _transition_to(state: String, description: String, auth_state: String) -> void:
	var current_state := String(_current_status.get("state", STATE_DISCONNECTED))
	if not _is_valid_transition(current_state, state):
		push_error("Illegal connection transition: %s -> %s." % [current_state, state])
		return

	_current_status = _make_status(state, description, auth_state)
	emit_signal("state_changed", _current_status.duplicate(true))


func _refresh_status(description: String, auth_state: String) -> void:
	_current_status = _make_status(
		String(_current_status.get("state", STATE_DISCONNECTED)),
		description,
		auth_state
	)
	emit_signal("state_changed", _current_status.duplicate(true))


func _make_status(state: String, description: String, auth_state: String) -> Dictionary:
	return {
		"state": state,
		"description": description,
		"auth_state": auth_state,
		"active_compression_mode": _active_compression_mode,
	}


func _is_valid_transition(current: String, next: String) -> bool:
	match current:
		STATE_DISCONNECTED:
			return next == STATE_CONNECTING
		STATE_CONNECTING:
			return next == STATE_CONNECTED or next == STATE_DISCONNECTED
		STATE_CONNECTED:
			return next == STATE_DEGRADED or next == STATE_DISCONNECTED
		STATE_DEGRADED:
			return next == STATE_CONNECTED or next == STATE_DISCONNECTED
		_:
			return false


func _canonicalize_compression_mode(requested_mode: String) -> String:
	if requested_mode == "Brotli":
		return "Gzip"
	if requested_mode == "Gzip":
		return "Gzip"
	return "None"


func _is_likely_auth_error(error_message: String) -> bool:
	var lowered := error_message.to_lower()
	for token in ["401", "403", "unauthorized", "forbidden", "auth", "jwt", "token"]:
		if lowered.find(token) != -1:
			return true
	return false


func _format_delay_seconds(delay_seconds: float) -> String:
	if is_equal_approx(delay_seconds, round(delay_seconds)):
		return str(int(round(delay_seconds)))
	return str(delay_seconds)


func _now_seconds() -> float:
	return Time.get_ticks_msec() / 1000.0

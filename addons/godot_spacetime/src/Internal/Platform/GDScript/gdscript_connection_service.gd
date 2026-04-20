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

# Cap on packets processed per `_drain_packets` invocation (one `_process` tick).
# At 60 Hz this yields ~7680 packets/sec drained, comfortably above pinned 2.1.0
# server per-second rates while keeping per-tick wall time bounded. A backlog
# larger than the cap (reconnect against a live table, adversarial flood) drains
# across subsequent ticks instead of freezing the main thread. Tune via a future
# spec if a real workload needs it.
const DRAIN_PACKETS_PER_TICK: int = 128

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
	# Pending subscriptions are keyed by request_id. While a subscribe is still
	# in flight `_begin_subscription()` seeds `query_set_id` from the same
	# value; `_handle_subscribe_applied()` may later rewrite the live handle's
	# `query_set_id` from the server ack after the pending entry is gone.
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

	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb (see
	# tests/fixtures/gdscript_wire/call_reducer_ping_insert_sent.bin):
	#   tag(u8=3) | RequestId(u32) | Flags(u8) | Reducer(string) | Args(bytes)
	# Delegates to `ConnectionProtocolScript.encode_call_reducer` so the wire
	# shape matches the pinned SDK byte-for-byte.
	if _socket == null or String(_current_status.get("state", STATE_DISCONNECTED)) != STATE_CONNECTED:
		_pending_reducer_calls.erase(request_id)
		push_error("invoke_reducer() failed to send the wire payload: %s" % error_string(ERR_UNAVAILABLE))
		return ""
	var call_payload := ConnectionProtocolScript.encode_call_reducer(request_id, clean_reducer_name, args_bytes)
	var send_result := _socket.put_packet(call_payload)
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
	var drained := 0
	while _socket != null \
	and _socket.get_ready_state() == WebSocketPeer.STATE_OPEN \
	and _socket.get_available_packet_count() > 0:
		if drained >= DRAIN_PACKETS_PER_TICK:
			break
		drained += 1
		var packet := _socket.get_packet()
		# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb: every frame carries
		# its own compression byte prefix. The session-level
		# `_active_compression_mode` hint is still consulted, but the v2 parser
		# treats each frame's envelope byte as authoritative instead of forcing
		# a legacy whole-frame gzip path whenever the session requested Gzip.
		var expects_compressed := _active_compression_mode != "None"
		var message := ConnectionProtocolScript.parse_server_message(packet, expects_compressed)
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
			"ProtocolError":
				var parse_error := String(message.get("error_message", "protocol parse error"))
				if String(_current_status.get("state", STATE_DISCONNECTED)) == STATE_CONNECTING:
					_handle_connect_failure(parse_error)
				else:
					_schedule_retry_or_disconnect(parse_error)


func _handle_initial_connection(message: Dictionary) -> void:
	var parsed_token := String(message.get("token", ""))
	if not parsed_token.is_empty() and not _is_structurally_valid_jwt(parsed_token):
		push_error(
			"InitialConnection returned a malformed token; skipping persistence and treating reconnects as anonymous."
		)
		_session_token = ""
	else:
		_session_token = parsed_token
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


# Emission-ordering contract for `_finish_disconnect`:
#   1. state_changed first: `_transition_to` emits `DISCONNECTED` before any close event.
#   2. connection_closed second: emitted after the state transition when `emit_close_event`.
#
# Why this ordering: a `state_changed(DISCONNECTED)` handler that synchronously
# calls `open_connection(...)` triggers the new cycle's `state_changed(CONNECTING)`
# from inside the old cycle's teardown. The old cycle's `connection_closed` then
# lands AFTER the new cycle's `CONNECTING` — visible to observers as a spurious
# close during the reconnect. Flipping the order (emit close FIRST, then the
# state transition) would let the close handler itself re-enter `open_connection`
# while `_current_status` still reads a stale pre-disconnect value, which is
# worse. Keeping state-first makes the terminal state unambiguous and pushes
# the reentry wart into an explicit, documented corner.
#
# Workarounds for callers affected by the old-cycle-close-during-new-cycle
# ordering: (a) defer the reconnect to the `connection_closed` handler instead
# of `state_changed`, or (b) gate on `event.closed_at_unix_time` to recognize
# the event as belonging to the completed cycle. Flipping the emission order
# is intentionally rejected — see this spec's Ask First rule.
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
	# Clear session state BEFORE emitting state_changed/connection_closed so that
	# signal handlers can synchronously call open_connection() and have their
	# freshly-resolved credential flags (_restored_from_store, _credentials_provided)
	# survive this teardown.
	_session_token = ""
	_credentials_provided = false
	_restored_from_store = false
	_ever_connected_this_cycle = false
	_last_transport_error = ""
	_transition_to(STATE_DISCONNECTED, description, auth_state)

	if emit_close_event:
		emit_signal("connection_closed", {
			"close_reason": close_reason,
			"error_message": error_message,
			"closed_at_unix_time": Time.get_unix_time_from_system(),
		})


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

	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb: the pinned SDK always
	# appends `connection_id=<hex32>&compression=<mode>` to the subscribe URL.
	# Without these the server still completes the WebSocket handshake but
	# falls back to its legacy envelope which rejects SDK-shaped frames.
	var base_url := String(_transport_request.get("url", ""))
	var compression_label := _active_compression_mode
	if compression_label.is_empty():
		compression_label = "None"
	var url_separator := "&" if base_url.find("?") != -1 else "?"
	var v2_url := "%s%sconnection_id=%s&compression=%s" % [
		base_url,
		url_separator,
		_random_connection_id_hex(),
		compression_label,
	]
	_transport_request["url"] = v2_url

	var socket: WebSocketPeer = _create_socket()
	socket.supported_protocols = ConnectionProtocolScript.make_supported_protocols()
	var headers: PackedStringArray = _transport_request.get("headers", PackedStringArray())
	if not headers.is_empty():
		socket.handshake_headers = headers

	var connect_result := socket.connect_to_url(v2_url)
	if connect_result != OK:
		return connect_result

	_socket = socket
	return OK


func _random_connection_id_hex() -> String:
	# Mirror the upstream Unity SDK's `ConnectionId.Random()` behavior:
	# construct 16 pseudo-random bytes with a fresh RNG instance and render them
	# uppercase hex for the subscribe URL's `connection_id=` parameter.
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	var hex := ""
	for i in range(16):
		hex += "%02X" % (rng.randi() & 0xFF)
	return hex


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
	var query_set_id_variant = message.get("query_set_id", null)
	if typeof(query_set_id_variant) == TYPE_INT and int(query_set_id_variant) >= 0:
		handle.query_set_id = int(query_set_id_variant)

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

	# Defensive guard (round-2 hardening): `authoritative_handle.query_set_id`
	# is expected to be a non-negative integer once a handle is registered, but
	# a stale or future-refactored code path could leave the field at `-1`
	# (the `_authoritative_handle_id` sentinel wording would match). An int
	# comparison below with `qs_id == int(-1)` could then false-match a bundled
	# entry whose `query_set_id` was parsed as `-1`, leaking rows through to the
	# cache. Mirror the per-entry `qs_id < 0` guard on the authoritative side.
	if int(authoritative_handle.query_set_id) < 0:
		push_warning("Ignoring TransactionUpdate: authoritative handle has negative query_set_id")
		return

	# Defensive shape-checks (cluster-A hardening): a malformed TransactionUpdate
	# frame (non-Array `query_sets`, non-Dictionary entry, missing/negative
	# `query_set_id`) must NOT raise a Godot runtime error from a typed cast
	# mid-handler. The earlier `var query_set_update: Dictionary = query_set_update_variant`
	# cast aborted the receive loop instead of skipping the bad entry.
	var query_sets_variant = message.get("query_sets", [])
	if not (query_sets_variant is Array):
		push_warning("Ignoring malformed TransactionUpdate.query_sets (not an Array)")
		return
	var query_sets: Array = query_sets_variant

	# Round-2 hardening: per-entry `push_warning` for the three data-malformed
	# categories (non-Dictionary, missing `query_set_id`, non-integer
	# `query_set_id`) is an adversarial-bulk symptom — a single malformed bundle
	# with N bad entries produced N warnings. Collapse to one summary after the
	# loop. The registry-state signals (authoritative-side guard above,
	# `qs_id < 0` below) stay audible because they indicate state drift, not
	# payload malformation.
	var malformed_entry_count := 0
	var relevant_updates: Array = []
	for query_set_update_variant in query_sets:
		if not (query_set_update_variant is Dictionary):
			malformed_entry_count += 1
			continue
		var query_set_update: Dictionary = query_set_update_variant
		var qs_id_variant = query_set_update.get("query_set_id", -1)
		if typeof(qs_id_variant) != TYPE_INT:
			malformed_entry_count += 1
			continue
		var qs_id := int(qs_id_variant)
		if qs_id < 0:
			malformed_entry_count += 1
			continue
		if qs_id == int(authoritative_handle.query_set_id):
			relevant_updates.append(query_set_update)

	if malformed_entry_count > 0:
		push_warning("Skipped %d malformed entries in TransactionUpdate.query_sets" % malformed_entry_count)

	if relevant_updates.is_empty():
		return

	_emit_row_changed_events(_cache_store.apply_transaction_updates(relevant_updates))


func _handle_reducer_result(message: Dictionary) -> void:
	# Round-2 hardening: `message.get("request_id", -1)` can return a
	# Variant-shaped value (Dictionary / Array / PackedByteArray / String) when
	# the server frame is malformed. `int(dict_or_array)` raises a Godot runtime
	# error that aborts the receive loop; `int("abc")` silently coerces to `0`
	# which would false-match a pending-call entry at `request_id=0` (no path
	# today reserves id 0, but the bundled-path `query_set_id` guard closed the
	# exact same silent-coercion class — mirror that guard here). The typeof
	# check must run BEFORE `int()`.
	var request_id_variant = message.get("request_id", -1)
	if typeof(request_id_variant) != TYPE_INT:
		push_warning("Ignoring ReducerResult: non-integer request_id")
		return
	var request_id := int(request_id_variant)
	var pending = _pending_reducer_calls.get(request_id)
	_pending_reducer_calls.erase(request_id)

	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb: a successful ReducerResult
	# bundles a TransactionUpdate inside its `Ok(ReducerOk { ..., TransactionUpdate })`
	# payload rather than emitting a standalone TransactionUpdate frame. Apply the
	# bundled rows through the cache so the row_changed signal fires before the
	# reducer_call_succeeded signal — matching the legacy-v1 ordering contract.
	# Mirror the upstream Unity SDK's "parse the bundled TransactionUpdate" shape,
	# but keep this runtime's overlap-first replacement contract intact: a pending
	# replacement handle is registered before SubscribeApplied, yet the old handle
	# remains authoritative until that apply event arrives. Skip pending query sets
	# so reducer-side rows cannot leak into the live cache before replacement apply.
	# Defensive shape-checks (cluster-A hardening): a malformed ReducerResult
	# frame (non-Array `query_sets`, non-Dictionary entry, missing/negative
	# `query_set_id`) must NOT raise a Godot runtime error from a typed cast
	# mid-handler — that would abort before the surrounding
	# reducer_call_succeeded / reducer_call_failed emission below, which the
	# caller relies on to resolve the in-flight invocation.
	var query_sets_variant = message.get("query_sets", [])
	if not (query_sets_variant is Array):
		push_warning("Ignoring malformed ReducerResult.query_sets (not an Array)")
		query_sets_variant = []
	var query_sets: Array = query_sets_variant
	if not query_sets.is_empty() and _authoritative_handle_id != -1:
		# Round-2 hardening: collapse the three data-malformed per-entry warnings
		# (non-Dictionary, missing `query_set_id`, non-integer `query_set_id`)
		# into a single post-loop summary. The "unregistered `query_set_id`"
		# warning stays per-entry: it is a registry-state signal (race or drift
		# bug between subscription lifecycle and server-emitted bundles), not an
		# adversarial-bulk symptom.
		var malformed_entry_count := 0
		var relevant: Array = []
		for q_variant in query_sets:
			if not (q_variant is Dictionary):
				malformed_entry_count += 1
				continue
			var q: Dictionary = q_variant
			var qs_id_variant = q.get("query_set_id", -1)
			if typeof(qs_id_variant) != TYPE_INT:
				malformed_entry_count += 1
				continue
			var qs_id := int(qs_id_variant)
			if qs_id < 0:
				malformed_entry_count += 1
				continue
			var handle = _subscription_registry.find_by_query_set_id(qs_id)
			if handle == null:
				push_warning(
					"Dropped bundled query_set update with unregistered query_set_id %d" % qs_id
				)
			elif _pending_subscriptions.has(qs_id):
				continue
			else:
				relevant.append(q)
		if malformed_entry_count > 0:
			push_warning("Skipped %d malformed entries in ReducerResult.query_sets" % malformed_entry_count)
		if not relevant.is_empty():
			_emit_row_changed_events(_cache_store.apply_transaction_updates(relevant))

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

	# The pending-subscription map is keyed by request_id, so seed
	# `query_set_id` from the same value until the server's SubscribeApplied ack
	# confirms which live query_set_id it will use for subsequent bundles.
	var handle = SubscriptionHandleScript.new(handle_id, request_id, request_id, query_sqls)
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
	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb (see
	# tests/fixtures/gdscript_wire/subscribe_sent.bin):
	#   tag(u8=0) | RequestId(u32) | QuerySetId(u32) | QueryStrings(array<string>)
	# The legacy emitter wrote `query_set_id` twice and no request_id; that
	# frame was rejected by the v2 server. Delegates to the pure static
	# encoder so the wire test can re-derive the exact bytes.
	if _socket == null or String(_current_status.get("state", STATE_DISCONNECTED)) != STATE_CONNECTED:
		return ERR_UNAVAILABLE
	var payload := ConnectionProtocolScript.encode_subscribe(
		int(handle.request_id),
		int(handle.query_set_id),
		handle.query_sqls,
	)
	return _socket.put_packet(payload)


func _send_unsubscribe_for_query_set(query_set_id: int) -> void:
	if query_set_id < 0:
		return

	if String(_current_status.get("state", STATE_DISCONNECTED)) != STATE_CONNECTED:
		return

	# Observed spacetime 2.1.0 / v2.bsatn.spacetimedb (see
	# tests/fixtures/gdscript_wire/unsubscribe_sent.bin):
	#   tag(u8=1) | RequestId(u32) | QuerySetId(u32) | Flags(u8)
	# The legacy emitter wrote a trailing u32(0) instead of a u8; the v2
	# server expects 10 bytes total and rejects a 13-byte unsubscribe.
	# Fire-and-forget: the reserved request_id is written to the wire and
	# intentionally discarded. There is no `_pending_unsubscribes` map and no
	# `UnsubscribeApplied` handler today. A future correlation spec would add
	# both together so the reserved id can be resolved when the server acks.
	var request_id := _reserve_request_id()
	if _socket == null:
		return
	var payload := ConnectionProtocolScript.encode_unsubscribe(request_id, query_set_id)
	_socket.put_packet(payload)


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
	# Intentionally do NOT reset `_next_request_id` here. The counter is
	# monotonic for the life of this service instance so that a stale
	# SubscribeApplied / ReducerResult still queued in the WebSocket receive
	# buffer from a previous session cannot false-match a freshly reserved id
	# after a disconnect/reconnect. Disposal of the service (node _exit_tree)
	# is the only path that discards the counter. The wire encodes RequestId
	# as u32 (see `_send_unsubscribe_for_query_set` comment below for the
	# frame layout), so wrap happens at ~4.29e9 reservations — reachable only
	# on a service instance that churns subscriptions/reducers for years; a
	# wrap-guard story is tracked in `deferred-work.md`.
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


func _is_structurally_valid_jwt(token: String) -> bool:
	var parts := token.split(".")
	if parts.size() != 3:
		return false
	for part_variant in parts:
		var part := String(part_variant)
		if part.is_empty():
			return false
		if not _is_base64url_segment(part):
			return false
	return true


func _is_base64url_segment(segment: String) -> bool:
	for i in range(segment.length()):
		var code := segment.unicode_at(i)
		var is_upper := code >= 65 and code <= 90
		var is_lower := code >= 97 and code <= 122
		var is_digit := code >= 48 and code <= 57
		var is_symbol := code == 45 or code == 95
		if not (is_upper or is_lower or is_digit or is_symbol):
			return false
	return true


func _format_delay_seconds(delay_seconds: float) -> String:
	if is_equal_approx(delay_seconds, round(delay_seconds)):
		return str(int(round(delay_seconds)))
	return str(delay_seconds)


func _now_seconds() -> float:
	return Time.get_ticks_msec() / 1000.0

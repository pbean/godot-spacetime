extends SceneTree

# Godot-headless harness invoked by `tests/test_gdscript_wire_layouts.py`.
#
# Usage:
#   godot --headless --path <project> --script res://tests/fixtures/gdscript_wire/parse_fixture_harness.gd -- \
#     <fixture_path.bin> <mode>
#
# `mode` is one of:
#   parse_initial_connection
#   parse_subscribe_applied
#   parse_unsubscribe_applied
#   parse_reducer_result
#   encode_subscribe <request_id> <query_set_id> <queries_csv>
#   encode_unsubscribe <request_id> <query_set_id> <flags>
#   encode_call_reducer <request_id> <reducer_name> <args_hex>
#
# Emits the result as a single line "WIRE-HARNESS <json>" so the Python side
# can capture it.

const ProtocolScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/connection_protocol.gd")


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 1:
		_emit_error("missing mode argument")
		quit(2)
		return

	var mode := String(args[0])
	match mode:
		"parse_initial_connection":
			_run_parse_server_fixture(args, "InitialConnection")
		"parse_subscribe_applied":
			_run_parse_server_fixture(args, "SubscribeApplied")
		"parse_unsubscribe_applied":
			_run_parse_server_fixture(args, "UnsubscribeApplied")
		"parse_reducer_result":
			_run_parse_server_fixture(args, "ReducerResult")
		"encode_subscribe":
			_run_encode_subscribe(args)
		"encode_unsubscribe":
			_run_encode_unsubscribe(args)
		"encode_call_reducer":
			_run_encode_call_reducer(args)
		_:
			_emit_error("unknown mode: %s" % mode)
			quit(2)


func _run_parse_server_fixture(args: Array, expected_kind: String) -> void:
	if args.size() < 2:
		_emit_error("%s requires fixture path" % args[0])
		quit(2)
		return
	var path := String(args[1])
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		_emit_error("cannot open fixture: %s" % path)
		quit(2)
		return
	var data := file.get_buffer(file.get_length())
	file.close()

	var message: Dictionary = ProtocolScript.parse_server_message(data, false)
	if String(message.get("kind", "")) != expected_kind:
		_emit_error("expected kind=%s, got=%s for %s" % [
			expected_kind,
			String(message.get("kind", "")),
			path,
		])
		quit(3)
		return

	_emit_result(_flatten_message(message))
	quit(0)


func _run_encode_subscribe(args: Array) -> void:
	if args.size() < 4:
		_emit_error("encode_subscribe requires <request_id> <query_set_id> <queries_csv>")
		quit(2)
		return
	var request_id := int(args[1])
	var query_set_id := int(args[2])
	var queries_csv := String(args[3])
	var queries: Array = Array(queries_csv.split("||"))
	var bytes: PackedByteArray = ProtocolScript.encode_subscribe(request_id, query_set_id, queries)
	_emit_result({"hex": bytes.hex_encode(), "len": bytes.size()})
	quit(0)


func _run_encode_unsubscribe(args: Array) -> void:
	if args.size() < 4:
		_emit_error("encode_unsubscribe requires <request_id> <query_set_id> <flags>")
		quit(2)
		return
	var request_id := int(args[1])
	var query_set_id := int(args[2])
	var flags := int(args[3])
	var bytes: PackedByteArray = ProtocolScript.encode_unsubscribe(request_id, query_set_id, flags)
	_emit_result({"hex": bytes.hex_encode(), "len": bytes.size()})
	quit(0)


func _run_encode_call_reducer(args: Array) -> void:
	if args.size() < 4:
		_emit_error("encode_call_reducer requires <request_id> <reducer_name> <args_hex>")
		quit(2)
		return
	var request_id := int(args[1])
	var reducer_name := String(args[2])
	var args_hex := String(args[3])
	var args_bytes := _hex_to_bytes(args_hex)
	var bytes: PackedByteArray = ProtocolScript.encode_call_reducer(request_id, reducer_name, args_bytes)
	_emit_result({"hex": bytes.hex_encode(), "len": bytes.size()})
	quit(0)


func _hex_to_bytes(h: String) -> PackedByteArray:
	var bytes := PackedByteArray()
	if h.is_empty():
		return bytes
	if h.length() % 2 != 0:
		_emit_error("hex string must have even length: %s" % h)
		quit(2)
		return bytes
	for i in range(0, h.length(), 2):
		bytes.append(("0x%s" % h.substr(i, 2)).hex_to_int())
	return bytes


func _flatten_message(message: Dictionary) -> Dictionary:
	# Serialise the parser's return Dictionary into something JSON-safe so the
	# pytest side can assert deeply. PackedByteArray becomes hex; nested
	# Dictionaries recurse through the same helper.
	var out := {}
	for k_variant in message.keys():
		var k := String(k_variant)
		if k == "raw_payload":
			continue  # too chatty for JSON assertion
		var v: Variant = message[k_variant]
		out[k] = _jsonify(v)
	return out


func _jsonify(v: Variant) -> Variant:
	var t := typeof(v)
	if t == TYPE_PACKED_BYTE_ARRAY:
		return (v as PackedByteArray).hex_encode()
	if t == TYPE_DICTIONARY:
		var d := {}
		for k in (v as Dictionary).keys():
			d[String(k)] = _jsonify((v as Dictionary)[k])
		return d
	if t == TYPE_ARRAY:
		var arr := []
		for entry in (v as Array):
			arr.append(_jsonify(entry))
		return arr
	return v


func _emit_result(payload: Variant) -> void:
	print("WIRE-HARNESS %s" % JSON.stringify({
		"ok": true,
		"data": payload,
	}))


func _emit_error(msg: String) -> void:
	print("WIRE-HARNESS %s" % JSON.stringify({
		"ok": false,
		"error": msg,
	}))

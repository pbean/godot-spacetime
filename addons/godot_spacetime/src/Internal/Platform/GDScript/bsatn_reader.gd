class_name BsatnReader

var _buf: PackedByteArray
var _pos: int = 0
# Parse-failure sentinel — set by higher-level parsers (e.g.
# `connection_protocol.gd:_parse_row_size_hint`) when they hit an unknown
# variant tag that the pinned 2.1.0 wire does not declare. The top-level
# `_finalize_parsed_message` converts any message whose reader has this
# flag set into a routable ProtocolError rather than a best-effort-parsed
# frame that downstream iterations would walk on garbage bytes. The
# BsatnReader itself does not set this — its own buffer-underrun path
# still routes through `_fail`.
var parse_failed: bool = false
var parse_error_message: String = ""


func _init(data: PackedByteArray) -> void:
	_buf = data
	# Reset the parse-failure sentinel on every construction so a reader
	# instance cannot carry a stale ProtocolError across logically
	# independent parses. Reader instances are fresh-per-packet today; this
	# guards the invariant against a future pooled or peek-rewind caller.
	parse_failed = false
	parse_error_message = ""


func _fail(message: String) -> void:
	push_error(message)
	assert(false, message)
	# assert() is debug-only; len(int) raises a runtime error in release exports too.
	var invalid_length := 0
	len(invalid_length)


func _require_available(count: int) -> void:
	# Parse-failure re-entry guard: once a higher-level parser has marked the
	# reader with `parse_failed`, any subsequent read call — whether from the
	# same parser forgetting an outer guard, or a downstream helper walking on
	# already-corrupted state — must not re-enter `_fail`. `_fail` intentionally
	# raises in release builds via `len(int)`; re-entry after a clean
	# ProtocolError sentinel was already produced would turn a routable error
	# into a receive-loop-aborting crash. Early-return preserves `_pos` so the
	# surrounding `_finalize_parsed_message` path can still serialise a stable
	# ProtocolError from the existing `parse_error_message`.
	if parse_failed:
		return
	if _pos + count > _buf.size():
		_fail("BSATN buffer underrun: need %d byte(s) at offset %d, size %d" % [count, _pos, _buf.size()])


func read_bool() -> bool:
	_require_available(1)
	var offset := _pos
	var v := _buf.decode_u8(_pos)
	_pos += 1
	if v == 0x00:
		return false
	if v == 0x01:
		return true
	_fail("Invalid BSATN bool value %d at offset %d" % [v, offset])
	return false


func read_u8() -> int:
	_require_available(1)
	var v := _buf.decode_u8(_pos)
	_pos += 1
	return v


func read_i8() -> int:
	_require_available(1)
	var v := _buf.decode_s8(_pos)
	_pos += 1
	return v


func read_u16() -> int:
	_require_available(2)
	var v := _buf.decode_u16(_pos)
	_pos += 2
	return v


func read_i16() -> int:
	_require_available(2)
	var v := _buf.decode_s16(_pos)
	_pos += 2
	return v


func read_u32() -> int:
	_require_available(4)
	var v := _buf.decode_u32(_pos)
	_pos += 4
	return v


func read_i32() -> int:
	_require_available(4)
	var v := _buf.decode_s32(_pos)
	_pos += 4
	return v


func read_u64() -> int:
	_require_available(8)
	var v := _buf.decode_u64(_pos)
	_pos += 8
	return v


func read_i64() -> int:
	_require_available(8)
	var v := _buf.decode_s64(_pos)
	_pos += 8
	return v


func read_f32() -> float:
	_require_available(4)
	var v := _buf.decode_float(_pos)
	_pos += 4
	return v


func read_f64() -> float:
	_require_available(8)
	var v := _buf.decode_double(_pos)
	_pos += 8
	return v


func read_string() -> String:
	var n := read_u32()
	_require_available(n)
	var s := _buf.slice(_pos, _pos + n).get_string_from_utf8()
	_pos += n
	return s


func read_bytes() -> PackedByteArray:
	var n := read_u32()
	_require_available(n)
	var b := _buf.slice(_pos, _pos + n)
	_pos += n
	return b


func read_fixed_bytes(count: int) -> PackedByteArray:
	_require_available(count)
	var b := _buf.slice(_pos, _pos + count)
	_pos += count
	return b


func read_option_tag() -> bool:
	_require_available(1)
	var offset := _pos
	var tag := _buf.decode_u8(_pos)
	_pos += 1
	if tag == 0x00:
		return false
	if tag == 0x01:
		return true
	_fail("Invalid BSATN option tag %d at offset %d" % [tag, offset])
	return false


func read_array_len() -> int:
	return read_u32()


func has_more() -> bool:
	return _pos < _buf.size()


func remaining_bytes() -> int:
	return _buf.size() - _pos


func peek_u32(relative_offset: int = 0) -> int:
	_require_available(relative_offset + 4)
	return _buf.decode_u32(_pos + relative_offset)


static func decompress_gzip(data: PackedByteArray) -> PackedByteArray:
	return data.decompress_dynamic(-1, FileAccess.COMPRESSION_GZIP)


# ─── Godot-native type helpers ────────────────────────────────────────────────


func read_vector2() -> Vector2:
	return Vector2(read_f32(), read_f32())


func read_vector3() -> Vector3:
	return Vector3(read_f32(), read_f32(), read_f32())


func read_vector4() -> Vector4:
	return Vector4(read_f32(), read_f32(), read_f32(), read_f32())


func read_quaternion() -> Quaternion:
	return Quaternion(read_f32(), read_f32(), read_f32(), read_f32())


func read_color() -> Color:
	return Color(read_f32(), read_f32(), read_f32(), read_f32())


func read_vector2i() -> Vector2i:
	return Vector2i(read_i32(), read_i32())


func read_vector3i() -> Vector3i:
	return Vector3i(read_i32(), read_i32(), read_i32())


func read_vector4i() -> Vector4i:
	return Vector4i(read_i32(), read_i32(), read_i32(), read_i32())

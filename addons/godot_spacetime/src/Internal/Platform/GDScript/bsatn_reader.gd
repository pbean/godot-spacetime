class_name BsatnReader

var _buf: PackedByteArray
var _pos: int = 0


func _init(data: PackedByteArray) -> void:
	_buf = data


func _fail(message: String) -> void:
	push_error(message)
	assert(false, message)
	# assert() is debug-only; len(int) raises a runtime error in release exports too.
	var invalid_length := 0
	len(invalid_length)


func _require_available(count: int) -> void:
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


func read_vector2i() -> Vector2I:
	return Vector2I(read_i32(), read_i32())


func read_vector3i() -> Vector3I:
	return Vector3I(read_i32(), read_i32(), read_i32())


func read_vector4i() -> Vector4I:
	return Vector4I(read_i32(), read_i32(), read_i32(), read_i32())

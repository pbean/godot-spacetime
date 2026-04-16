class_name BsatnWriter

var _buf: PackedByteArray = PackedByteArray()
var _pos: int = 0


func write_bool(v: bool) -> void:
	_buf.resize(_pos + 1)
	_buf.encode_u8(_pos, 1 if v else 0)
	_pos += 1


func write_u8(v: int) -> void:
	_buf.resize(_pos + 1)
	_buf.encode_u8(_pos, v & 0xFF)
	_pos += 1


func write_i8(v: int) -> void:
	_buf.resize(_pos + 1)
	_buf.encode_s8(_pos, v)
	_pos += 1


func write_u16(v: int) -> void:
	_buf.resize(_pos + 2)
	_buf.encode_u16(_pos, v)
	_pos += 2


func write_i16(v: int) -> void:
	_buf.resize(_pos + 2)
	_buf.encode_s16(_pos, v)
	_pos += 2


func write_u32(v: int) -> void:
	_buf.resize(_pos + 4)
	_buf.encode_u32(_pos, v)
	_pos += 4


func write_i32(v: int) -> void:
	_buf.resize(_pos + 4)
	_buf.encode_s32(_pos, v)
	_pos += 4


func write_u64(v: int) -> void:
	_buf.resize(_pos + 8)
	_buf.encode_u64(_pos, v)
	_pos += 8


func write_i64(v: int) -> void:
	_buf.resize(_pos + 8)
	_buf.encode_s64(_pos, v)
	_pos += 8


func write_f32(v: float) -> void:
	_buf.resize(_pos + 4)
	_buf.encode_float(_pos, v)
	_pos += 4


func write_f64(v: float) -> void:
	_buf.resize(_pos + 8)
	_buf.encode_double(_pos, v)
	_pos += 8


func write_string(v: String) -> void:
	var utf8 := v.to_utf8_buffer()
	write_u32(utf8.size())
	_buf.resize(_pos + utf8.size())
	for i in utf8.size():
		_buf[_pos + i] = utf8[i]
	_pos += utf8.size()


func write_bytes(v: PackedByteArray) -> void:
	write_u32(v.size())
	_buf.resize(_pos + v.size())
	for i in v.size():
		_buf[_pos + i] = v[i]
	_pos += v.size()


func write_option_some() -> void:
	write_u8(0x01)


func write_option_none() -> void:
	write_u8(0x00)


func write_array_len(count: int) -> void:
	write_u32(count)


func get_bytes() -> PackedByteArray:
	return _buf.slice(0, _pos)


# ─── Godot-native type helpers ────────────────────────────────────────────────


func write_vector2(v: Vector2) -> void:
	write_f32(v.x)
	write_f32(v.y)


func write_vector3(v: Vector3) -> void:
	write_f32(v.x)
	write_f32(v.y)
	write_f32(v.z)


func write_vector4(v: Vector4) -> void:
	write_f32(v.x)
	write_f32(v.y)
	write_f32(v.z)
	write_f32(v.w)


func write_quaternion(v: Quaternion) -> void:
	write_f32(v.x)
	write_f32(v.y)
	write_f32(v.z)
	write_f32(v.w)


func write_color(v: Color) -> void:
	write_f32(v.r)
	write_f32(v.g)
	write_f32(v.b)
	write_f32(v.a)


func write_vector2i(v: Vector2I) -> void:
	write_i32(v.x)
	write_i32(v.y)


func write_vector3i(v: Vector3I) -> void:
	write_i32(v.x)
	write_i32(v.y)
	write_i32(v.z)


func write_vector4i(v: Vector4I) -> void:
	write_i32(v.x)
	write_i32(v.y)
	write_i32(v.z)
	write_i32(v.w)

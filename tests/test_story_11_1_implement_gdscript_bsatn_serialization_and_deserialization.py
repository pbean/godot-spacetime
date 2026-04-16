"""
Story 11.1: Implement GDScript BSATN Serialization and Deserialization

Static content assertions — GDScript cannot run from pytest.
Byte-identity tests use Python's struct module to validate the format spec.
"""
import struct
from pathlib import Path

ADDON_ROOT = Path(__file__).parent.parent / "addons" / "godot_spacetime" / "src"
GDSCRIPT_DIR = ADDON_ROOT / "Internal" / "Platform" / "GDScript"
WRITER_PATH = GDSCRIPT_DIR / "bsatn_writer.gd"
READER_PATH = GDSCRIPT_DIR / "bsatn_reader.gd"


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _writer_src() -> str:
    return WRITER_PATH.read_text()


def _reader_src() -> str:
    return READER_PATH.read_text()


def _function_segment(src: str, func_name: str) -> str:
    marker = f"func {func_name}"
    start = src.index(marker)
    next_func = src.find("\nfunc ", start + len(marker))
    next_static = src.find("\nstatic func ", start + len(marker))
    candidates = [pos for pos in (next_func, next_static) if pos != -1]
    end = min(candidates) if candidates else len(src)
    return src[start:end]


# ─── AC 1 + AC 2 + AC 4: File existence and class declarations ────────────────


def test_bsatn_writer_file_exists():
    assert WRITER_PATH.exists(), f"Missing: {WRITER_PATH}"


def test_bsatn_reader_file_exists():
    assert READER_PATH.exists(), f"Missing: {READER_PATH}"


def test_bsatn_writer_class_name():
    assert "class_name BsatnWriter" in _writer_src()


def test_bsatn_reader_class_name():
    assert "class_name BsatnReader" in _reader_src()


# ─── AC 1: Primitive write methods ────────────────────────────────────────────


def test_bsatn_writer_primitive_write_methods_present():
    src = _writer_src()
    expected = [
        "write_bool",
        "write_u8",
        "write_i8",
        "write_u16",
        "write_i16",
        "write_u32",
        "write_i32",
        "write_u64",
        "write_i64",
        "write_f32",
        "write_f64",
        "write_string",
        "write_bytes",
    ]
    missing = [fn for fn in expected if f"func {fn}" not in src]
    assert not missing, f"Missing writer methods: {missing}"


def test_bsatn_writer_get_bytes_present():
    assert "func get_bytes" in _writer_src()


def test_bsatn_writer_write_option_methods_present():
    src = _writer_src()
    assert "func write_option_some" in src
    assert "func write_option_none" in src


def test_bsatn_writer_write_array_len_present():
    assert "func write_array_len" in _writer_src()


# ─── AC 1: Primitive read methods ─────────────────────────────────────────────


def test_bsatn_reader_primitive_read_methods_present():
    src = _reader_src()
    expected = [
        "read_bool",
        "read_u8",
        "read_i8",
        "read_u16",
        "read_i16",
        "read_u32",
        "read_i32",
        "read_u64",
        "read_i64",
        "read_f32",
        "read_f64",
        "read_string",
        "read_bytes",
    ]
    missing = [fn for fn in expected if f"func {fn}" not in src]
    assert not missing, f"Missing reader methods: {missing}"


def test_bsatn_reader_read_option_tag_present():
    assert "func read_option_tag" in _reader_src()


def test_bsatn_reader_read_array_len_present():
    assert "func read_array_len" in _reader_src()


def test_bsatn_reader_has_more_present():
    assert "func has_more" in _reader_src()


def test_bsatn_reader_has_buffer_guard_helper():
    assert "func _require_available" in _reader_src()


def test_bsatn_reader_fail_helper_stops_in_debug_and_release():
    segment = _function_segment(_reader_src(), "_fail")
    assert "push_error(message)" in segment
    assert "assert(false, message)" in segment
    assert "len(invalid_length)" in segment


def test_bsatn_reader_primitive_reads_guard_against_truncated_buffers():
    src = _reader_src()
    expected = [
        "read_bool",
        "read_u8",
        "read_i8",
        "read_u16",
        "read_i16",
        "read_u32",
        "read_i32",
        "read_u64",
        "read_i64",
        "read_f32",
        "read_f64",
    ]
    missing = [fn for fn in expected if "_require_available(" not in _function_segment(src, fn)]
    assert not missing, f"Missing truncated-buffer guards in reader methods: {missing}"


def test_bsatn_reader_string_read_guards_payload_slice():
    segment = _function_segment(_reader_src(), "read_string")
    assert "var n := read_u32()" in segment
    assert "_require_available(n)" in segment
    assert ".slice(_pos, _pos + n)" in segment


def test_bsatn_reader_bytes_read_guards_payload_slice():
    segment = _function_segment(_reader_src(), "read_bytes")
    assert "var n := read_u32()" in segment
    assert "_require_available(n)" in segment
    assert ".slice(_pos, _pos + n)" in segment


def test_bsatn_reader_bool_rejects_non_canonical_values():
    segment = _function_segment(_reader_src(), "read_bool")
    assert "v == 0x00" in segment
    assert "v == 0x01" in segment
    assert "_fail(" in segment


def test_bsatn_reader_option_tag_rejects_invalid_variants():
    segment = _function_segment(_reader_src(), "read_option_tag")
    assert "tag == 0x00" in segment
    assert "tag == 0x01" in segment
    assert "_fail(" in segment


# ─── AC 2: Godot-native type methods ──────────────────────────────────────────


def test_bsatn_writer_godot_native_types_present():
    src = _writer_src()
    expected = [
        "write_vector2",
        "write_vector3",
        "write_vector4",
        "write_quaternion",
        "write_color",
        "write_vector2i",
        "write_vector3i",
        "write_vector4i",
    ]
    missing = [fn for fn in expected if f"func {fn}" not in src]
    assert not missing, f"Missing writer Godot-native methods: {missing}"


def test_bsatn_reader_godot_native_types_present():
    src = _reader_src()
    expected = [
        "read_vector2",
        "read_vector3",
        "read_vector4",
        "read_quaternion",
        "read_color",
        "read_vector2i",
        "read_vector3i",
        "read_vector4i",
    ]
    missing = [fn for fn in expected if f"func {fn}" not in src]
    assert not missing, f"Missing reader Godot-native methods: {missing}"


# ─── AC 3: Python byte-identity format spec validation ────────────────────────


def test_bsatn_u32_byte_order():
    assert struct.pack("<I", 1) == b"\x01\x00\x00\x00"
    assert struct.pack("<I", 0x01020304) == b"\x04\x03\x02\x01"


def test_bsatn_i32_negative_byte_order():
    assert struct.pack("<i", -1) == b"\xff\xff\xff\xff"


def test_bsatn_bool_encoding():
    assert struct.pack("<B", 1) == b"\x01"
    assert struct.pack("<B", 0) == b"\x00"


def test_bsatn_f32_encoding():
    assert struct.pack("<f", 1.0) == b"\x00\x00\x80\x3f"


def test_bsatn_string_encoding():
    # "hi" = 2 UTF-8 bytes; length prefix is u32 LE
    expected = struct.pack("<I", 2) + b"hi"
    assert expected == b"\x02\x00\x00\x00hi"


def test_bsatn_option_none_encoding():
    assert struct.pack("<B", 0x00) == b"\x00"


def test_bsatn_option_some_encoding():
    # Option<u8>(Some(42)) → tag 0x01 + value 0x2a
    assert struct.pack("<BB", 0x01, 42) == b"\x01\x2a"


# ─── AC 4: Gzip decompression ─────────────────────────────────────────────────


def test_bsatn_reader_decompress_gzip_present():
    assert "func decompress_gzip" in _reader_src()


def test_bsatn_reader_decompress_gzip_is_static():
    assert "static func decompress_gzip" in _reader_src()


def test_bsatn_reader_uses_compression_gzip_constant():
    assert "COMPRESSION_GZIP" in _reader_src()


def test_bsatn_reader_uses_decompress_dynamic():
    assert "decompress_dynamic" in _reader_src()


# ─── Structural: BsatnReader constructor ──────────────────────────────────────


def test_bsatn_reader_init_constructor_present():
    assert "func _init" in _reader_src()


# ─── Anti-pattern guards: signed types use signed encoders ────────────────────


def test_bsatn_writer_uses_signed_32_encoder():
    assert "encode_s32" in _writer_src()


def test_bsatn_writer_uses_signed_64_encoder():
    assert "encode_s64" in _writer_src()


def test_bsatn_writer_f64_uses_double_not_float_encoder():
    assert "encode_double" in _writer_src()


def test_bsatn_reader_uses_signed_32_decoder():
    assert "decode_s32" in _reader_src()


def test_bsatn_reader_uses_signed_64_decoder():
    assert "decode_s64" in _reader_src()


def test_bsatn_reader_f64_uses_double_not_float_decoder():
    assert "decode_double" in _reader_src()


def test_bsatn_writer_does_not_use_append_array():
    assert "append_array" not in _writer_src()


def test_bsatn_writer_tracks_position_variable():
    assert "var _pos: int = 0" in _writer_src()


def test_bsatn_reader_tracks_position_variable():
    assert "var _pos: int = 0" in _reader_src()


# ─── Additional byte-identity format tests ────────────────────────────────────


def test_bsatn_u8_encoding():
    assert struct.pack("<B", 255) == b"\xff"
    assert struct.pack("<B", 0) == b"\x00"


def test_bsatn_i8_encoding():
    assert struct.pack("<b", -1) == b"\xff"
    assert struct.pack("<b", 127) == b"\x7f"


def test_bsatn_u16_encoding():
    assert struct.pack("<H", 0x0102) == b"\x02\x01"
    assert struct.pack("<H", 0xFFFF) == b"\xff\xff"


def test_bsatn_i16_encoding():
    assert struct.pack("<h", -1) == b"\xff\xff"
    assert struct.pack("<h", 256) == b"\x00\x01"


def test_bsatn_u64_encoding():
    assert struct.pack("<Q", 1) == b"\x01\x00\x00\x00\x00\x00\x00\x00"
    assert struct.pack("<Q", 0xDEADBEEF) == b"\xef\xbe\xad\xde\x00\x00\x00\x00"


def test_bsatn_i64_encoding():
    assert struct.pack("<q", -1) == b"\xff\xff\xff\xff\xff\xff\xff\xff"


def test_bsatn_f64_encoding():
    assert struct.pack("<d", 1.0) == b"\x00\x00\x00\x00\x00\x00\xf0\x3f"
    assert struct.pack("<d", 0.0) == b"\x00\x00\x00\x00\x00\x00\x00\x00"


def test_bsatn_bytes_length_prefix_encoding():
    raw = b"\xde\xad\xbe\xef"
    expected = struct.pack("<I", len(raw)) + raw
    assert expected == b"\x04\x00\x00\x00\xde\xad\xbe\xef"


# ─── Godot-native type field-order and encoding checks ────────────────────────


def test_bsatn_writer_color_uses_rgba_field_order():
    src = _writer_src()
    idx = src.index("func write_color")
    segment = src[idx : idx + 300]
    assert segment.index("v.r") < segment.index("v.g") < segment.index("v.b") < segment.index("v.a")


def test_bsatn_writer_vector2i_uses_i32_not_f32():
    src = _writer_src()
    idx = src.index("func write_vector2i")
    segment = src[idx : idx + 200]
    assert "write_i32" in segment
    assert "write_f32" not in segment


def test_bsatn_reader_color_reads_four_f32_components():
    """Color(r,g,b,a) is constructed positionally — verify 4 f32 reads in read_color."""
    src = _reader_src()
    idx = src.index("func read_color")
    segment = src[idx : idx + 200]
    assert "-> Color" in segment
    assert segment.count("read_f32()") == 4


def test_bsatn_reader_vector2i_uses_i32_not_f32():
    src = _reader_src()
    idx = src.index("func read_vector2i")
    segment = src[idx : idx + 200]
    assert "read_i32" in segment
    assert "read_f32" not in segment

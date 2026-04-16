extends RefCounted

const BsatnReaderScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/bsatn_reader.gd")

var _rows: Array = []

var count: int:
	get:
		return _rows.size()


func sql_table_name() -> String:
	return "smoke_test"


func cache_table_name() -> String:
	return "SmokeTest"


func decode_row(row_bytes: PackedByteArray) -> Dictionary:
	var reader = BsatnReaderScript.new(row_bytes)
	return {
		"id": reader.read_u32(),
		"value": reader.read_string(),
	}


func get_primary_key(row: Dictionary) -> Variant:
	return row.get("id")


func iter() -> Array:
	return _rows.duplicate(true)


func replace_rows(rows: Array) -> void:
	_rows = rows.duplicate(true)

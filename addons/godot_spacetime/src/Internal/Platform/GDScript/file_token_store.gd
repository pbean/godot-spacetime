extends "res://addons/godot_spacetime/src/Internal/Platform/GDScript/token_store.gd"
class_name GdscriptFileTokenStore

const DEFAULT_TOKEN_PATH := "user://spacetime/auth/token"

var _token_path: String = DEFAULT_TOKEN_PATH


func _init(token_path: String = DEFAULT_TOKEN_PATH) -> void:
	_token_path = token_path.strip_edges()
	if _token_path.is_empty():
		_token_path = DEFAULT_TOKEN_PATH


func get_token() -> String:
	last_error_message = ""
	if not FileAccess.file_exists(_token_path):
		return ""

	var file := FileAccess.open(_token_path, FileAccess.READ)
	if file == null:
		last_error_message = "failed to open token store for reading"
		return ""

	return file.get_as_text().strip_edges()


func store_token(token: String) -> int:
	last_error_message = ""
	var mkdir_result := _ensure_parent_dir()
	if mkdir_result != OK:
		return mkdir_result

	var file := FileAccess.open(_token_path, FileAccess.WRITE)
	if file == null:
		last_error_message = "failed to open token store for writing"
		return FileAccess.get_open_error()

	file.store_string(token)
	return OK


func clear_token() -> int:
	last_error_message = ""
	if not FileAccess.file_exists(_token_path):
		return OK
	var absolute_path := ProjectSettings.globalize_path(_token_path)
	return DirAccess.remove_absolute(absolute_path)


func get_token_path() -> String:
	return _token_path


func _ensure_parent_dir() -> int:
	var token_dir := _token_path.get_base_dir()
	if token_dir.is_empty():
		return OK

	var absolute_dir := ProjectSettings.globalize_path(token_dir)
	return DirAccess.make_dir_recursive_absolute(absolute_dir)

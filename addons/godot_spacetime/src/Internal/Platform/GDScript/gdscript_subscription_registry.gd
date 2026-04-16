class_name GdscriptSubscriptionRegistry
extends RefCounted

var _entries: Dictionary = {}


func register(handle: Object) -> void:
	_entries[int(handle.handle_id)] = {
		"handle": handle,
	}


func unregister(handle_id: int) -> Dictionary:
	if not _entries.has(handle_id):
		return {}

	var entry: Dictionary = _entries[handle_id]
	_entries.erase(handle_id)
	return entry


func try_get_entry(handle_id: int) -> Dictionary:
	if not _entries.has(handle_id):
		return {}
	return (_entries[handle_id] as Dictionary).duplicate(true)


func try_get_handle(handle_id: int) -> Object:
	if not _entries.has(handle_id):
		return null
	return _entries[handle_id]["handle"]


func find_by_query_set_id(query_set_id: int) -> Object:
	for entry in _entries.values():
		var handle = entry.get("handle")
		if handle != null and int(handle.query_set_id) == query_set_id:
			return handle
	return null


func clear() -> void:
	for entry in _entries.values():
		var handle = entry.get("handle")
		if handle != null:
			handle.close()
	_entries.clear()

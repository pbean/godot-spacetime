class_name GdscriptRowChangedEvent
extends RefCounted

var table_name: String = ""
var change_type: String = ""
var old_row = null
var new_row = null


func _init(table_name_value: String, change_type_value: String, old_row_value = null, new_row_value = null) -> void:
	table_name = table_name_value
	change_type = change_type_value
	old_row = old_row_value
	new_row = new_row_value


func to_dictionary() -> Dictionary:
	return {
		"table_name": table_name,
		"change_type": change_type,
		"old_row": old_row,
		"new_row": new_row,
	}

class_name GdscriptTokenStore

var last_error_message: String = ""


func get_token() -> String:
	last_error_message = ""
	return ""


func store_token(_token: String) -> int:
	last_error_message = ""
	return OK


func clear_token() -> int:
	last_error_message = ""
	return OK

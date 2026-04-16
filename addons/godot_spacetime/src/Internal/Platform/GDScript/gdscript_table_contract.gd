class_name GdscriptTableContract
extends RefCounted

const REQUIRED_METHODS := [
	"sql_table_name",
	"cache_table_name",
	"decode_row",
	"get_primary_key",
	"iter",
	"replace_rows",
]


static func validate(contract: Variant) -> String:
	if contract == null:
		return "configure_bindings() requires non-null table contract objects."

	for method_name in REQUIRED_METHODS:
		if not contract.has_method(method_name):
			return "configure_bindings() requires each table contract to implement %s()." % method_name

	return ""


static func cache_name_from_sql(sql_table_name: String) -> String:
	var pieces := sql_table_name.strip_edges().split("_", false)
	var result := ""
	for piece in pieces:
		if piece.is_empty():
			continue
		result += piece.substr(0, 1).to_upper() + piece.substr(1)
	return result

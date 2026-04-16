class_name GdscriptSubscriptionHandle
extends RefCounted

const STATUS_ACTIVE := "Active"
const STATUS_SUPERSEDED := "Superseded"
const STATUS_CLOSED := "Closed"

var handle_id: int = -1
var query_set_id: int = -1
var status: String = STATUS_ACTIVE
var query_sqls: Array = []


func _init(handle_id_value: int, query_set_id_value: int, query_sqls_value: Array = []) -> void:
	handle_id = handle_id_value
	query_set_id = query_set_id_value
	query_sqls = query_sqls_value.duplicate(true)
	status = STATUS_ACTIVE


func supersede() -> void:
	if status == STATUS_CLOSED:
		return
	status = STATUS_SUPERSEDED


func close() -> void:
	status = STATUS_CLOSED

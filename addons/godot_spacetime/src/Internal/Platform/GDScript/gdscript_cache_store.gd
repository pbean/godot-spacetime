class_name GdscriptCacheStore
extends RefCounted

const TableContractScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_table_contract.gd")
const RowChangedEventScript = preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_row_changed_event.gd")

var _bindings = null
var _contracts_by_sql: Dictionary = {}
var _contracts_by_cache_name: Dictionary = {}


func configure_bindings(binding_metadata: Variant) -> int:
	var contracts: Array = []
	if binding_metadata is Array:
		contracts = binding_metadata.duplicate(true)
	elif binding_metadata != null and binding_metadata.has_method("get_table_contracts"):
		contracts = binding_metadata.get_table_contracts()
	else:
		push_error("configure_bindings() requires a bindings object with get_table_contracts() or an Array of contracts.")
		return ERR_INVALID_PARAMETER

	if contracts.is_empty():
		push_error("configure_bindings() requires at least one table contract.")
		return ERR_INVALID_PARAMETER

	var contracts_by_sql: Dictionary = {}
	var contracts_by_cache_name: Dictionary = {}
	for contract in contracts:
		var validation_error := TableContractScript.validate(contract)
		if not validation_error.is_empty():
			push_error(validation_error)
			return ERR_INVALID_PARAMETER

		var sql_name := String(contract.sql_table_name()).strip_edges()
		var cache_name := String(contract.cache_table_name()).strip_edges()
		if sql_name.is_empty() or cache_name.is_empty():
			push_error("configure_bindings() requires non-empty sql_table_name() and cache_table_name() values.")
			return ERR_INVALID_PARAMETER

		if contracts_by_sql.has(sql_name):
			push_error("configure_bindings() duplicate sql_table_name '%s': each table must be registered once." % sql_name)
			return ERR_INVALID_PARAMETER
		if contracts_by_cache_name.has(cache_name):
			push_error("configure_bindings() duplicate cache_table_name '%s': each table must be registered once." % cache_name)
			return ERR_INVALID_PARAMETER

		contracts_by_sql[sql_name] = contract
		contracts_by_cache_name[cache_name] = contract

	_bindings = binding_metadata
	_contracts_by_sql = contracts_by_sql
	_contracts_by_cache_name = contracts_by_cache_name
	clear()
	return OK


func has_bindings() -> bool:
	return _bindings != null and not _contracts_by_sql.is_empty()


func get_remote_tables():
	return _bindings


func get_rows(cache_table_name: String) -> Array:
	if not _contracts_by_cache_name.has(cache_table_name):
		return []
	return _contracts_by_cache_name[cache_table_name].iter()


func clear() -> void:
	for contract in _contracts_by_cache_name.values():
		contract.replace_rows([])


func build_snapshot(query_rows: Array) -> Dictionary:
	var snapshot: Dictionary = {}
	for cache_name in _contracts_by_cache_name.keys():
		snapshot[cache_name] = []

	for table_entry_variant in query_rows:
		var table_entry: Dictionary = table_entry_variant
		var sql_name := String(table_entry.get("table_name", ""))
		if not _contracts_by_sql.has(sql_name):
			continue

		var contract = _contracts_by_sql[sql_name]
		snapshot[String(contract.cache_table_name())] = _decode_rows(
			contract,
			table_entry.get("row_payloads", [])
		)

	return snapshot


func commit_snapshot(snapshot: Dictionary) -> Array:
	var row_events: Array = []
	for cache_name in _contracts_by_cache_name.keys():
		var contract = _contracts_by_cache_name[cache_name]
		var old_rows: Array = contract.iter()
		var new_rows: Array = snapshot.get(cache_name, [])
		row_events.append_array(_diff_rows(contract, old_rows, new_rows))
		contract.replace_rows(new_rows)
	return row_events


func apply_transaction_updates(query_set_updates: Array) -> Array:
	var row_events: Array = []
	for query_set_update_variant in query_set_updates:
		var query_set_update: Dictionary = query_set_update_variant
		for table_update_variant in query_set_update.get("tables", []):
			var table_update: Dictionary = table_update_variant
			var sql_name := String(table_update.get("table_name", ""))
			if not _contracts_by_sql.has(sql_name):
				continue

			var contract = _contracts_by_sql[sql_name]
			var state := _rows_to_state(contract, contract.iter())
			for rows_variant in table_update.get("updates", []):
				var update_entry: Dictionary = rows_variant
				match String(update_entry.get("variant", "")):
					"PersistentTable":
						row_events.append_array(
							_apply_persistent_rows(
								contract,
								state,
								update_entry.get("insert_row_payloads", []),
								update_entry.get("delete_row_payloads", [])
							)
						)
					"EventTable":
						row_events.append_array(
							_apply_event_rows(contract, update_entry.get("event_row_payloads", []))
						)

			contract.replace_rows(_state_to_rows(state))

	return row_events


func _decode_rows(contract, row_payloads: Array) -> Array:
	var rows: Array = []
	for payload_variant in row_payloads:
		rows.append(contract.decode_row(payload_variant))
	return rows


func _rows_to_state(contract, rows: Array) -> Dictionary:
	var by_key: Dictionary = {}
	var order: Array = []
	for row in rows:
		var key = contract.get_primary_key(row)
		if not by_key.has(key):
			order.append(key)
		by_key[key] = row
	return {
		"by_key": by_key,
		"order": order,
	}


func _state_to_rows(state: Dictionary) -> Array:
	var rows: Array = []
	var by_key: Dictionary = state.get("by_key", {})
	for key in state.get("order", []):
		if by_key.has(key):
			rows.append(by_key[key])
	return rows


func _diff_rows(contract, old_rows: Array, new_rows: Array) -> Array:
	var old_state := _rows_to_state(contract, old_rows)
	var new_state := _rows_to_state(contract, new_rows)
	var old_by_key: Dictionary = old_state.get("by_key", {})
	var new_by_key: Dictionary = new_state.get("by_key", {})
	var row_events: Array = []
	var table_name := String(contract.cache_table_name())

	for key in old_state.get("order", []):
		if not new_by_key.has(key):
			row_events.append(RowChangedEventScript.new(
				table_name,
				"Delete",
				old_by_key[key],
				null
			).to_dictionary())
		elif old_by_key[key] != new_by_key[key]:
			row_events.append(RowChangedEventScript.new(
				table_name,
				"Update",
				old_by_key[key],
				new_by_key[key]
			).to_dictionary())

	for key in new_state.get("order", []):
		if not old_by_key.has(key):
			row_events.append(RowChangedEventScript.new(
				table_name,
				"Insert",
				null,
				new_by_key[key]
			).to_dictionary())

	return row_events


func _apply_persistent_rows(contract, state: Dictionary, insert_row_payloads: Array, delete_row_payloads: Array) -> Array:
	var inserts := _decode_rows(contract, insert_row_payloads)
	var deletes := _decode_rows(contract, delete_row_payloads)
	var by_key: Dictionary = state.get("by_key", {})
	var order: Array = state.get("order", [])
	var table_name := String(contract.cache_table_name())
	var row_events: Array = []
	var inserts_by_key: Dictionary = {}

	for inserted_row in inserts:
		inserts_by_key[contract.get_primary_key(inserted_row)] = inserted_row

	for deleted_row in deletes:
		var key = contract.get_primary_key(deleted_row)
		if inserts_by_key.has(key):
			var new_row = inserts_by_key[key]
			var old_row = by_key.get(key, deleted_row)
			if not by_key.has(key):
				order.append(key)
			by_key[key] = new_row
			row_events.append(RowChangedEventScript.new(
				table_name,
				"Update",
				old_row,
				new_row
			).to_dictionary())
			inserts_by_key.erase(key)
			continue

		var old_deleted_row = by_key.get(key, deleted_row)
		if by_key.has(key):
			by_key.erase(key)
			order.erase(key)
		row_events.append(RowChangedEventScript.new(
			table_name,
			"Delete",
			old_deleted_row,
			null
		).to_dictionary())

	for key in inserts_by_key.keys():
		var inserted_row = inserts_by_key[key]
		if by_key.has(key):
			var old_row = by_key[key]
			by_key[key] = inserted_row
			row_events.append(RowChangedEventScript.new(
				table_name,
				"Update",
				old_row,
				inserted_row
			).to_dictionary())
		else:
			by_key[key] = inserted_row
			order.append(key)
			row_events.append(RowChangedEventScript.new(
				table_name,
				"Insert",
				null,
				inserted_row
			).to_dictionary())

	return row_events


func _apply_event_rows(contract, event_row_payloads: Array) -> Array:
	var row_events: Array = []
	var table_name := String(contract.cache_table_name())
	for event_row in _decode_rows(contract, event_row_payloads):
		row_events.append(RowChangedEventScript.new(
			table_name,
			"Insert",
			null,
			event_row
		).to_dictionary())
	return row_events

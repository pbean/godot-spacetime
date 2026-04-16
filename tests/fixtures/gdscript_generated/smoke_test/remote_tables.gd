extends RefCounted

const SmokeTestTableScript = preload("res://tests/fixtures/gdscript_generated/smoke_test/smoke_test_table.gd")
const TypedEntityTableScript = preload("res://tests/fixtures/gdscript_generated/smoke_test/typed_entity_table.gd")

var SmokeTest = SmokeTestTableScript.new()
var TypedEntity = TypedEntityTableScript.new()


func get_table_contracts() -> Array:
	return [SmokeTest, TypedEntity]

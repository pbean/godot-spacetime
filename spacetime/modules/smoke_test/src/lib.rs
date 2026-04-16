use spacetimedb::{table, reducer, ReducerContext, SpacetimeType, Table};

#[table(name = smoke_test, public)]
pub struct SmokeTest {
    #[primary_key]
    #[auto_inc]
    pub id: u32,
    #[index(btree)]
    pub value: String,
}

// Fixture types for Godot-native type mapping (Story 7.1).
// These are bare SpacetimeDB types used as column types — no #[table] on them.

// Layout matches Vector2 (two f32 fields: x, y)
#[derive(SpacetimeType)]
pub struct Vec2F { pub x: f32, pub y: f32 }

// Layout matches Vector3I (three i32 fields: x, y, z)
#[derive(SpacetimeType)]
pub struct Vec3I { pub x: i32, pub y: i32, pub z: i32 }

// Layout matches Quaternion (four f32 fields: x, y, z, w AND name contains "quat")
#[derive(SpacetimeType)]
pub struct EntityQuat { pub x: f32, pub y: f32, pub z: f32, pub w: f32 }

// Layout matches Color (four f32 fields: r, g, b, a)
#[derive(SpacetimeType)]
pub struct RgbaColor { pub r: f32, pub g: f32, pub b: f32, pub a: f32 }

// Does NOT match any Godot layout (mixed types — fallback case)
#[derive(SpacetimeType)]
pub struct NotAGodotType { pub label: String, pub value: f32 }

#[table(name = typed_entity, public)]
pub struct TypedEntity {
    #[primary_key]
    #[auto_inc]
    pub id: u32,
    pub position: Vec2F,
    pub orientation: EntityQuat,
    pub color: RgbaColor,
    pub tile: Vec3I,
}

#[reducer]
pub fn ping(_ctx: &ReducerContext) {
    // No-op smoke reducer: validates the generation and CLI invocation path.
}

#[reducer]
pub fn ping_insert(ctx: &ReducerContext, value: String) {
    // Inserts a single SmokeTest row so dynamic lifecycle tests can observe
    // a real row-level change end-to-end through the SDK cache surface.
    ctx.db.smoke_test().insert(SmokeTest { id: 0, value });
}

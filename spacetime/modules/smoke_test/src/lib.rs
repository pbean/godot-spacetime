use spacetimedb::{table, reducer, ReducerContext, Table};

#[table(name = smoke_test, public)]
pub struct SmokeTest {
    #[primary_key]
    #[auto_inc]
    pub id: u32,
    pub value: String,
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

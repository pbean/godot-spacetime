use spacetimedb::{table, reducer, ReducerContext};

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

use spacetimedb::{reducer, table, view, AnonymousViewContext, ReducerContext, SpacetimeType, Table};

#[table(name = player, public)]
pub struct Player {
    #[primary_key]
    #[auto_inc]
    pub id: u64,
    #[index(btree)]
    pub level: u64,
    pub name: String,
    pub active: bool,
}

#[derive(SpacetimeType)]
pub struct LevelTwoPlayerSummary {
    pub id: u64,
    pub name: String,
    pub level: u64,
}

#[view(name = players_for_level_two, public)]
fn players_for_level_two(ctx: &AnonymousViewContext) -> Vec<LevelTwoPlayerSummary> {
    ctx.db
        .player()
        .level()
        .filter(2_u64)
        .map(|player| LevelTwoPlayerSummary {
            id: player.id,
            name: player.name.clone(),
            level: player.level,
        })
        .collect()
}

#[view(name = player_one, public)]
fn player_one(ctx: &AnonymousViewContext) -> Option<Player> {
    ctx.db.player().id().find(1_u64)
}

#[reducer]
pub fn seed_players(ctx: &ReducerContext) {
    ctx.db.player().insert(Player {
        id: 0,
        name: "Ada".to_string(),
        level: 2,
        active: true,
    });

    ctx.db.player().insert(Player {
        id: 0,
        name: "Grace".to_string(),
        level: 3,
        active: false,
    });
}

"""
Story 10.4: Generate Bindings for Database View Definitions

Static contract coverage asserting:
- the pre-committed view_test module, script, fixture, and docs exist
- view definitions generate typed handles and query helpers next to tables
- view handles remain read-only projections without index helpers
- modules without view exports remain unchanged
- docs explain the read-only distinction
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_CARGO_REL = "spacetime/modules/view_test/Cargo.toml"
MODULE_README_REL = "spacetime/modules/view_test/README.md"
MODULE_REL = "spacetime/modules/view_test/src/lib.rs"
SCRIPT_REL = "scripts/codegen/generate-view-test.sh"
CLIENT_REL = "tests/fixtures/generated/view_test/SpacetimeDBClient.g.cs"
PLAYER_TABLE_REL = "tests/fixtures/generated/view_test/Tables/Player.g.cs"
PLAYER_ONE_REL = "tests/fixtures/generated/view_test/Tables/PlayerOne.g.cs"
PLAYERS_FOR_LEVEL_TWO_REL = "tests/fixtures/generated/view_test/Tables/PlayersForLevelTwo.g.cs"
PLAYER_TYPE_REL = "tests/fixtures/generated/view_test/Types/Player.g.cs"
SUMMARY_TYPE_REL = "tests/fixtures/generated/view_test/Types/LevelTwoPlayerSummary.g.cs"
SEED_PLAYERS_REDUCER_REL = "tests/fixtures/generated/view_test/Reducers/SeedPlayers.g.cs"
FIXTURE_README_REL = "tests/fixtures/generated/view_test/README.md"
DOCS_REL = "docs/codegen.md"
SMOKE_CLIENT_REL = "demo/generated/smoke_test/SpacetimeDBClient.g.cs"
SCHEDULED_CLIENT_REL = "tests/fixtures/generated/scheduled_test/SpacetimeDBClient.g.cs"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


# ---------------------------------------------------------------------------
# Task 0 / AC 1,2,3,4 - pre-committed infrastructure exists
# ---------------------------------------------------------------------------

def test_story_10_4_required_files_exist() -> None:
    required = [
        MODULE_CARGO_REL,
        MODULE_README_REL,
        MODULE_REL,
        SCRIPT_REL,
        FIXTURE_README_REL,
        CLIENT_REL,
        PLAYER_TABLE_REL,
        PLAYER_ONE_REL,
        PLAYERS_FOR_LEVEL_TWO_REL,
        PLAYER_TYPE_REL,
        SUMMARY_TYPE_REL,
        SEED_PLAYERS_REDUCER_REL,
        DOCS_REL,
    ]
    for rel in required:
        assert (ROOT / rel).is_file(), f"{rel} must exist for Story 10.4."


# ---------------------------------------------------------------------------
# Task 1 / AC 2 - validate the Rust fixture module shape
# ---------------------------------------------------------------------------

def test_view_module_declares_expected_table_projection_views_and_reducer() -> None:
    module = _read(MODULE_REL)
    for expected in (
        "#[table(name = player, public)]",
        "pub struct Player {",
        "pub id: u64,",
        "pub level: u64,",
        "pub name: String,",
        "pub active: bool,",
        "#[derive(SpacetimeType)]",
        "pub struct LevelTwoPlayerSummary {",
        "#[view(name = players_for_level_two, public)]",
        "fn players_for_level_two(ctx: &AnonymousViewContext) -> Vec<LevelTwoPlayerSummary>",
        "#[view(name = player_one, public)]",
        "fn player_one(ctx: &AnonymousViewContext) -> Option<Player>",
        "#[reducer]",
        "pub fn seed_players(ctx: &ReducerContext)",
    ):
        assert expected in module, (
            "Story 10.4's view_test module must declare the expected table, "
            f"projection type, views, and reducer. Missing {expected!r}."
        )


def test_view_module_pins_spacetimedb_1_12_0() -> None:
    cargo_toml = _read(MODULE_CARGO_REL)
    assert 'spacetimedb = "=1.12.0"' in cargo_toml, (
        "view_test/Cargo.toml must pin spacetimedb = \"=1.12.0\" to match the "
        "other repository-owned fixture modules."
    )


# ---------------------------------------------------------------------------
# Task 2 / AC 1,2,4 - validate the generated view binding surface
# ---------------------------------------------------------------------------

def test_view_fixture_uses_distinct_namespace() -> None:
    client = _read(CLIENT_REL)
    assert "namespace SpacetimeDB.ViewTestTypes" in client, (
        "The view_test fixture must use the distinct namespace "
        "'SpacetimeDB.ViewTestTypes'."
    )
    assert "namespace SpacetimeDB.Types" not in client, (
        "The view_test fixture must not fall back to the default namespace."
    )


def test_remote_tables_register_player_and_view_handles() -> None:
    client = _read(CLIENT_REL)
    for expected in (
        "AddTable(Player = new(conn))",
        "AddTable(PlayerOne = new(conn))",
        "AddTable(PlayersForLevelTwo = new(conn))",
    ):
        assert expected in client, (
            "RemoteTables must register the regular table and both view handles. "
            f"Missing {expected!r}."
        )


def test_query_builder_includes_all_table_and_view_helpers() -> None:
    client = _read(CLIENT_REL)
    for expected in (
        "new QueryBuilder().From.Player().ToSql(),",
        "new QueryBuilder().From.PlayerOne().ToSql(),",
        "new QueryBuilder().From.PlayersForLevelTwo().ToSql(),",
        'public global::SpacetimeDB.Table<Player, PlayerCols, PlayerIxCols> Player() => new("player"',
        'public global::SpacetimeDB.Table<Player, PlayerOneCols, PlayerOneIxCols> PlayerOne() => new("player_one"',
        'public global::SpacetimeDB.Table<LevelTwoPlayerSummary, PlayersForLevelTwoCols, PlayersForLevelTwoIxCols> PlayersForLevelTwo() => new("players_for_level_two"',
    ):
        assert expected in client, (
            "QueryBuilder must expose Player plus both views through the same "
            f"subscription/query surface. Missing {expected!r}."
        )


def test_dispatch_only_routes_seed_players() -> None:
    client = _read(CLIENT_REL)
    dispatch = _section(
        client,
        "protected override bool Dispatch(",
        "public SubscriptionBuilder SubscriptionBuilder() => new(this);",
    )
    assert "Reducer.SeedPlayers args => Reducers.InvokeSeedPlayers(eventContext, args)," in dispatch, (
        "DbConnection.Dispatch() must dispatch the regular SeedPlayers reducer."
    )
    assert dispatch.count("Reducer.") == 1, (
        "DbConnection.Dispatch() must only contain the SeedPlayers reducer case."
    )
    assert "PlayerOne" not in dispatch and "PlayersForLevelTwo" not in dispatch, (
        "Views must not produce reducer dispatch entries."
    )


def test_remote_reducers_only_expose_seed_players_surface() -> None:
    reducer = _read(SEED_PLAYERS_REDUCER_REL)
    for expected in (
        "public sealed partial class RemoteReducers : RemoteBase",
        "public event SeedPlayersHandler? OnSeedPlayers;",
        "public void SeedPlayers()",
        "public bool InvokeSeedPlayers(",
        'string IReducerArgs.ReducerName => "seed_players";',
    ):
        assert expected in reducer, (
            "RemoteReducers must expose the normal SeedPlayers reducer surface. "
            f"Missing {expected!r}."
        )
    for unexpected in ("OnPlayerOne", "OnPlayersForLevelTwo"):
        assert unexpected not in reducer, (
            "View definitions must not generate reducer-facing API surface."
        )


def test_player_one_view_reuses_player_row_type() -> None:
    handle = _read(PLAYER_ONE_REL)
    assert "RemoteTableHandle<EventContext, Player>" in handle, (
        "PlayerOneHandle must reuse the Player row type because the view returns Option<Player>."
    )
    assert 'RemoteTableName => "player_one"' in handle, (
        "PlayerOneHandle must target the generated player_one view name."
    )
    for expected in (
        "global::SpacetimeDB.Col<Player, ulong> Id",
        "global::SpacetimeDB.Col<Player, ulong> Level",
        "global::SpacetimeDB.Col<Player, string> Name",
        "global::SpacetimeDB.Col<Player, bool> Active",
    ):
        assert expected in handle, (
            "PlayerOneCols must reuse the Player schema exactly. "
            f"Missing {expected!r}."
        )
    assert not (ROOT / "tests/fixtures/generated/view_test/Types/PlayerOne.g.cs").exists(), (
        "player_one must reuse Types/Player.g.cs instead of generating a new PlayerOne row type."
    )


def test_players_for_level_two_view_uses_projection_row_type() -> None:
    handle = _read(PLAYERS_FOR_LEVEL_TWO_REL)
    assert "RemoteTableHandle<EventContext, LevelTwoPlayerSummary>" in handle, (
        "PlayersForLevelTwoHandle must use the dedicated LevelTwoPlayerSummary projection type."
    )
    assert 'RemoteTableName => "players_for_level_two"' in handle, (
        "PlayersForLevelTwoHandle must target the generated players_for_level_two view name."
    )
    for expected in (
        "global::SpacetimeDB.Col<LevelTwoPlayerSummary, ulong> Id",
        "global::SpacetimeDB.Col<LevelTwoPlayerSummary, string> Name",
        "global::SpacetimeDB.Col<LevelTwoPlayerSummary, ulong> Level",
    ):
        assert expected in handle, (
            "PlayersForLevelTwoCols must match the projection schema exported by the view. "
            f"Missing {expected!r}."
        )


def test_level_two_player_summary_matches_projection_schema() -> None:
    projection = _read(SUMMARY_TYPE_REL)
    for expected in (
        "[SpacetimeDB.Type]",
        '[DataMember(Name = "id")]',
        '[DataMember(Name = "name")]',
        '[DataMember(Name = "level")]',
        "public ulong Id;",
        "public string Name;",
        "public ulong Level;",
    ):
        assert expected in projection, (
            "LevelTwoPlayerSummary.g.cs must contain the three-field projection schema. "
            f"Missing {expected!r}."
        )
    assert '[DataMember(Name = "active")]' not in projection and "public bool Active;" not in projection, (
        "LevelTwoPlayerSummary must remain distinct from Player and must not carry the active field."
    )


# ---------------------------------------------------------------------------
# Task 3 / AC 4 - distinguish views from regular tables
# ---------------------------------------------------------------------------

def test_player_table_handle_keeps_primary_key_and_btree_indexes() -> None:
    player_handle = _read(PLAYER_TABLE_REL)
    for expected in (
        "public sealed class PlayerHandle : RemoteTableHandle<EventContext, Player>",
        "public sealed class IdUniqueIndex : UniqueIndexBase<ulong>",
        "public sealed class LevelIndex : BTreeIndexBase<ulong>",
        "protected override object GetPrimaryKey(Player row) => row.Id;",
    ):
        assert expected in player_handle, (
            "The regular Player table handle must keep its primary-key and BTree index helpers. "
            f"Missing {expected!r}."
        )


def test_view_handles_do_not_generate_index_helpers_or_primary_keys() -> None:
    for rel in (PLAYER_ONE_REL, PLAYERS_FOR_LEVEL_TWO_REL):
        handle = _read(rel)
        for forbidden in ("UniqueIndexBase", "BTreeIndexBase", "GetPrimaryKey("):
            assert forbidden not in handle, (
                f"{rel} must remain an index-free read-only projection, not a full table handle."
            )


def test_player_one_handle_keeps_cols_but_has_empty_index_set() -> None:
    handle = _read(PLAYER_ONE_REL)
    for expected in (
        "public sealed class PlayerOneCols",
        "public sealed class PlayerOneIxCols",
        "public PlayerOneIxCols(string tableName)",
    ):
        assert expected in handle, (
            "PlayerOne.g.cs must keep the normal cols/index-cols structural pattern. "
            f"Missing {expected!r}."
        )
    assert "global::SpacetimeDB.IxCol<Player," not in handle, (
        "PlayerOneIxCols must not contain index fields because the view has no indexes."
    )


def test_codegen_docs_cover_read_only_view_distinction() -> None:
    docs = _read(DOCS_REL)
    for expected in (
        "## Database View Definitions",
        "### Read-Only Distinction",
        "misc_exports",
        "bash scripts/codegen/generate-view-test.sh",
        "SpacetimeDB.ViewTestTypes",
        "QueryBuilder.From.PlayerOne()",
        "QueryBuilder.From.PlayersForLevelTwo()",
        "read-only projections",
        "smoke_test",
        "table/reducer-only bindings",
    ):
        assert expected in docs, (
            f"docs/codegen.md must document {expected!r} for Story 10.4."
        )


# ---------------------------------------------------------------------------
# Task 4 / AC 3 - regression anchors for modules with no views
# ---------------------------------------------------------------------------

def test_smoke_test_generated_bindings_remain_unchanged() -> None:
    smoke_client = _read(SMOKE_CLIENT_REL)
    for unexpected in (
        "PlayerOne",
        "PlayersForLevelTwo",
        "LevelTwoPlayerSummary",
        "ViewTest",
        "player_one",
        "players_for_level_two",
    ):
        assert unexpected not in smoke_client, (
            "smoke_test must remain unchanged when no view definitions are exported."
        )


def test_scheduled_test_generated_bindings_remain_unchanged() -> None:
    scheduled_client = _read(SCHEDULED_CLIENT_REL)
    for unexpected in (
        "PlayerOne",
        "PlayersForLevelTwo",
        "LevelTwoPlayerSummary",
        "ViewTest",
        "player_one",
        "players_for_level_two",
    ):
        assert unexpected not in scheduled_client, (
            "scheduled_test must remain unchanged when no view definitions are exported."
        )

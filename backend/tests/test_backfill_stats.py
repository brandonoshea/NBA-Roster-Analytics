from models.salary import PlayerSeason
from backfill.backfill import get_or_create_player, upsert_player_season
from backfill.backfill_stats import extract_stat_rows, upsert_player_season_stats

STATS_HTML = """
<table id="per_game_stats">
<tbody>
<tr>
  <td data-stat="name_display"><a href="/players/t/tatumja01.html">Jayson Tatum</a></td>
  <td data-stat="pts_per_g">27.1</td>
  <td data-stat="trb_per_g">8.1</td>
  <td data-stat="ast_per_g">4.9</td>
</tr>
<tr>
  <td data-stat="name_display">Team Totals</td>
</tr>
</tbody>
</table>
"""


def test_extract_stat_rows_skips_rows_without_player_link():
    rows = extract_stat_rows(STATS_HTML, team="BOS", year=2024)

    assert len(rows) == 1
    row = rows[0]
    assert row["bref_id"] == "tatumja01"
    assert row["points"] == 27.1
    assert row["rebounds"] == 8.1
    assert row["assists"] == 4.9


def test_extract_stat_rows_missing_table_returns_empty():
    assert extract_stat_rows("<div>nothing</div>", team="BOS", year=2024) == []


def test_upsert_player_season_stats_updates_existing_salary_row(db_session):
    player = get_or_create_player(db_session, "Jayson Tatum", "tatumja01")
    upsert_player_season(
        db_session, player, {"season": 2024, "team": "BOS", "salary": 32_000_000.0}
    )

    upsert_player_season_stats(
        db_session,
        player,
        {"season": 2024, "team": "BOS", "points": 27.1, "rebounds": 8.1, "assists": 4.9},
    )
    db_session.commit()

    seasons = db_session.query(PlayerSeason).filter_by(player_id=player.id).all()
    assert len(seasons) == 1
    assert float(seasons[0].salary) == 32_000_000.0
    assert float(seasons[0].points) == 27.1


def test_upsert_player_season_stats_creates_row_when_no_salary_row_exists(db_session):
    player = get_or_create_player(db_session, "Two Way Guy", "twoway01")

    upsert_player_season_stats(
        db_session,
        player,
        {"season": 2024, "team": "BOS", "points": 5.0, "rebounds": 1.0, "assists": 1.0},
    )
    db_session.commit()

    seasons = db_session.query(PlayerSeason).filter_by(player_id=player.id).all()
    assert len(seasons) == 1
    assert seasons[0].salary is None

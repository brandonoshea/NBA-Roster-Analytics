from models.salary import PlayerSeason
from backfill.backfill import (
    _bref_team_code,
    _parse_salary,
    extract_salary_rows,
    get_or_create_player,
    upsert_player_season,
)

SALARY_HTML = """
<div>
<!--
<div class="table_wrapper">
<table id="salaries2">
<tbody>
<tr>
  <td data-stat="player"><a href="/players/j/jamesle01.html">LeBron James</a></td>
  <td data-stat="salary">$47,607,350</td>
</tr>
<tr>
  <td data-stat="player"><a href="/players/d/doncilu01.html">Luka Doncic</a></td>
  <td data-stat="salary"></td>
</tr>
</tbody>
</table>
</div>
-->
</div>
"""


def test_bref_team_code_handles_charlotte_rebrand():
    assert _bref_team_code("CHO", 2014) == "CHA"
    assert _bref_team_code("CHO", 2015) == "CHO"
    assert _bref_team_code("BOS", 2014) == "BOS"


def test_parse_salary_valid():
    assert _parse_salary("$47,607,350") == 47_607_350.0


def test_parse_salary_blank_returns_none():
    assert _parse_salary("") is None


def test_parse_salary_non_numeric_returns_none():
    assert _parse_salary("Did Not Play") is None


def test_extract_salary_rows_parses_bref_id_and_salary():
    rows = extract_salary_rows(SALARY_HTML, team="LAL", year=2024)

    assert len(rows) == 1  # the blank-salary row is dropped
    row = rows[0]
    assert row["bref_id"] == "jamesle01"
    assert row["full_name"] == "LeBron James"
    assert row["salary"] == 47_607_350.0
    assert row["team"] == "LAL"
    assert row["season"] == 2024


def test_extract_salary_rows_missing_table_returns_empty():
    assert extract_salary_rows("<div>no table here</div>", team="LAL", year=2024) == []


def test_get_or_create_player_is_idempotent_on_bref_id(db_session):
    first = get_or_create_player(db_session, "LeBron James", "jamesle01")
    second = get_or_create_player(db_session, "LeBron James (updated)", "jamesle01")

    assert first.id == second.id
    assert db_session.query(second.__class__).count() == 1


def test_upsert_player_season_inserts_then_updates(db_session):
    player = get_or_create_player(db_session, "LeBron James", "jamesle01")
    row = {"season": 2024, "team": "LAL", "salary": 47_000_000.0}

    upsert_player_season(db_session, player, row)
    upsert_player_season(db_session, player, {**row, "salary": 48_000_000.0})
    db_session.commit()

    seasons = db_session.query(PlayerSeason).filter_by(player_id=player.id).all()
    assert len(seasons) == 1
    assert float(seasons[0].salary) == 48_000_000.0

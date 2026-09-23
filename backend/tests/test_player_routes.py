from tests.factories import make_player, make_season, make_valuation


def test_list_players_empty(client):
    resp = client.get("/players")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_players_returns_latest_season_only(client, db_session):
    player = make_player(db_session, full_name="Jayson Tatum")
    make_season(db_session, player, season=2023, points=27)
    make_season(db_session, player, season=2024, points=30)
    db_session.commit()

    resp = client.get("/players")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["season"] == 2024
    assert body[0]["full_name"] == "Jayson Tatum"


def test_list_players_orders_by_points_desc(client, db_session):
    low = make_player(db_session, full_name="Low Scorer", bref_id="low01")
    high = make_player(db_session, full_name="High Scorer", bref_id="high01")
    make_season(db_session, low, season=2024, points=10)
    make_season(db_session, high, season=2024, points=35)
    db_session.commit()

    resp = client.get("/players")

    body = resp.json()
    assert [row["full_name"] for row in body] == ["High Scorer", "Low Scorer"]


def test_list_players_includes_valuation(client, db_session):
    player = make_player(db_session)
    make_season(db_session, player, season=2024)
    make_valuation(db_session, player, season=2024, verdict="overpaid")
    db_session.commit()

    resp = client.get("/players")

    body = resp.json()[0]
    assert body["verdict"] == "overpaid"
    assert body["predicted_salary"] is not None


def test_get_player_not_found(client):
    resp = client.get("/players/999")
    assert resp.status_code == 404


def test_get_player_returns_all_seasons_desc(client, db_session):
    player = make_player(db_session)
    make_season(db_session, player, season=2022)
    make_season(db_session, player, season=2024)
    make_season(db_session, player, season=2023)
    db_session.commit()

    resp = client.get(f"/players/{player.id}")

    assert resp.status_code == 200
    seasons = [row["season"] for row in resp.json()]
    assert seasons == [2024, 2023, 2022]

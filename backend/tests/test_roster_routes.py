from tests.factories import make_player, make_season, make_valuation


def _make_players(db_session, n, **kwargs):
    return [
        make_player(db_session, full_name=f"Player {i}", bref_id=f"player{i}", **kwargs)
        for i in range(n)
    ]


def test_create_roster_empty(client):
    resp = client.post("/rosters", json={"name": "Bench", "player_ids": []})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Bench"
    assert body["player_count"] == 0
    assert body["players"] == []


def test_create_roster_with_players(client, db_session):
    players = _make_players(db_session, 2)
    for p in players:
        make_season(db_session, p, season=2024, salary=5_000_000)
    db_session.commit()

    resp = client.post(
        "/rosters", json={"name": "Starters", "player_ids": [p.id for p in players]}
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["player_count"] == 2
    assert float(body["total_salary"]) == 10_000_000


def test_create_roster_dedupes_player_ids(client, db_session):
    player = make_player(db_session)
    db_session.commit()

    resp = client.post(
        "/rosters", json={"name": "Dupes", "player_ids": [player.id, player.id, player.id]}
    )

    assert resp.status_code == 201
    assert resp.json()["player_count"] == 1


def test_create_roster_rejects_too_many_players(client, db_session):
    players = _make_players(db_session, 16)
    db_session.commit()

    resp = client.post(
        "/rosters", json={"name": "Too Big", "player_ids": [p.id for p in players]}
    )

    assert resp.status_code == 400


def test_create_roster_rejects_unknown_player(client):
    resp = client.post("/rosters", json={"name": "Ghosts", "player_ids": [12345]})
    assert resp.status_code == 404


def test_get_roster_not_found(client):
    resp = client.get("/rosters/999")
    assert resp.status_code == 404


def test_list_rosters(client, db_session):
    player = make_player(db_session)
    db_session.commit()
    client.post("/rosters", json={"name": "A", "player_ids": [player.id]})
    client.post("/rosters", json={"name": "B", "player_ids": []})

    resp = client.get("/rosters")

    assert resp.status_code == 200
    names = {row["name"] for row in resp.json()}
    assert names == {"A", "B"}


def test_delete_roster(client, db_session):
    player = make_player(db_session)
    db_session.commit()
    created = client.post("/rosters", json={"name": "Temp", "player_ids": [player.id]}).json()

    resp = client.delete(f"/rosters/{created['id']}")
    assert resp.status_code == 204

    assert client.get(f"/rosters/{created['id']}").status_code == 404


def test_delete_roster_not_found(client):
    resp = client.delete("/rosters/999")
    assert resp.status_code == 404


def test_add_player_to_roster(client, db_session):
    players = _make_players(db_session, 2)
    db_session.commit()
    roster = client.post(
        "/rosters", json={"name": "Growing", "player_ids": [players[0].id]}
    ).json()

    resp = client.post(f"/rosters/{roster['id']}/players", json={"player_id": players[1].id})

    assert resp.status_code == 201
    assert resp.json()["player_count"] == 2


def test_add_player_roster_not_found(client, db_session):
    player = make_player(db_session)
    db_session.commit()
    resp = client.post("/rosters/999/players", json={"player_id": player.id})
    assert resp.status_code == 404


def test_add_player_not_found(client):
    roster = client.post("/rosters", json={"name": "Solo", "player_ids": []}).json()
    resp = client.post(f"/rosters/{roster['id']}/players", json={"player_id": 12345})
    assert resp.status_code == 404


def test_add_player_already_on_roster(client, db_session):
    player = make_player(db_session)
    db_session.commit()
    roster = client.post(
        "/rosters", json={"name": "Full House", "player_ids": [player.id]}
    ).json()

    resp = client.post(f"/rosters/{roster['id']}/players", json={"player_id": player.id})

    assert resp.status_code == 400


def test_add_player_rejects_when_roster_full(client, db_session):
    players = _make_players(db_session, 16)
    db_session.commit()
    roster = client.post(
        "/rosters", json={"name": "Max", "player_ids": [p.id for p in players[:15]]}
    ).json()

    resp = client.post(
        f"/rosters/{roster['id']}/players", json={"player_id": players[15].id}
    )

    assert resp.status_code == 400


def test_remove_player_from_roster(client, db_session):
    player = make_player(db_session)
    db_session.commit()
    roster = client.post(
        "/rosters", json={"name": "Shrinking", "player_ids": [player.id]}
    ).json()

    resp = client.delete(f"/rosters/{roster['id']}/players/{player.id}")

    assert resp.status_code == 200
    assert resp.json()["player_count"] == 0


def test_remove_player_not_on_roster(client, db_session):
    player = make_player(db_session)
    db_session.commit()
    roster = client.post("/rosters", json={"name": "Empty", "player_ids": []}).json()

    resp = client.delete(f"/rosters/{roster['id']}/players/{player.id}")

    assert resp.status_code == 404


def test_remove_player_roster_not_found(client, db_session):
    player = make_player(db_session)
    db_session.commit()
    resp = client.delete(f"/rosters/999/players/{player.id}")
    assert resp.status_code == 404


def test_roster_totals_use_latest_season_and_valuation(client, db_session):
    player = make_player(db_session)
    make_season(db_session, player, season=2023, salary=1_000_000, minutes_played=100)
    make_season(db_session, player, season=2024, salary=8_000_000, minutes_played=2000)
    make_valuation(db_session, player, season=2024, predicted_salary=9_000_000)
    db_session.commit()

    resp = client.post("/rosters", json={"name": "Valued", "player_ids": [player.id]})

    body = resp.json()
    assert float(body["total_salary"]) == 8_000_000
    assert float(body["total_predicted_salary"]) == 9_000_000

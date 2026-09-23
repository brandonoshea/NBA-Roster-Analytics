from models.salary import Player, PlayerSeason
from models.valuation import PlayerValuation


def make_player(db, *, full_name="Test Player", position="G", bref_id=None, headshot_url=None):
    player = Player(
        full_name=full_name,
        position=position,
        bref_id=bref_id or full_name.lower().replace(" ", "_"),
        headshot_url=headshot_url,
    )
    db.add(player)
    db.flush()
    return player


def make_season(db, player, *, season=2025, team="BOS", salary=1_000_000, points=20,
                 rebounds=5, assists=5, minutes_played=30, **extra):
    row = PlayerSeason(
        player_id=player.id,
        season=season,
        team=team,
        salary=salary,
        points=points,
        rebounds=rebounds,
        assists=assists,
        minutes_played=minutes_played,
        **extra,
    )
    db.add(row)
    db.flush()
    return row


def make_valuation(db, player, *, season=2025, predicted_salary=1_200_000,
                    actual_salary=1_000_000, verdict="underpaid", delta_pct=20):
    row = PlayerValuation(
        player_id=player.id,
        season=season,
        predicted_salary=predicted_salary,
        actual_salary=actual_salary,
        verdict=verdict,
        delta_pct=delta_pct,
    )
    db.add(row)
    db.flush()
    return row

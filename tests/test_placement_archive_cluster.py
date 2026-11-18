"""W117.1: price-archive backfill of the book at submit, and game-clustered placement intervals."""
import json
from datetime import datetime, timezone

from prediction_market_bot.c5_execution.placement import archive_book as ab, model as pm


def _write(d, day, rows):
    (d / f"prices_{day}.jsonl").write_text("\n".join(json.dumps(r) for r in rows))


def test_book_from_ticks_nearest_before_and_max_age(tmp_path):
    _write(tmp_path, "2026-11-17", [
        {"run_ts": "2026-11-17T20:00:00Z", "ticker": "T-A", "yes_bid": 0.40, "yes_ask": 0.44},
        {"run_ts": "2026-11-17T20:20:00Z", "ticker": "T-A", "yes_bid": 0.50, "yes_ask": 0.52},
        {"run_ts": "2026-11-17T20:20:00Z", "ticker": "T-B", "yes_bid": 0.5, "yes_ask": None}])
    ticks = ab.load_ticks(tmp_path, ["T-A", "T-B"], ["2026-11-17"])
    assert "T-B" not in ticks  # one-sided is dropped
    at = datetime(2026, 11, 17, 20, 25, tzinfo=timezone.utc)
    b = ab.book_from_ticks(ticks, "T-A", at, ab.MAX_AGE)
    assert b["spread"] == 0.02 and b["src"] == "archive"
    late = datetime(2026, 11, 17, 21, 30, tzinfo=timezone.utc)
    assert ab.book_from_ticks(ticks, "T-A", late, ab.MAX_AGE) is None  # stale tick is not used


def test_cluster_ci_counts_games_and_widens():
    vals = [0.2, 0.2, 0.2, 0.2, -0.1, -0.1]
    games = ["g1", "g1", "g1", "g1", "g2", "g2"]
    r = pm.cluster_mean_ci(vals, games)
    assert r["n"] == 6 and r["n_games"] == 2
    one = pm.cluster_mean_ci([1.0, 1.0], ["g", "g"])
    assert one["lo"] is None  # one game: no interval
    assert pm.t_crit(1000) < pm.t_crit(5)


def test_game_key_shared_across_markets():
    a = {"sport": "NBA", "ticker": "KXNBAGAME-26NOV17ABCDEF-ABC"}
    b = {"sport": "nba", "ticker": "KXNBASPREAD-26NOV17ABCDEF-ABC5"}
    assert pm.game_of(a) == pm.game_of(b)

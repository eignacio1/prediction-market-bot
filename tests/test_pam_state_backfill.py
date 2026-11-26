"""W129.4 Part B: backfill builders on a synthetic league (no event store needed)."""
import numpy as np
import pandas as pd

from prediction_market_bot.pam import nba_state_backfill as B


def synth(n_games=14):
    rows, tips = [], []
    for g in range(n_games):
        gid = f"00220{g:05d}"
        tip = pd.Timestamp("2024-01-01 00:00", tz="UTC") + pd.Timedelta(days=g, hours=1)
        tips.append({"game_id": gid, "season": 2024, "season_type": "regular-season",
                     "game_date": (tip - pd.Timedelta(hours=5)).strftime("%Y-%m-%d"),
                     "tip_earliest": tip, "tip_latest": tip, "tip_imputed": False})
        for p in range(8):
            mins = 36 - 3 * p if not (p == 0 and g == 13) else 0   # star misses the last game
            rows.append({"game_id": gid, "person_id": 100 + p, "team_id": 1, "first_name": chr(97 + p) * 3, "family_name": "X",
                         "minutes": f"{mins}:00", "field_goals_attempted": 20 - p, "free_throws_attempted": 4,
                         "turnovers": 2, "season": 2024})
    return pd.DataFrame(rows), pd.DataFrame(tips).set_index("game_id")


def test_prior_excludes_own_game_and_future():
    box, tips = synth()
    b = B.player_priors(B.prepare(box, tips))
    star = b[b["pid"] == "100"].sort_values("tip_earliest")
    assert star.iloc[0]["cum_min"] == 0                      # first game has no prior
    assert star.iloc[5]["cum_min"] == 5 * 36                 # strictly the five earlier games
    assert abs(star.iloc[0]["usage_s"] - B.USAGE_PRIOR) < 1e-9   # no history -> prior only


def test_state_rows_are_pretip_and_star_out_drops_into_vacated():
    box, tips = synth()
    b = B.player_priors(B.prepare(box, tips))
    inj = {pd.Timestamp("2024-01-13").date(): {"13:00": {"aaa x": "Out"}}}  # game 13 day; slot <= as_of (tip-4h)
    rows = list(B.build_player_state(b, inj, "2026-11-25T00:00:00Z"))
    for r in rows:
        assert pd.Timestamp(r.known_at) <= pd.Timestamp(r.as_of_ts)
    last = [r for r in rows if r.game_id.endswith("00013") and r.player_id == "101"][0]
    first = [r for r in rows if r.game_id.endswith("00000") and r.player_id == "101"][0]
    assert last.teammates_out == 1 and last.vacated_usage_share > 0
    assert last.minutes_expected > [r for r in rows if r.game_id.endswith("00012") and r.player_id == "101"][0].minutes_expected - 1e-9
    assert first.minutes_share_full_roster is None            # under 5 full-roster prior games
    assert last.role_security is None and last.return_window is None


def test_no_report_means_unknown_not_zero():
    box, tips = synth()
    b = B.player_priors(B.prepare(box, tips))
    rows = list(B.build_player_state(b, {}, "x"))
    assert all(r.teammates_out is None and r.vacated_usage_share is None for r in rows)


def test_availability_counts_prior_games_only():
    box, tips = synth()
    b = B.prepare(box, tips)
    rows = [r for r in B.build_availability(b, "x") if r.player_id == "100"]
    assert rows[0].gp_by_season == {}                        # nothing before game 0
    assert rows[13].gp_by_season["2024"] == [13, 13]
    assert rows[13].missed_by_body_part is None


def test_trait_rows_known_at_fit_end():
    t = B.build_trait_reliability([{"stat": "points", "unit": "min", "r_split_half": 0.9, "k": 60.1}], "x")[0]
    assert t.known_at.startswith("2022-07-01") and t.r_split_half_interval is None

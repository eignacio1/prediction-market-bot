"""W65.1 / EXP-039: NBA player-points shadow is evaluate-and-log only; cron blocks additive and well-formed;
ticker parser, settlement join, registry flip and the player-game judged unit behave as pre-registered."""
from __future__ import annotations

import re
from pathlib import Path

from prediction_market_bot.c5_execution import market_type_registry as R
from prediction_market_bot.pregame_shadow import calibration_engine as ce
from prediction_market_bot.pregame_shadow.nba_player_points_forecaster import parse_market_ticker
from prediction_market_bot.pregame_shadow.nba_player_points_settlement import join_row

ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN = ("submit_order", "open_position", "exit_position", "settle_position", "place_order", "PaperTrader",
             "kelly_fraction", "evaluate_forecast", "c4_risk_engine", "paper_trader", "venue_router",
             "get_band_config", "make_on_row")
SCRIPTS = ("run_nba_player_points_shadow.py", "run_nba_player_points_shadow_settle.py",
           "nba_player_box_backfill.py", "train_nba_player_points.py")
SRC = ("pregame_shadow/nba_player_points_forecaster.py", "pregame_shadow/nba_player_points_model.py",
       "pregame_shadow/nba_player_points_settlement.py")
MAIN = (ROOT / "deploy" / "cron.nba_player_points_shadow").read_text()
PRE = (ROOT / "deploy" / "cron.nba_player_points_shadow_preseason").read_text()


def _jobs(txt):
    return [l for l in txt.splitlines() if l.strip() and not l.startswith("#")]


def test_no_order_or_sizing_path():
    files = [ROOT / "scripts" / s for s in SCRIPTS] + [ROOT / "src/prediction_market_bot" / s for s in SRC]
    for f in files:
        txt = f.read_text()
        for tok in FORBIDDEN:
            assert tok not in txt, f"{f.name} mentions {tok}"


def test_cron_blocks_marked_and_scripts_only_player_points():
    assert MAIN.splitlines()[0] == "# BEGIN EXP-039 NBA PLAYER POINTS"
    assert MAIN.rstrip().splitlines()[-1] == "# END EXP-039 NBA PLAYER POINTS"
    assert PRE.splitlines()[0] == "# BEGIN EXP-039 NBA PLAYER POINTS PRESEASON"
    assert PRE.rstrip().splitlines()[-1] == "# END EXP-039 NBA PLAYER POINTS PRESEASON"
    for j in _jobs(MAIN) + _jobs(PRE):
        assert re.search(r"scripts/(run_nba_player_points_shadow(_settle)?|nba_player_box_backfill)\.py", j), j
        assert "kelly" not in j and ".env" not in j


def test_cron_minutes_off_00_30_and_no_duplicate_schedule():
    mine = _jobs(MAIN) + _jobs(PRE)
    for j in mine:
        for m in (int(x) for x in j.split()[0].split(",")):
            assert m not in (0, 30), j
    sched = [" ".join(j.split()[:5]) for j in mine]
    assert len(sched) == len(set(sched))
    # no (minute) collision with any other family's job that runs every hour at that minute
    for p in (ROOT / "deploy").glob("cron.*"):
        if p.name.startswith("cron.nba_player_points") or p.name == "cron.conf":
            continue
        for j in _jobs(p.read_text()):
            f = j.split()
            if f[1] == "*" and re.fullmatch(r"\d+", f[0]):
                assert " ".join(f[:5]) not in sched, (p.name, j)


def test_cron_conf_mirrors_both_blocks():
    conf = (ROOT / "deploy" / "cron.conf").read_text()
    assert MAIN.strip() in conf and PRE.strip() in conf


def test_existing_nba_blocks_untouched_by_name():
    conf = (ROOT / "deploy" / "cron.conf").read_text()
    assert "# BEGIN EXP-038 NBA" in conf and "# END EXP-038 NBA" in conf


def test_parse_market_ticker():
    p = parse_market_ticker("KXNBAPTS-26OCT08BOSCLE-BOSPGEORGE13-25")
    assert p["game_date"] == "2026-10-08" and p["away"] == "BOS" and p["home"] == "CLE"
    assert p["team"] == "BOS" and p["initial"] == "P" and p["surname"] == "GEORGE" and p["jersey"] == "13"
    assert p["points_threshold"] == 25 and p["strike"] == 24.5
    assert parse_market_ticker("KXNBAPTS-26OCT08BOSCLE-LALPGEORGE13-25") is None      # team not in the game
    assert parse_market_ticker("KXNBAPTS-26OCT08BOSCLE-BOSPGEORGE13-X") is None
    assert parse_market_ticker("garbage") is None


_BOX = [{"player_id": "1", "name": "Paul George", "jersey": "13", "team": "BOS", "home": False, "minutes": 30.0,
         "points": 27.0, "fga": 18.0, "dnp": False},
        {"player_id": "2", "name": "Paul George", "jersey": "8", "team": "BOS", "home": False, "minutes": 0.0,
         "points": 0.0, "fga": 0.0, "dnp": True}]
_CLIM = {"10": 0.7, "15": 0.5, "20": 0.3, "25": 0.15}


def test_settlement_played_dnp_and_unmatched():
    row = {"market_ticker": "KXNBAPTS-26OCT08BOSCLE-BOSPGEORGE13-25", "band": "T1"}
    r = join_row(row, _BOX, _CLIM)
    assert r["settlement"] == "played" and r["y"] == 1.0 and r["p_clim"] == 0.15
    assert r["game_key"] == "2026-10-08:BOS@CLE"
    hi = join_row(row,
                  [dict(_BOX[0], points=24.0)], _CLIM)
    assert hi["y"] == 0.0                                                      # 24 < 25
    dnp = join_row({**row, "market_ticker": "KXNBAPTS-26OCT08BOSCLE-BOSPGEORGE8-10"}, _BOX, _CLIM)
    assert dnp["settlement"] == "dnp_scalar" and dnp["y"] is None
    miss = join_row({**row, "market_ticker": "KXNBAPTS-26OCT08BOSCLE-BOSJTATUM0-10"}, _BOX, _CLIM)
    assert miss["settlement"] == "unmatched_player" and miss["y"] is None


def test_registry_flip_to_shadow_and_count():
    cells = [c for c in R.MARKET_TYPE_REGISTRY.values() if c.market_type == R.MarketType.NBA_PLAYER_POINTS]
    shadow = {c.band.name for c in cells if c.status == R.CellStatus.SHADOW}
    assert shadow == {"T1_MULTI_DAY", "T2_SAME_DAY", "T3_PRE_TIP"}
    assert len(R.MARKET_TYPE_REGISTRY) == 107


def test_engine_policy_is_player_game_and_seeded():
    p = ce.PREREG["NBA_PTS"]
    assert p.unit == "player_game" and p.boot_seed == 20261009 and p.looks == (300, 800)

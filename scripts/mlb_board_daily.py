#!/usr/bin/env python3
"""W129.3 Part B: the MLB daily board. Prices the day's slate with the MLB engine and writes the board the shadow forecaster reads.

Applies: reads the schedule cache (games today, ET date) and three SYNCED input tables (plate-appearance history, the day's
games with starters, the day's lineups; all built off-box, the Stats API 406s the box), prices every game that has a full
lineup and two starters with `joint_board.price_games`, and writes `exp_output/MLB_BOARD/board_<ET date>.json`
({"HOME|AWAY|DATE": {column: p}}, the shape `MLBEngineForecaster` takes). One JSON run line per run goes to
`logs/mlb_board.log` with `games_scheduled` and `rows_written`.
SILENT-EXIT RULE (GG-1957): a run that writes 0 rows on a scheduled game day exits 1 and is a FAIL in health.log
(`silent_exit_status`, read by `scripts/mlb_board_install.py healthcheck`). A missing, stale or unreadable input is a status
and a 0-row run, never a quiet success.
Does not apply: orders, stake, kelly, ledger writes, the price as a bet (it is a layer-1 router input), any network call.

  PYTHONPATH=src:. python3 scripts/mlb_board_daily.py [--now ISO] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

ET = ZoneInfo("America/New_York")
SCHEDULE = ("exp_output", "MLB_GAME", "cache_w47", "games_current.parquet")
INPUTS_DIR = ("exp_output", "MLB_BOARD", "inputs")
INPUT_FILES = ("pa.parquet", "games.parquet", "lineups.parquet")
STAMP = "inputs.meta.json"
LOG_REL = ("logs", "mlb_board.log")
MAX_INPUT_AGE_H = 26.0


def _ts(s: str) -> datetime:
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def et_date(now: datetime) -> str:
    return now.astimezone(ET).date().isoformat()


def games_scheduled(root: Path, now: datetime) -> tuple[int | None, str | None]:
    """(games on today's ET date in the schedule cache, None) or (None, reason) when the cache cannot be read."""
    try:
        import pandas as pd
        g = pd.read_parquet(root.joinpath(*SCHEDULE))
        start = pd.to_datetime(g["start_utc"], utc=True).dt.tz_convert(ET).dt.date.astype(str)
        return int((start == et_date(now)).sum()), None
    except Exception as e:  # noqa: BLE001 -- reported in the run line, never raised
        return None, "schedule_unreadable:%s" % type(e).__name__


def input_status(root: Path, now: datetime, max_age_h: float = MAX_INPUT_AGE_H) -> tuple[bool, str]:
    d = root.joinpath(*INPUTS_DIR)
    missing = [f for f in INPUT_FILES if not (d / f).exists()]
    if missing:
        return False, "no_inputs:" + ",".join(missing)
    try:
        stamp = _ts(json.loads((d / STAMP).read_text())["built_at"])
    except (OSError, ValueError, KeyError):
        return False, "no_input_stamp"
    if now - stamp > timedelta(hours=max_age_h):
        return False, "stale_inputs:%.0fh" % ((now - stamp).total_seconds() / 3600)
    return True, "ok"


def price_slate(games, lineups, pa, n_draws: int = 4000) -> dict:
    """{"HOME|AWAY|DATE": {column: p}} for every game with a full lineup and two starters."""
    from prediction_market_bot.mlb_engine import joint_board, pa_model
    from prediction_market_bot.pregame_shadow.mlb_forecaster import canon
    league = pa_model.fit_league(pa_model.prep(pa))
    hist = pa_model.PAHistory(pa, games)
    inputs = pa_model.game_inputs(games, lineups, hist, league)
    priced = joint_board.price_games(inputs, n=n_draws)
    meta = games.set_index("game_pk")
    out = {}
    for _, r in priced.iterrows():
        m = meta.loc[int(r["game_pk"])]
        key = "%s|%s|%s" % (canon(m["home_team"]), canon(m["away_team"]), str(m["game_date"])[:10])
        out[key] = {c: float(r[c]) for c in priced.columns if c not in ("game_pk", "game_date") and r[c] == r[c]}
    return out


def load_board(path) -> dict:
    """The board file as `MLBEngineForecaster` takes it: {(home, away, ET date): {column: p}} (the file keys are 'HOME|AWAY|DATE')."""
    raw = json.loads(Path(path).read_text())
    return {tuple(k.split("|")): v for k, v in raw.items()}


def run(root: Path = ROOT, now: datetime | None = None, price_fn=price_slate, dry_run: bool = False) -> dict:
    now = now or datetime.now(timezone.utc)
    n_sched, why = games_scheduled(root, now)
    rec = {"ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "date": et_date(now), "games_scheduled": n_sched,
           "games_priced": 0, "rows_written": 0, "status": "ok"}
    ok, status = input_status(root, now)
    if why:
        rec["status"] = why
    elif not ok:
        rec["status"] = status
    elif n_sched == 0:
        rec["status"] = "no_games_today"
    else:
        try:
            import pandas as pd
            d = root.joinpath(*INPUTS_DIR)
            pa, games, lu = (pd.read_parquet(d / f) for f in INPUT_FILES)
            games = games[games["game_date"].astype(str).str[:10] == rec["date"]]
            board = price_fn(games, lu, pa)
            rec["games_priced"] = rec["rows_written"] = len(board)
            if board and not dry_run:
                out = root / "exp_output" / "MLB_BOARD" / ("board_%s.json" % rec["date"])
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(board, sort_keys=True))
            if not board:
                rec["status"] = "priced_zero_games"
        except Exception as e:  # noqa: BLE001
            rec["status"] = "error:%s" % type(e).__name__
            rec["error"] = str(e)[:200]
    rec["silent_exit"] = bool((n_sched or 0) > 0 and rec["rows_written"] == 0)
    if not dry_run:
        log = root.joinpath(*LOG_REL)
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def silent_exit_status(lines: list[str], now: datetime, window_h: float = 24.0) -> tuple[str, str]:
    """('PASS'|'FAIL'|'WARN', detail) from mlb_board.log lines. FAIL: any run in the window with games_scheduled > 0 and
    rows_written == 0. WARN: no run line in the window at all (the caller decides whether a run was due)."""
    cutoff = now - timedelta(hours=window_h)
    seen, bad = 0, []
    for ln in lines:
        try:
            r = json.loads(ln)
            if _ts(r["ts"]) < cutoff:
                continue
        except (ValueError, KeyError, TypeError):
            continue
        seen += 1
        if (r.get("games_scheduled") or 0) > 0 and (r.get("rows_written") or 0) == 0:
            bad.append("%s %s (%d games)" % (r["ts"], r.get("status"), r["games_scheduled"]))
    if bad:
        return "FAIL", "0 rows on a scheduled game day: %s" % "; ".join(bad[-3:])
    if seen == 0:
        return "WARN", "no run line in the last %.0fh" % window_h
    return "PASS", "%d run line(s), none silent" % seen


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--now")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    rec = run(ROOT, _ts(a.now) if a.now else None, dry_run=a.dry_run)
    print(json.dumps(rec, sort_keys=True))
    return 1 if rec["silent_exit"] else 0


if __name__ == "__main__":
    sys.exit(main())

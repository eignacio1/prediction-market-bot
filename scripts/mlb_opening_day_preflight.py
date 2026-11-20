#!/usr/bin/env python3
"""W122.4 / GG-1957: is MLB logging ready? Read-only; exit 1 if any check fails. Run before opening day and daily in season.

Checks: games cache stamp fresh (<26h) · cache has games on/after today · frozen model file present · every game cell has a
ledger row in the last 24h when games are scheduled · fail-closed exits recorded in the last 24h (reported, not hidden).
Usage: python3 scripts/mlb_opening_day_preflight.py [--root .] [--now ISO]
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

GAME_CELLS = ("MLB_MONEYLINE", "MLB_RUN_LINE", "MLB_GAME_TOTAL", "MLB_TEAM_TOTAL")
BANDS = ("T1", "T2", "T3")


def _ts(s):
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def preflight(root: Path, now: datetime, max_age_h: float = 26.0) -> dict:
    cache = root / "exp_output" / "MLB_GAME" / "cache_w47"
    led = root / "exp_output" / "PREGAME_SHADOW"
    checks = {}
    try:
        stamp = _ts(json.loads((cache / "games_current.meta.json").read_text())["refreshed_at"])
        age = (now - stamp).total_seconds() / 3600
        checks["games_cache_fresh"] = {"ok": age <= max_age_h, "age_h": round(age, 1)}
    except (OSError, ValueError, KeyError):
        checks["games_cache_fresh"] = {"ok": False, "age_h": None, "why": "stamp missing/unreadable"}
    n_ahead = None
    try:
        import pandas as pd
        g = pd.read_parquet(cache / "games_current.parquet")
        col = "game_date" if "game_date" in g else g.columns[0]
        n_ahead = int((pd.to_datetime(g[col]).dt.date >= now.date()).sum())
    except Exception as e:  # noqa: BLE001 - reported, never raised
        checks["schedule_has_games_ahead"] = {"ok": False, "why": repr(e)[:120]}
    if n_ahead is not None:
        checks["schedule_has_games_ahead"] = {"ok": n_ahead > 0, "games_today_or_later": n_ahead}
    checks["model_file_present"] = {"ok": (root / "models" / "mlb_game_pregame_v1.json").exists()}
    cutoff = now - timedelta(hours=24)
    rows = {}
    for c in GAME_CELLS:
        n = 0
        for b in BANDS:
            f = led / f"MLB_{c}_{b}.jsonl"
            if f.exists():
                for line in f.read_text().splitlines():
                    try:
                        if _ts(json.loads(line)["ts_utc"]) >= cutoff:
                            n += 1
                    except (ValueError, TypeError, KeyError):
                        continue
        rows[c] = n
    games_expected = bool(n_ahead)
    checks["cells_logged_24h"] = {"ok": (not games_expected) or all(v > 0 for v in rows.values()), "rows_24h": rows,
                                  "games_expected": games_expected}
    fc = led / "_MLB_FAILCLOSED.jsonl"
    nfc = 0
    if fc.exists():
        for line in fc.read_text().splitlines():
            try:
                if _ts(json.loads(line)["ts"]) >= cutoff:
                    nfc += 1
            except (ValueError, KeyError):
                continue
    checks["failclosed_exits_24h"] = {"ok": True, "count": nfc}  # informational: a number, not a pass/fail
    return {"ok": all(v["ok"] for v in checks.values()), "now": now.isoformat(), "checks": checks}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--now")
    a = ap.parse_args(argv)
    now = _ts(a.now) if a.now else datetime.now(timezone.utc)
    res = preflight(Path(a.root), now)
    print(json.dumps(res, indent=1))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

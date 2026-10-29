#!/usr/bin/env python3
"""PROOF_CALENDAR generator (W94.Q Part B). Read-only.

Two modes:
  --emit          (runs on the box, read-only) prints one JSON blob: the calibration engine's cells plus, per cell,
                  the dates its judged games settled, and per-sport distinct-game counts per archive day.
  --input FILE    (runs anywhere) reads that blob and writes 04_EXECUTION/PROOF_CALENDAR.md. Never typed by hand.

Projection method (stated once, applies to every row): the rate is judged units per ACTIVE day over the trailing 14
days (days inside the sport's season window; an off-season gap is not counted as a zero-rate day), the future walks the
real season windows below (zero accrual outside them), and the interval is the 10th-90th percentile of a
Gamma(k + 0.5, active_days) posterior on that rate (Poisson counts, Jeffreys prior), seeded. It applies when the recent
14 days are representative of the rest of the season; it does not when the schedule is lumpy (NFL bye weeks) or the
trailing window is mostly a ramp-up. A row with k = 0 in the window has no projection, and says so.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WINDOW_DAYS = 14
HORIZON = date(2029, 1, 1)
DRAWS = 2000
SEED = 20261029

# Regular-season windows (inclusive). Dates the schedule has not published are labelled assumptions in the output.
SEASONS: dict[str, list[tuple[str, str]]] = {
    "NFL": [("2026-09-10", "2027-01-10"), ("2027-09-09", "2028-01-09")],
    "NBA": [("2026-10-20", "2027-04-12"), ("2027-10-19", "2028-04-10")],
    "NHL": [("2026-10-07", "2027-04-17"), ("2027-10-06", "2028-04-15")],
    "MLB": [("2026-03-26", "2026-11-01"), ("2027-03-25", "2027-10-03"), ("2028-03-23", "2028-10-01")],
}
SEASON_NOTE = ("NFL regular season ends 2027-01-10 (EXP-041 s.4); MLB pauses after the World Series (~2026-11-01) until "
               "~2027-03-25 (EXP-042); NBA/NHL window ends are the usual calendar, not a published schedule (assumption).")

MODAL_RE = re.compile(r"Vs market, every cell:\**\s*([A-Z][A-Z ]+?)\s*≈\s*(\d+)%")
NFL_EXPECT = "12_EXPLORATORY/NFL_FIRST_LOOK_EXPECTATIONS.md"
MODAL_BY_SPORT = {
    "NBA": "SHADOW (CI spans zero) (EXP-038 s.4; EXP-039: SHADOW or negative)",
    "NHL": "not stated in EXP-036",
}

# Frozen hypotheses that are not engine cells. need = judged units for the call that can PASS.
STATIC = [
    {"id": "EXP-041", "tests": "NFL market-anchored pooled paired dBrier, 12 cells (4 families), one test", "sport": "NFL",
     "freeze": "2026-10-22", "need": 500, "unit": "games", "family": "KXNFL",
     "modal": "NOT DISTINGUISHABLE ~85% (BEATS ~5%, HARMS ~10%)",
     "note": "no scored look below 500 games; 2026 season alone cannot reach it; descriptive count only 2027-01-10"},
    {"id": "EXP-043 H-B", "tests": "pooled ladder trigger, exact fee, NFL now / NBA+NHL from archive install / MLB from opening",
     "sport": "NFL", "freeze": "2026-10-28", "need": 7535, "unit": "games", "family": "KXNFL",
     "modal": "net near zero, interval includes zero, UNDECIDED at the checkpoint",
     "note": "NFL stratum only; NBA/NHL/MLB add strata, so this rate is a floor; descriptive checkpoint 2027-01-31"},
    {"id": "EXP-043 H-A net2-5c", "tests": "KXMLBTOTAL T0-2h tight, gap 2-5c, forward", "sport": "MLB",
     "freeze": "2026-10-28", "need": 284, "unit": "games", "family": "KXMLBTOTAL",
     "modal": "FAIL or UNDECIDED", "note": "counts every game with a snapshot; the cell's qualifying subset is smaller (upper bound)"},
    {"id": "EXP-043 H-A net5c+", "tests": "KXMLBTOTAL T0-2h tight, gap 5c+, forward", "sport": "MLB",
     "freeze": "2026-10-28", "need": 61, "unit": "games", "family": "KXMLBTOTAL",
     "modal": "FAIL or UNDECIDED", "note": "counts every game with a snapshot; the cell's qualifying subset is smaller (upper bound)"},
] + [
    {"id": f"EXP-042 cell {i}", "tests": "W89.2 ride cell %d, forward (price archive after the 2026-10-28 freeze)" % i, "sport": "NFL" if i == 6 else "MLB",
     "freeze": "2026-10-28", "need": n, "unit": "games", "family": "KXNFL" if i == 6 else "KXMLB",
     "modal": "regress to zero; <= 2 of 11 hold; zero PASS before 2027-06",
     "note": "counts every game with a snapshot in the sport (upper bound on the cell's subset)"}
    for i, n in zip(range(1, 12), (1367, 823, 158, 307, 196, 408, 855, 214, 224, 75, 557))
]


# --------------------------------------------------------------------------- pure calendar maths
def _d(s: str) -> date:
    return date.fromisoformat(s[:10])


def is_active(sport: str, day: date) -> bool:
    return any(_d(a) <= day <= _d(b) for a, b in SEASONS.get(sport, []))


def trailing_rate(unit_dates: list[str], sport: str, today: date, window: int = WINDOW_DAYS) -> tuple[int, int]:
    """(units settled in the trailing window, ACTIVE days in that window). Window = the `window` days ending yesterday."""
    days = [today - timedelta(days=i) for i in range(1, window + 1)]
    active = sum(1 for d in days if is_active(sport, d))
    lo, hi = days[-1], days[0]
    k = sum(1 for s in unit_dates if lo <= _d(s) <= hi)
    return k, active


def walk(need: float, rate: float, sport: str, today: date) -> date | None:
    """First day the cumulative expected count reaches `need`, accruing `rate` per active day from tomorrow on."""
    if need <= 0:
        return today
    if rate <= 0:
        return None
    cum, d = 0.0, today
    while d < HORIZON:
        d += timedelta(days=1)
        if is_active(sport, d):
            cum += rate
            if cum >= need:
                return d
    return None


def project(need_left: float, k: int, active_days: int, sport: str, today: date,
            draws: int = DRAWS, seed: int = SEED) -> dict:
    """Point date (rate = k / active_days) and an 80% interval (10th-90th pct of the Gamma(k+.5, active_days) rate)."""
    if need_left <= 0:
        return {"point": today.isoformat(), "lo": None, "hi": None, "note": "reached"}
    if k <= 0 or active_days <= 0:
        return {"point": None, "lo": None, "hi": None,
                "note": f"no accrual in the trailing {WINDOW_DAYS}d ({k} units / {active_days} active days)"}
    rng = random.Random(seed)
    rates = sorted(rng.gammavariate(k + 0.5, 1.0 / active_days) for _ in range(draws))
    r_lo, r_hi = rates[int(0.10 * draws)], rates[int(0.90 * draws)]
    p = walk(need_left, k / active_days, sport, today)
    early, late = walk(need_left, r_hi, sport, today), walk(need_left, r_lo, sport, today)
    return {"point": p.isoformat() if p else None, "lo": early.isoformat() if early else None,
            "hi": late.isoformat() if late else None, "rate": k / active_days,
            "note": "" if p else f"not reached by {HORIZON.isoformat()}"}


def fmt_proj(pr: dict) -> str:
    if not pr.get("point"):
        return pr.get("note") or "n/a"
    hi = pr["hi"] or f"> {HORIZON.isoformat()}"
    return f"{pr['point']} [{pr['lo'] or pr['point']}, {hi}]"


# --------------------------------------------------------------------------- box side
def emit(repo: Path, now: datetime | None = None) -> dict:
    sys.path.insert(0, str(repo / "src"))
    from prediction_market_bot.pregame_shadow import calibration_engine as ce
    now = now or datetime.now(timezone.utc)
    res = ce.run(repo, now, persist=False)
    dates: dict[str, list[str]] = {}
    for c in ce.discover_cells(repo):
        pol = ce.policy_for(c.get("policy", c["sport"]))
        rows = [r for r in ce.first_row_per_unit(ce.load_settled(c)) if ce.eligible(pol, r)]
        dates[c["cell"]] = sorted(str(r.get("start_time_utc") or r["ts_utc"])[:10] for r in rows)
    cells = [{k: c.get(k) for k in ("cell", "sport", "band", "market_type", "rows", "judged_n", "settled_games",
                                    "first_look_n", "status_text", "projection")} | {"settle_dates": dates.get(c["cell"], [])}
             for c in res["cells"]]
    arch: dict[str, dict[str, int]] = {}
    for p in sorted((repo / "exp_output/PRICE_ARCHIVE").glob("prices_*.jsonl")):
        day = p.stem.split("_", 1)[1]
        seen: dict[str, set] = {}
        with open(p) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                ev, ser = r.get("event_ticker") or "", r.get("series_ticker") or ""
                if ser:
                    seen.setdefault(ser, set()).add(ev)
        arch[day] = {s: len(v) for s, v in seen.items()}
    return {"generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "cells": cells, "archive_games_per_day": arch}


# --------------------------------------------------------------------------- render
def archive_series(arch: dict[str, dict[str, int]], family: str, since: str, until: date) -> dict[str, int]:
    """Per-day distinct-event count summed over series whose ticker starts with `family`, for days in [since, until)."""
    out: dict[str, int] = {}
    for day, per in arch.items():
        if since <= day < until.isoformat():
            n = sum(v for s, v in per.items() if s.startswith(family) and s.endswith("GAME"))
            out[day] = n
    return out


def static_rows(arch: dict, today: date) -> list[dict]:
    rows = []
    for h in STATIC:
        per_day = archive_series(arch, h["family"], h["freeze"], today)
        total = sum(per_day.values())
        # a game is seen on several archive days (ladders open ahead); the day-count is an upper bound on accrual.
        k = sum(v for d, v in per_day.items() if (today - _d(d)).days <= WINDOW_DAYS)
        active = sum(1 for i in range(1, WINDOW_DAYS + 1) if is_active(h["sport"], today - timedelta(days=i)))
        pr = project(h["need"] - total, k, active, h["sport"], today)
        rows.append({"id": h["id"], "tests": h["tests"], "rows": f"{total} game-days seen since {h['freeze']}",
                     "rate": f"{k} in {active} active days" if active else "season paused",
                     "judged_n": f"{h['need']} {h['unit']}", "proj": fmt_proj(pr), "modal": h["modal"], "note": h["note"]})
    return rows


def engine_rows(blob: dict, today: date, modal_nfl: str) -> list[dict]:
    out = []
    for c in blob["cells"]:
        need = (c.get("first_look_n") or 0) - (c.get("judged_n") or 0)
        k, active = trailing_rate(c.get("settle_dates", []), c["sport"], today)
        pr = project(need, k, active, c["sport"], today) if c.get("first_look_n") else {"point": None, "note": "no look pre-registered"}
        eng = (c.get("projection") or {}).get("date") or (c.get("projection") or {}).get("note") or "-"
        modal = modal_nfl if c["sport"].startswith("NFL") else MODAL_BY_SPORT.get(c["sport"], "see prereg")
        out.append({"id": c["cell"], "tests": f"{c['sport']} {c['market_type']} {c['band']} vs market",
                    "rows": f"{c['rows']} rows / {c['judged_n']} judged",
                    "rate": f"{k} in {active} active days" if active else "season paused",
                    "judged_n": str(c.get("first_look_n") or "-"), "proj": fmt_proj(pr),
                    "modal": modal, "note": f"engine: {eng}"})
    return out


def render(blob: dict, repo: Path, today: date | None = None) -> str:
    today = today or _d(blob["generated"])
    modal = "see " + NFL_EXPECT
    p = repo / NFL_EXPECT
    if p.exists() and (m := MODAL_RE.search(p.read_text())):
        modal = f"{m.group(1).strip()} ~{m.group(2)}% (first look)"
    rows = engine_rows(blob, today, modal) + static_rows(blob.get("archive_games_per_day", {}), today)
    L = ["# PROOF CALENDAR", "",
         f"*Generated by `scripts/proof_calendar.py` from the box read of {blob['generated']}. Never edited by hand; "
         "regenerate with the `proof_calendar_read` box task, then `--input`.*", "",
         "**Method.** Rate = judged units per active day over the trailing 14 days; the future walks the real season "
         "windows (zero accrual outside them); interval = 10th-90th percentile of a Gamma(k+0.5, active_days) posterior "
         "on that rate. Applies when the last 14 days are representative of the season; does not for lumpy schedules "
         "(NFL byes) or a ramp-up window. " + SEASON_NOTE, "",
         f"**{len(blob['cells'])} calibration-engine cells + {len(STATIC)} frozen hypotheses = {len(rows)} rows.** "
         "A projected date is when to LOOK, not a prediction of the verdict; no score is read below the judged n.", "",
         "| Hypothesis | What it tests | Rows to date | 14-day accrual | Judged n | Projected look (80% interval) | Pre-registered modal outcome | Note |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append("| " + " | ".join(str(r[k]).replace("|", "/") for k in
                                   ("id", "tests", "rows", "rate", "judged_n", "proj", "modal", "note")) + " |")
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--input")
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--out", default="04_EXECUTION/PROOF_CALENDAR.md")
    a = ap.parse_args(argv)
    repo = Path(a.repo)
    if a.emit:
        print(json.dumps(emit(repo)))
        return 0
    if not a.input:
        ap.error("--input FILE or --emit")
    blob = json.loads(Path(a.input).read_text())
    (repo / a.out).write_text(render(blob, repo))
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""READ-ONLY (W105.1 / B-051): the blend-weight test's cell table at a planned look.  Pre-registration:
12_EXPLORATORY/blend_test/BLEND_TEST_PREREGISTRATION_20261106.md (frozen).

GATED: before a cell's planned look this prints ONLY "n so far / next look at" for that cell - no score, no z, no w.
At a reached look k the statistic is computed on exactly the FIRST n_k games (by game date), never on later games, so a read
between looks cannot leak extra data.  Nothing is written.  Output is one aggregated table (well under 60 KB)."""
from __future__ import annotations

import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from prediction_market_bot.nba_engine.live_scoring import outcome  # noqa: E402
from prediction_market_bot.quant import blend, blend_power as bp  # noqa: E402
from prediction_market_bot.quant.multiplicity import spend_obrien_fleming  # noqa: E402

ARMS = {"v1": "NBA_ENGINE_LIVE", "v2": "NBA_ENGINE_LIVE_V2", "v3": "NBA_ENGINE_LIVE_V3"}
FAMS = ("NBA_MONEYLINE", "NBA_SPREAD", "NBA_GAME_TOTAL", "NBA_TEAM_TOTAL")
NMAX = {"v1": 400, "v2": 400, "v3": 100}
FRACS = (0.25, 0.5, 0.75, 1.0)
ALPHA = 0.05
HARD_STOP = dt.date(2027, 4, 20)
ABBR = {"GS": "GSW", "NO": "NOP", "NY": "NYK", "SA": "SAS", "UTAH": "UTA", "WSH": "WAS"}
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=%s"


def look_counts(arm: str) -> list:
    return [int(round(f * NMAX[arm])) for f in FRACS]


def fetch_finals(d0: dt.date, d1: dt.date) -> dict:
    out: dict = {}
    d = d0
    while d <= d1:
        try:
            data = json.load(urllib.request.urlopen(ESPN % d.strftime("%Y%m%d"), timeout=15))
        except Exception:
            data = {}
        for ev in data.get("events", []):
            comp = (ev.get("competitions") or [{}])[0]
            if not (ev.get("status", {}).get("type", {}).get("completed")):
                continue
            t = {c["homeAway"]: c for c in comp.get("competitors", [])}
            if "home" in t and "away" in t:
                h, a = (ABBR.get(t[k]["team"]["abbreviation"], t[k]["team"]["abbreviation"]) for k in ("home", "away"))
                out.setdefault((h, a), []).append((dt.date.fromisoformat(ev["date"][:10]),
                                                   (int(t["home"]["score"]), int(t["away"]["score"]))))
        d += dt.timedelta(days=1)
    return out


def _final_for(r: dict, finals: dict):
    gd = dt.date.fromisoformat(r["game_date"])
    best = None
    for d, f in finals.get((r["home"], r["away"]), []):
        k = abs((d - gd).days)
        if k <= 1 and (best is None or k < best[0]):
            best = (k, f)
    return best[1] if best else None


def cell_rows(rows: list, fam: str, finals: dict) -> list:
    data = []
    for r in rows:
        if r["family"] != fam or r.get("p_market") is None or r.get("p_engine") is None or not bp.eligible(r["p_market"]):
            continue
        f = _final_for(r, finals)
        y = None if f is None else outcome(r, f)
        if y is not None:
            data.append((r["game_date"], (r["game_date"], r["home"], r["away"]), r["p_market"], r["p_engine"], float(y)))
    return data


def first_n_games(data: list, n: int) -> list:
    """Rows of the first n games by (game_date, home, away); deterministic and independent of later games."""
    games = sorted({d[1] for d in data})[:n]
    keep = set(games)
    return [(d[1], d[2], d[3], d[4]) for d in data if d[1] in keep]


def n_games(data: list) -> int:
    return len({d[1] for d in data})


def cell_at_look(data: list, arm: str, today: dt.date) -> dict:
    """Gated status of one cell.  Before the next look: only counts.  At reached looks: z, p, w~, bound, CV gain."""
    n = n_games(data)
    counts = look_counts(arm)
    reached = [k for k, c in enumerate(counts) if n >= c] if today <= HARD_STOP else []
    out = {"n": n, "looks_at": counts, "reached": [k + 1 for k in reached], "reads": {}}
    for k in reached:
        sub = first_n_games(data, counts[k])
        gs = bp.game_scores(sub)
        z = bp.score_z([v[0] for v in gs.values()])
        rd = {"games": counts[k], "z": z, "p": bp.z_to_p(z), "w_tilde": bp.w_score_estimate(gs)}
        rd["w_upper95"] = bp.w_score_upper(gs, b=1000, seed=20261106)
        gbc = blend.cv_gain(sub, "linear", seed=20261106)["gain_by_cluster"]
        per = [sum(v) / len(v) for v in gbc.values() if v]
        rd["cv_gain"] = round(sum(per) / len(per), 6) if per else None
        out["reads"][k + 1] = rd
    return out


def holm_by_look(cells: dict) -> dict:
    """{look: {cell: rejected}} - Holm across ALL 12 cells at each look, unreached cells p = 1, cumulative alpha a_k."""
    keys = sorted(cells)
    res = {}
    for k in (1, 2, 3, 4):
        ps = [cells[c]["reads"].get(k, {}).get("p", 1.0) if cells[c]["reads"].get(k) else 1.0 for c in keys]
        if all(p == 1.0 for p in ps):
            continue
        rej = bp.holm_at_look(ps, spend_obrien_fleming(FRACS[k - 1], ALPHA))
        res[k] = dict(zip(keys, rej))
    return res


def decide(cell: dict, holm: dict, key: str, arm: str) -> str:
    for k, rd in sorted(cell["reads"].items()):
        if holm.get(k, {}).get(key) and (rd["cv_gain"] or 0) > 0:
            return "MOVE"
    if 4 in cell["reads"]:
        ub = cell["reads"][4]["w_upper95"]
        return "NO MOVE" if ub is not None and ub < 0.5 else "INCONCLUSIVE"
    return "NOT AT A LOOK"


def build(root: Path, finals: dict, today: dt.date) -> dict:
    cells = {}
    for arm, d in ARMS.items():
        p = root / "exp_output" / d / "rows.jsonl"
        rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
        for fam in FAMS:
            cells[f"{arm}/{fam}"] = cell_at_look(cell_rows(rows, fam, finals), arm, today)
    holm = holm_by_look(cells)
    for key, c in cells.items():
        c["decision"] = decide(c, holm, key, key.split("/")[0])
    return {"cells": cells, "holm": {k: v for k, v in holm.items()}}


def render(res: dict) -> str:
    lines = ["blend-test cell table (pre-registration BLEND_TEST_PREREGISTRATION_20261106; gated)"]
    for key, c in sorted(res["cells"].items()):
        nxt = next((x for x in c["looks_at"] if x > c["n"]), None)
        if not c["reads"]:
            lines.append(f"{key}: n so far {c['n']} / look at {nxt}")
            continue
        for k, rd in sorted(c["reads"].items()):
            lines.append(f"{key} look{k}@{rd['games']}: z={rd['z']:.3f} p={rd['p']:.4f} w~={rd['w_tilde']:.3f} "
                         f"w_up95={rd['w_upper95']} cv_gain={rd['cv_gain']}")
        lines.append(f"{key}: n so far {c['n']} next look at {nxt} -> {c['decision']}")
    return "\n".join(lines)


def main() -> int:
    today = dt.datetime.now(dt.timezone.utc).date()
    dates = []
    for d in ARMS.values():
        p = ROOT / "exp_output" / d / "rows.jsonl"
        if p.exists():
            dates += [json.loads(l)["game_date"] for l in p.read_text().splitlines() if l.strip()]
    if not dates:
        print("no rows"); return 0
    d0, d1 = dt.date.fromisoformat(min(dates)) - dt.timedelta(days=1), min(today, dt.date.fromisoformat(max(dates)) + dt.timedelta(days=1))
    print(render(build(ROOT, fetch_finals(d0, d1), today)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

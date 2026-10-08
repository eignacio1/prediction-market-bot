"""First-look REPORT (W59.2 Part B). One renderer for the real report and the synthetic rehearsal, so the
rehearsal is in the exact format the real one will have. Pure formatting over `compute_scores` output:
it never scores, never unseals, and prints nothing for a cell that has not reached its look.
"""
from __future__ import annotations

import dataclasses
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from . import calibration_engine as ce


def _ci(d: Any) -> str:
    if not isinstance(d, dict):
        return "unavailable (no climatology field on this sport's settled rows)"
    lo, hi = d["ci95"]
    return f"{d['mean']:+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]"


def render_report(cells: list[dict], title: str, synthetic: bool = False, note: str = "") -> str:
    """cells: dicts carrying `cell`, `sport`, `band` and the compute_scores fields (status, verdict, release, scores)."""
    L = [f"# {title}", ""]
    if synthetic:
        L += ["> **SYNTHETIC - rehearsal of the report format on generated data. No cell below is a real cell, "
              "no number is a finding, nothing here releases a look.**", ""]
    if note:
        L += [note, ""]
    L += ["Sign convention: `delta_brier_vs_X = Brier(X) - Brier(model)`; positive = model better.",
          "Scoring unit: first ledger row per (market_ticker, band); inference: game-cluster bootstrap.", ""]
    L += ["| cell | status | n (games scored) | delta-Brier vs market (95% CI) | delta-Brier vs climatology (95% CI) | verdict |",
          "|---|---|---:|---|---|---|"]
    detail: list[str] = []
    for c in cells:
        v = c.get("verdict") or {}
        if not v:       # not at a look: say so, print no score
            L.append(f"| {c['cell']} | {c['status_text']} | {c['judged_n']} | - | - | none (not at a look) |")
            continue
        flag = " ⚠ model worse than climatology" if v.get("model_failure_vs_climatology") else ""
        L.append(f"| {c['cell']} | {c['status_text']} | {v['n']} | {_ci(v['delta_brier_vs_market'])} | "
                 f"{_ci(v['delta_brier_vs_climatology'])}{flag} | **{v['verdict']}** |")
        b = c["scores"]["bootstrap"]
        detail += [f"### {c['cell']}", f"- verdict **{v['verdict']}** - rule: {v['rule']}",
                   f"- E_net per contract (entry, expected): k007 {v['e_net_entry_k007']:+.4f}, kmult {v['e_net_entry_kmult']:+.4f}",
                   f"- bootstrap: B={b['B']}, seed={b['seed']}, unit={b['unit']}",
                   f"- release: look {c['release']['look']}, {len(c['release']['games'])} games, "
                   f"digest `{c['release']['digest'][:16]}...`, frozen={c['release']['frozen']}",
                   f"- pre-registration: {c.get('prereg', ce.PREREG[c['sport']].citation)}", ""]
    return "\n".join(L + [""] + detail) + "\n"


def synthetic_games(n: int, p: float, q: float, seed: int, mid: float = 0.5, strikes: int = 1) -> list[dict]:
    """n games in start order; model says p, true win rate q, market says mid. Deterministic in seed."""
    rng = random.Random(seed)
    base = datetime(2026, 10, 1, tzinfo=timezone.utc)
    rows = []
    for i in range(n):
        st = (base + timedelta(hours=6 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        for k in range(strikes):
            rows.append({"market_ticker": f"S{i:05d}-{k}", "band": "T1", "ts_utc": st, "game_key": f"SG{i:05d}",
                         "p_yes": p, "mid": mid, "yes_bid": mid - 0.01, "yes_ask": mid + 0.01,
                         "y": 1.0 if rng.random() < q else 0.0, "p_clim": 0.5, "start_time_utc": st})
    return rows


SCENARIOS = (   # (cell, sport, model p, true rate, market mid)
    ("SYN_NFL_model_worse", "NFL", 0.90, 0.30, 0.50),
    ("SYN_NFL_no_edge", "NFL", 0.52, 0.52, 0.50),
    ("SYN_NFL_real_edge", "NFL", 0.70, 0.70, 0.55),
    ("SYN_MLB_no_edge", "MLB", 0.50, 0.50, 0.50),
    ("SYN_NHL_no_edge", "NHL", 0.50, 0.50, 0.50),
)


def synthetic_cells(nhl_boot_b: int = 400) -> list[dict]:
    out = []
    for i, (name, sport, p, q, mid) in enumerate(SCENARIOS):
        pol = ce.PREREG[sport]
        if sport == "NHL":
            pol = dataclasses.replace(pol, boot_b=nhl_boot_b)     # real spec is B=10,000; reduced here for runtime, stated in the note
        rows = synthetic_games(pol.looks[0], p, q, 7000 + i, mid)
        for r in rows:
            if sport == "MLB":
                r["start_time_utc"] = "2027-" + r["start_time_utc"][5:]; r.pop("p_clim")     # 2027 regular season; MLB has no p_clim
        c = ce.compute_scores(pol, "T1", rows, {})
        c.update({"cell": name, "sport": sport, "band": "T1"})
        out.append(c)
    # one cell below its look: must print no score
    c = ce.compute_scores(ce.PREREG["NFL"], "T1", synthetic_games(59, 0.6, 0.6, 1), {})
    c.update({"cell": "SYN_NFL_59_games", "sport": "NFL", "band": "T1"})
    return out + [c]

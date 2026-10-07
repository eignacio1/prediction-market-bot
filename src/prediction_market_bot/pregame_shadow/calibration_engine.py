"""Pre-registration-aware calibration engine (W58.3). Read-only; stdlib + scoring + fees only.

One pipeline for every shadow cell. Each cell is governed by ITS OWN pre-registration, held in the
single reviewed PREREG table below (one citation per row). Counts are always emitted. A score field
is emitted only where the governing policy allows it, and the gate lives INSIDE ``compute_scores`` --
calling it directly on a sealed cell still returns counts and a status, never a score.

Sign convention is scoring.py's (pre-registered): delta_brier_vs_X = Brier(X) - Brier(model);
POSITIVE means the model is better. Never change a PREREG parameter here; change the
pre-registration (a superseding document) and cite it.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from prediction_market_bot.pregame_shadow import scoring

STATUS_SEALED, STATUS_PRELIM, STATUS_JUDGED = "SEALED", "PRELIMINARY", "JUDGED"
STATUS_HISTORICAL, STATUS_COUNTS = "HISTORICAL", "COUNTS ONLY"

# Every key a sealed cell must never carry.
SCORE_KEYS = frozenset({
    "brier_model", "brier_market", "brier_climatology", "logloss_model", "logloss_market",
    "delta_brier_vs_market", "delta_brier_vs_climatology", "reliability_bins", "brier_decomposition",
    "e_net_entry_expected_k007", "e_net_entry_expected_kmult", "e_net_realised_best_side", "scores",
})
N_BINS = 10


@dataclass(frozen=True)
class Policy:
    sport: str
    looks: tuple[int, ...]            # judged-n at which a look is allowed; () = counts only
    mode: str                         # "sealed_until_look" | "preliminary_below" | "counts_only"
    citation: str
    eligible_from: str | None = None  # rows with start_time_utc before this are counted, never scored
    sealed_while_gg_open: tuple[tuple[str, str], ...] = ()   # (band, GG id): sealed in that band
    has_climatology: bool = True


PREREG: dict[str, Policy] = {
    "NFL": Policy("NFL", (60, 150), "sealed_until_look",
                  "EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, "
                  "second look 150; no scoring before judged n; models frozen"),
    "MLB": Policy("MLB", (150, 600), "sealed_until_look",
                  "EXP-037 MLB pre-registration (2026-10-02): 2026 postseason rows never scored (head-start, "
                  "counted only); judged looks use 2027 regular season only, n=150 then 600",
                  eligible_from="2027-03-01", has_climatology=False),
    "NHL": Policy("NHL", (2500,), "preliminary_below",
                  "EXP-036 NHL pre-registration (2026-10-02): judged n=2,500 settled games per cell; below that "
                  "figures are PRELIMINARY only; T3 sealed while GG-401 is open",
                  sealed_while_gg_open=(("T3", "GG-401"),), has_climatology=False),
}
# Cells with no pre-registration (e.g. NBA until W58.2/EXP-038 lands) fall through to counts only.
NO_PREREG = Policy("-", (), "counts_only", "no pre-registration: counts only")

# Historical families already scored in Waves 38-44: shown in full, citing the existing results.
HISTORICAL: dict[str, str] = {
    "MLB player-hits (KXMLBHIT)": "05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/EXP028_pregame_mlb_hits_RESULTS_2026-09-30.md",
    "T4M-PROJ": "05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES (Waves 38-44 results)",
}


def policy_for(sport: str) -> Policy:
    return PREREG.get(sport, NO_PREREG)


# ── status (the single source of the seal decision) ────────────────────────────

def cell_status(policy: Policy, band: str, n_judged: int, gg_open: dict[str, bool]) -> str:
    for b, gg in policy.sealed_while_gg_open:
        if b == band and gg_open.get(gg, True):          # unknown GG state is treated as open
            return STATUS_SEALED
    if policy.mode == "counts_only" or not policy.looks:
        return STATUS_COUNTS
    if n_judged >= policy.looks[0]:
        return STATUS_JUDGED
    return STATUS_PRELIM if policy.mode == "preliminary_below" else STATUS_SEALED


def status_text(policy: Policy, status: str, n_judged: int) -> str:
    target = policy.looks[0] if policy.looks else None
    if status == STATUS_SEALED:
        return f"SEALED ({n_judged} of {target})" if target else "SEALED"
    if status == STATUS_PRELIM:
        return f"PRELIMINARY (n={n_judged} of {target})"
    return status


# ── metrics (built on scoring primitives) ─────────────────────────────────────

def reliability_bins(ps: list[float], ys: list[float], n_bins: int = N_BINS) -> list[dict]:
    bins: list[list[tuple[float, float]]] = [[] for _ in range(n_bins)]
    for p, y in zip(ps, ys):
        bins[min(int(p * n_bins), n_bins - 1)].append((p, y))
    out = []
    for i, b in enumerate(bins):
        out.append({"lo": i / n_bins, "hi": (i + 1) / n_bins, "n": len(b),
                    "mean_p": sum(p for p, _ in b) / len(b) if b else None,
                    "obs_freq": sum(y for _, y in b) / len(b) if b else None})
    return out


def brier_decomposition(ps: list[float], ys: list[float], n_bins: int = N_BINS) -> dict:
    """Murphy: Brier ~= reliability - resolution + uncertainty (binned; exact when p is constant per bin)."""
    n = len(ps)
    if n == 0:
        return {}
    ybar = sum(ys) / n
    rel = res = 0.0
    for b in reliability_bins(ps, ys, n_bins):
        if b["n"]:
            rel += b["n"] * (b["mean_p"] - b["obs_freq"]) ** 2
            res += b["n"] * (b["obs_freq"] - ybar) ** 2
    return {"reliability": rel / n, "resolution": res / n, "uncertainty": ybar * (1 - ybar), "bins": n_bins}


def _score_rows(policy: Policy, rows: list[dict]) -> dict:
    """Run scoring.score_cell and add bins/decomposition. Caller has already passed the seal gate."""
    shim = [dict(r) if "p_clim" in r else {**r, "p_clim": r["mid"]} for r in rows]
    out = scoring.score_cell(shim)
    if not policy.has_climatology or any("p_clim" not in r for r in rows):
        out.pop("brier_climatology", None)
        out.pop("delta_brier_vs_climatology", None)
        out["climatology"] = "unavailable"
    ps, ys = [r["p_yes"] for r in rows], [r["y"] for r in rows]
    out["reliability_bins"] = reliability_bins(ps, ys)
    out["brier_decomposition"] = brier_decomposition(ps, ys)
    return out


def _games_in_order(rows: list[dict]) -> list[str]:
    first: dict[str, str] = {}
    for r in sorted(rows, key=lambda r: r["ts_utc"]):
        first.setdefault(r["game_key"], r["ts_utc"])
    return sorted(first, key=lambda g: (first[g], g))


def eligible(policy: Policy, row: dict) -> bool:
    return policy.eligible_from is None or str(row.get("start_time_utc", ""))[:10] >= policy.eligible_from


def compute_scores(policy: Policy, band: str, settled_rows: list[dict], gg_open: dict[str, bool]) -> dict:
    """Counts + status always; score fields only if the policy allows. The gate is re-derived HERE
    from the policy and the counts, so a direct call on a sealed cell cannot leak a score."""
    scored = first_row_per_unit(settled_rows)
    elig = [r for r in scored if eligible(policy, r)]
    games = _games_in_order(elig)
    n_judged = len(games)
    status = cell_status(policy, band, n_judged, gg_open)
    out: dict[str, Any] = {"status": status, "status_text": status_text(policy, status, n_judged),
                           "judged_n": n_judged, "first_look_n": policy.looks[0] if policy.looks else None,
                           "scored_rows_available": len(elig)}
    if status in (STATUS_SEALED, STATUS_COUNTS):
        assert not (SCORE_KEYS & out.keys())
        return out
    look = max([k for k in policy.looks if k <= n_judged], default=n_judged)   # earliest `look` games only
    use = set(games[:look])
    out["scores"] = _score_rows(policy, [r for r in elig if r["game_key"] in use])
    out["scores_over_games"] = len(use)
    if status == STATUS_PRELIM:
        out["scores_label"] = f"PRELIMINARY (n={n_judged} of {policy.looks[0]})"
    return out


def first_row_per_unit(rows: list[dict]) -> list[dict]:
    rows = [r for r in rows if r.get("y") is not None and r.get("game_key")]
    return scoring.first_row_per_market(rows)


# ── projection ────────────────────────────────────────────────────────────────

def project_first_look(policy: Policy, settled_rows: list[dict], now: datetime, window_days: int = 14) -> dict:
    """Projected date judged n reaches the first look, at the trailing settle rate. Counts only."""
    if not policy.looks:
        return {"date": None, "note": "no pre-registered look"}
    elig = [r for r in first_row_per_unit(settled_rows) if eligible(policy, r)]
    games: dict[str, datetime] = {}
    for r in elig:
        t = _parse(r.get("start_time_utc"))
        if t:
            games[r["game_key"]] = min(t, games.get(r["game_key"], t))
    n, target = len(games), policy.looks[0]
    if n >= target:
        return {"date": None, "note": "first look reached", "settle_rate_per_day": None}
    if policy.eligible_from and now.strftime("%Y-%m-%d") < policy.eligible_from:
        return {"date": None, "note": f"judged games begin {policy.eligible_from}", "settle_rate_per_day": None}
    recent = [t for t in games.values() if t >= now - timedelta(days=window_days)]
    span = max(1.0, (now - min(recent)).total_seconds() / 86400) if recent else None
    rate = len(recent) / span if recent and span else 0.0
    if rate <= 0:
        return {"date": None, "note": "no games settled in the trailing window", "settle_rate_per_day": 0.0}
    return {"date": (now + timedelta(days=(target - n) / rate)).strftime("%Y-%m-%d"),
            "note": f"at {rate:.2f} settled games/day over the last {window_days}d", "settle_rate_per_day": rate}


def _parse(s: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


# ── I/O (read-only) ───────────────────────────────────────────────────────────

def _jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def gg_is_open(repo: Path, gg: str) -> bool:
    """True unless the live GG log's Status line for `gg` is readable and not OPEN."""
    try:
        txt = (repo / "03_DECISIONS/GOVERNANCE_GAP_LOG.md").read_text()
        m = re.search(rf"^### {re.escape(gg)}\b.*?\n\*\*Status:\*\*\s*([A-Z][A-Z \-]*)", txt, re.M | re.S)
        return True if not m else m.group(1).strip().startswith("OPEN")
    except Exception:
        return True


def discover_cells(repo: Path) -> list[dict]:
    cells = []
    for sport, ledger_dir, settled_dir in (
        ("NFL", repo / "exp_output/PREGAME_SHADOW", repo / "exp_output/PREGAME_SHADOW/settled"),
        ("MLB", repo / "exp_output/PREGAME_SHADOW", repo / "exp_output/PREGAME_SHADOW/settled"),
        ("NHL", repo / "data/shadow/nhl", repo / "data/shadow/nhl/settled"),
    ):
        for p in sorted(ledger_dir.glob(f"{sport}_*_T[123].jsonl")):
            stem = p.stem
            parts = stem.split("_")
            if sport != "NHL":
                parts = parts[1:]                          # NFL_NFL_X / MLB_MLB_X -> drop doubled sport
            cells.append({"cell": stem, "sport": sport, "band": parts[-1], "market_type": "_".join(parts[1:-1]),
                          "ledger": p, "settled": settled_dir / p.name})
    return cells


def load_settled(cell: dict) -> list[dict]:
    """Settled rows as scoring rows (y, game_key, ts_utc, quotes). NHL is joined to its ledger."""
    rows = _jsonl(cell["settled"])
    if cell["sport"] != "NHL":
        return rows
    led = {(r["run_id"], r["market_ticker"]): r for r in _jsonl(cell["ledger"])}
    out = []
    for s in rows:
        l = led.get((s.get("run_id"), s.get("market_ticker")))
        if l is None or s.get("outcome") is None:
            continue
        out.append({**l, "y": float(s["outcome"]), "game_key": l["event_ticker"]})
    return out


def evaluate_cell(cell: dict, repo: Path, now: datetime, gg_open: dict[str, bool]) -> dict:
    policy = policy_for(cell["sport"])
    ledger_rows = _jsonl(cell["ledger"])
    settled = load_settled(cell)
    n_games_settled = len({r["game_key"] for r in first_row_per_unit(settled)})
    res = compute_scores(policy, cell["band"], settled, gg_open)
    last = max((r["ts_utc"] for r in ledger_rows), default=None)
    res.update({"cell": cell["cell"], "sport": cell["sport"], "band": cell["band"],
                "market_type": cell["market_type"], "rows": len(ledger_rows), "settled_games": n_games_settled,
                "pct_to_first_look": (round(100 * min(res["judged_n"] / policy.looks[0], 1), 1) if policy.looks else None),
                "projection": project_first_look(policy, settled, now), "last_row": last,
                "prereg": policy.citation, "source": str(cell["ledger"].relative_to(repo))})
    return res


def run(repo: Path, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    gg = {"GG-401": gg_is_open(repo, "GG-401")}
    cells = [evaluate_cell(c, repo, now, gg) for c in discover_cells(repo)]
    return {"generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "gg_open": gg, "cells": cells,
            "historical": [{"family": k, "status": STATUS_HISTORICAL, "source": v} for k, v in HISTORICAL.items()],
            "summary": {"cells": len(cells),
                        "logging": sum(1 for c in cells if c["rows"] > 0),
                        "with_outcomes": sum(1 for c in cells if c["settled_games"] > 0),
                        "reached_look": sum(1 for c in cells if c["status"] == STATUS_JUDGED)}}

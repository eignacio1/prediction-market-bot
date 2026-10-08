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

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from prediction_market_bot.pregame_shadow import scoring, settled_schema

STATUS_SEALED, STATUS_PRELIM, STATUS_JUDGED = "SEALED", "PRELIMINARY", "JUDGED"
STATUS_HISTORICAL, STATUS_COUNTS = "HISTORICAL", "COUNTS ONLY"

# Every key a sealed cell must never carry.
SCORE_KEYS = frozenset({
    "brier_model", "brier_market", "brier_climatology", "logloss_model", "logloss_market",
    "delta_brier_vs_market", "delta_brier_vs_climatology", "reliability_bins", "brier_decomposition",
    "e_net_entry_expected_k007", "e_net_entry_expected_kmult", "e_net_realised_best_side", "scores",
    "verdict", "release",
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
    boot_b: int = scoring.BOOT_B                  # per pre-registration
    boot_seed: int = scoring.BOOT_SEED
    per_game_mean: bool = False                   # EXP-036: per-game score = mean over that game's strikes
    rules: str = "exp037"                         # decision-rule family: "exp037" (NFL/MLB) | "exp036" (NHL) | "exp038" (NBA)
    undefined: tuple[str, ...] = ()               # rules the pre-registration leaves open; the engine does NOT invent them


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
                  sealed_while_gg_open=(("T3", "GG-401"),), has_climatology=False,
                  boot_b=10_000, per_game_mean=True, rules="exp036"),
    # EXP-038 (W60.2). Differences from NFL, all from the text: looks 150 / 400, bootstrap seed 20261006 (B=2000),
    # climatology from the training seasons (settle writes p_clim), preseason rows never count (settled_schema.counts_toward_judged_n).
    "NBA": Policy("NBA", (150, 400), "sealed_until_look",
                  "EXP-038 NBA pre-registration (2026-10-06): first look judged n=150 settled regular-season games per "
                  "cell, second look 400; preseason excluded from judged n; seed 20261006",
                  boot_seed=20261006, rules="exp038",
                  undefined=("second look 'or 2027-01-31, whichever first': the date trigger names no rule for which games "
                             "are scored or at what n, so only the n=400 second look is released (GG-529)",
                             "'judged on whatever n they reach' (spread/total T1, sec. 1) conflicts with sec. 4 (no scoring "
                             "before 150): a cell below 150 stays sealed",
                             "ordering key for 'earliest N games': EXP-038 sec. 3 inherits EXP-037, whose addendum fixes "
                             "(start_time_utc, game_key); not restated in EXP-038 itself")),
}
# Cells with no pre-registration fall through to counts only.
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
    out = scoring.score_cell(shim, policy.boot_b, policy.boot_seed, policy.per_game_mean)
    if not policy.has_climatology or any("p_clim" not in r for r in rows):
        out.pop("brier_climatology", None)
        out.pop("delta_brier_vs_climatology", None)
        out["climatology"] = "unavailable"
    ps, ys = [r["p_yes"] for r in rows], [r["y"] for r in rows]
    out["reliability_bins"] = reliability_bins(ps, ys)
    out["brier_decomposition"] = brier_decomposition(ps, ys)
    return out


def _games_in_order(rows: list[dict]) -> list[str]:
    """Deterministic order of settled games: (scheduled start, game_key). Falls back to the game's first
    ledger timestamp only for a game with no start time. Ties break on game_key, never on arrival order."""
    first: dict[str, str] = {}
    for r in rows:
        k = str(r.get("start_time_utc") or r["ts_utc"])
        if r["game_key"] not in first or k < first[r["game_key"]]:
            first[r["game_key"]] = k
    return sorted(first, key=lambda g: (first[g], g))


def eligible(policy: Policy, row: dict) -> bool:
    if not settled_schema.counts_toward_judged_n(row):
        return False
    return policy.eligible_from is None or str(row.get("start_time_utc", ""))[:10] >= policy.eligible_from


def verdict(policy: Policy, status: str, scores: dict, n_judged: int) -> dict:
    """The pre-registered decision, from the pre-registered fields only. Emitted only on a released look
    (status JUDGED); a PRELIMINARY or sealed cell has no verdict. Never changes a cell's registry status."""
    if status != STATUS_JUDGED or not scores:
        return {}
    dm = scores["delta_brier_vs_market"]
    dc = scores.get("delta_brier_vs_climatology")
    lo, hi = dm["ci95"]
    e7, ek = scores["e_net_entry_expected_k007"]["mean"], scores["e_net_entry_expected_kmult"]["mean"]
    out: dict[str, Any] = {"n": n_judged, "delta_brier_vs_market": dm,
                           "delta_brier_vs_climatology": dc if dc is not None else "unavailable",
                           "e_net_entry_k007": e7, "e_net_entry_kmult": ek}
    if policy.rules == "exp036":
        clim_dead = dc is not None and n_judged >= 500 and dc["ci95"][1] <= 0
        if clim_dead:
            v, why = "RULED_OUT", "(a) n>=500 and the CI of delta vs climatology has upper bound <= 0"
        elif n_judged >= 2500 and hi < 0 and e7 < 0 and ek < 0:
            v, why = "RULED_OUT", "(b) n>=2500, delta vs market CI upper bound < 0 and E_net < 0 under both fees"
        elif n_judged >= 2500 and lo > 0 and e7 > 0 and ek > 0:
            v, why = "CANDIDATE-PENDING-CAPACITY", "n>=2500, delta vs market CI lower bound > 0, E_net > 0 under both fees"
        else:
            v, why = "SHADOW-continue", "everything else"
    else:
        if policy.rules == "exp038" and hi >= 0 and lo <= 0 and n_judged >= policy.looks[-1]:
            v, why = "UNRESOLVED", "EXP-038 sec. 5.2: CI still spans zero after the second look; never decided by judgement"
        elif hi < 0:
            v, why = "RULED_OUT", "delta vs market < 0 with the CI upper bound < 0"
        elif lo > 0 and e7 > 0 and ek > 0:
            v, why = "CANDIDATE-PENDING-CAPACITY", "delta vs market CI lower bound > 0 and E_net > 0 under both fees"
        elif lo > 0:
            v, why = "SHADOW", "delta vs market CI excludes zero but E_net <= 0 under a fee candidate"
        else:
            v, why = "SHADOW", "CI spans zero"
    out.update({"verdict": v, "rule": why})
    if dc is not None and dc["mean"] <= 0:
        out["model_failure_vs_climatology"] = True         # reported separately; not a decision rule
    return out


def manifest_digest(look: int, games: list[str]) -> str:
    return hashlib.sha256(json.dumps({"look": look, "games": sorted(games)}).encode()).hexdigest()


def compute_scores(policy: Policy, band: str, settled_rows: list[dict], gg_open: dict[str, bool],
                   frozen: dict | None = None) -> dict:
    """Counts + status always; score fields only if the policy allows. The gate is re-derived HERE
    from the policy and the counts, so a direct call on a sealed cell cannot leak a score.

    `frozen` = a persisted release manifest {"look": k, "games": [...]}. A look scores exactly the games
    named in it, forever: later or late-settling games never change a released look."""
    scored = first_row_per_unit(settled_rows)
    elig = [r for r in scored if eligible(policy, r)]
    games = _games_in_order(elig)
    n_judged = len(games)
    status = cell_status(policy, band, n_judged, gg_open)
    out: dict[str, Any] = {"status": status, "status_text": status_text(policy, status, n_judged),
                           "judged_n": n_judged, "first_look_n": policy.looks[0] if policy.looks else None,
                           "scored_rows_available": len(elig)}
    if policy.undefined:
        out["undefined_rules"] = list(policy.undefined)
    if status in (STATUS_SEALED, STATUS_COUNTS):
        assert not (SCORE_KEYS & out.keys())
        return out
    look = max([k for k in policy.looks if k <= n_judged], default=n_judged)   # earliest `look` games only
    if frozen and frozen.get("look") == look and set(frozen["games"]) <= set(games):
        use_games = list(frozen["games"])
    else:
        use_games = games[:look]
    use = set(use_games)
    out["scores"] = _score_rows(policy, [r for r in elig if r["game_key"] in use])
    out["scores_over_games"] = len(use)
    if status == STATUS_PRELIM:
        out["scores_label"] = f"PRELIMINARY (n={n_judged} of {policy.looks[0]})"
    else:
        out["release"] = {"look": look, "games": sorted(use), "digest": manifest_digest(look, list(use)),
                          "frozen": bool(frozen and frozen.get("look") == look)}
        out["verdict"] = verdict(policy, status, out["scores"], len(use))
    return out


def first_row_per_unit(rows: list[dict]) -> list[dict]:
    rows = [r for r in rows if r.get("y") is not None and r.get("game_key")]
    return scoring.first_row_per_market(rows)


# ── projection ────────────────────────────────────────────────────────────────
# W59.2 Part A. The projection walks the sport's REAL remaining schedule (games per day, so per week)
# and multiplies by the cell's observed coverage (settled games / scheduled games since the cell began
# logging). A trailing-day rate extrapolated linearly is wrong for NFL (one slate a week, a bye-week
# dip, season ends at week 18) and for any cell that cannot reach its look inside the published season.
SETTLE_LAG_DAYS = 1


def _day(s: Any) -> str | None:
    t = _parse(s)
    return t.strftime("%Y-%m-%d") if t else (str(s)[:10] if s else None)


def load_schedule(repo: Path, sport: str) -> list[str] | None:
    """Dates (YYYY-MM-DD, one entry per scheduled regular-season game) from the sport's published
    schedule. None = no schedule published/available (never guessed)."""
    try:
        if sport == "NFL":
            d = json.loads((repo / "data/schedules/nfl_2026.json").read_text())
            return sorted(g["gameday"] for g in d["games"] if g.get("game_type", "REG") == "REG")
        if sport == "NBA":
            return None        # no NBA regular-season schedule is checked in; never guessed (cells show counts)
        if sport == "NHL":
            files = sorted((repo / "data/raw/nhl/schedule").glob("*.json"))
            games = json.loads(files[-1].read_text())["games"] if files else []
            out = [_day(g["start_time_utc"]) for g in games if g.get("game_type") == 2 and g.get("start_time_utc")]
            return sorted(x for x in out if x) or None
    except Exception:
        return None
    return None        # MLB 2027: schedule not yet published


def _project_one(target: int, n: int, dates: list[str], coverage: float, today: str) -> dict:
    need = target - n
    future = [d for d in dates if d >= today]
    per_week: dict[str, int] = {}
    for d in future:
        wk = (datetime.strptime(d, "%Y-%m-%d").date())
        k = (wk - timedelta(days=wk.weekday())).isoformat()
        per_week[k] = per_week.get(k, 0) + 1
    expected_total = len(future) * coverage
    if need <= 0:
        return {"date": None, "reached": True}
    if expected_total < need:
        return {"date": None, "reachable": False, "need": need,
                "expected_additional": round(expected_total, 1), "games_remaining_on_schedule": len(future)}
    cum = 0.0
    for d in future:
        cum += coverage
        if cum >= need:
            land = (datetime.strptime(d, "%Y-%m-%d") + timedelta(days=SETTLE_LAG_DAYS)).strftime("%Y-%m-%d")
            return {"date": land, "reachable": True, "need": need, "games_remaining_on_schedule": len(future)}
    return {"date": None, "reachable": False, "need": need}


def project_first_look(policy: Policy, settled_rows: list[dict], now: datetime, schedule: list[str] | None = None,
                       cell_first_ts: str | None = None) -> dict:
    """Projected date judged n reaches the first look, from the real remaining schedule x cell coverage.
    Counts only. `schedule` = one date per scheduled game (None = unavailable -> no date, said plainly)."""
    if not policy.looks:
        return {"date": None, "note": "no pre-registered look"}
    elig = [r for r in first_row_per_unit(settled_rows) if eligible(policy, r)]
    n, target = len({r["game_key"] for r in elig}), policy.looks[0]
    today = now.strftime("%Y-%m-%d")
    if n >= target:
        return {"date": None, "note": "first look reached", "method": "schedule"}
    if policy.eligible_from and today < policy.eligible_from:
        return {"date": None, "note": f"judged games begin {policy.eligible_from}; schedule not yet published",
                "method": "schedule"}
    if not schedule:
        return {"date": None, "note": "no published schedule available for this sport", "method": "schedule"}
    start = _day(cell_first_ts) or today
    cutoff = (now - timedelta(days=SETTLE_LAG_DAYS)).strftime("%Y-%m-%d")
    past = sum(1 for d in schedule if start <= d <= cutoff)
    if past < 5:
        return {"date": None, "note": f"coverage unmeasurable yet ({past} scheduled games since the cell began logging)",
                "method": "schedule"}
    coverage = min(1.0, n / past)
    if coverage <= 0:
        return {"date": None, "note": f"no settled games out of {past} scheduled since logging began", "method": "schedule",
                "coverage": 0.0}
    res = _project_one(target, n, schedule, coverage, today)
    res.update({"method": "schedule", "coverage": round(coverage, 3), "coverage_basis": f"{n} settled of {past} scheduled since {start}"})
    if res.get("date"):
        res["note"] = (f"{res['games_remaining_on_schedule']} games left on schedule x {coverage:.0%} coverage; "
                       f"needs {res['need']} more")
    elif res.get("reachable") is False:
        res["note"] = (f"not reachable on the published schedule: need {res['need']} more, expect "
                       f"{res.get('expected_additional', 0)} from {res.get('games_remaining_on_schedule', 0)} games left")
    return res


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


# EXP-038 sec. 1: the 12 NBA cells are listed from day one so counts show before the first regular-season row.
# Only the judged dir is read; PREGAME_SHADOW_PRESEASON is never discovered.
EXPECTED_CELLS: dict[str, tuple[str, ...]] = {
    "NBA": tuple(f"NBA_NBA_{mt}_{b}" for mt in ("MONEYLINE", "SPREAD", "GAME_TOTAL", "TEAM_TOTAL") for b in ("T1", "T2", "T3")),
}


def discover_cells(repo: Path) -> list[dict]:
    cells = []
    for sport, ledger_dir, settled_dir in (
        ("NFL", repo / "exp_output/PREGAME_SHADOW", repo / "exp_output/PREGAME_SHADOW/settled"),
        ("MLB", repo / "exp_output/PREGAME_SHADOW", repo / "exp_output/PREGAME_SHADOW/settled"),
        ("NHL", repo / "data/shadow/nhl", repo / "data/shadow/nhl/settled"),
        ("NBA", repo / "exp_output/PREGAME_SHADOW", repo / "exp_output/PREGAME_SHADOW/settled"),
    ):
        paths = {p.name: p for p in ledger_dir.glob(f"{sport}_*_T[123].jsonl")}
        for name in EXPECTED_CELLS.get(sport, ()):
            paths.setdefault(f"{name}.jsonl", ledger_dir / f"{name}.jsonl")
        for _, p in sorted(paths.items()):
            stem = p.stem
            parts = stem.split("_")
            if sport != "NHL":
                parts = parts[1:]                          # NFL_NFL_X / MLB_MLB_X -> drop doubled sport
            cells.append({"cell": stem, "sport": sport, "band": parts[-1], "market_type": "_".join(parts[1:-1]),
                          "ledger": p, "settled": settled_dir / p.name})
    return cells


def load_settled(cell: dict) -> list[dict]:
    """Settled rows as scoring rows, normalised to the one schema (settled_schema.normalize). NHL settled rows
    carry no quotes or game id of their own, so they are joined to their ledger row on (run_id, market_ticker)."""
    rows = _jsonl(cell["settled"])
    led = ({(r["run_id"], r["market_ticker"]): r for r in _jsonl(cell["ledger"])} if cell["sport"] == "NHL" else None)
    out = []
    for s in rows:
        l = led.get((s.get("run_id"), s.get("market_ticker"))) if led is not None else None
        if led is not None and l is None:
            continue
        n = settled_schema.normalize(s, l)
        if n is not None:
            out.append(n)
    return out


MANIFEST_DIR = "exp_output/CALIBRATION/release_manifests"


def manifest_path(repo: Path, cell: dict, look: int) -> Path:
    return repo / MANIFEST_DIR / f"{cell['cell']}.look{look}.json"


def load_manifest(repo: Path, cell: dict) -> dict | None:
    """The persisted release for this cell's most recent look, or None. Corrupt files read as absent
    here and are caught by the digest check below -- never silently trusted."""
    best = None
    for p in sorted((repo / MANIFEST_DIR).glob(f"{cell['cell']}.look*.json")) if (repo / MANIFEST_DIR).exists() else []:
        try:
            m = json.loads(p.read_text())
        except ValueError:
            continue
        if m.get("digest") == manifest_digest(m.get("look"), m.get("games", [])):
            best = m if best is None or m["look"] > best["look"] else best
    return best


def persist_release(repo: Path, cell: dict, release: dict, now: datetime) -> Path | None:
    """Write-once. An existing manifest for (cell, look) is never overwritten."""
    p = manifest_path(repo, cell, release["look"])
    if p.exists():
        return None
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({**release, "cell": cell["cell"], "released_at": now.strftime("%Y-%m-%dT%H:%M:%SZ")}, indent=1))
    return p


def evaluate_cell(cell: dict, repo: Path, now: datetime, gg_open: dict[str, bool], persist: bool = False) -> dict:
    policy = policy_for(cell["sport"])
    ledger_rows = _jsonl(cell["ledger"])
    settled = load_settled(cell)
    n_games_settled = len({r["game_key"] for r in first_row_per_unit(settled) if settled_schema.counts_toward_judged_n(r)})
    res = compute_scores(policy, cell["band"], settled, gg_open, load_manifest(repo, cell))
    if persist and res.get("release") and not res["release"]["frozen"]:
        persist_release(repo, cell, res["release"], now)
    last = max((r["ts_utc"] for r in ledger_rows), default=None)
    res.update({"cell": cell["cell"], "sport": cell["sport"], "band": cell["band"],
                "market_type": cell["market_type"], "rows": len(ledger_rows), "settled_games": n_games_settled,
                "pct_to_first_look": (round(100 * min(res["judged_n"] / policy.looks[0], 1), 1) if policy.looks else None),
                "projection": project_first_look(policy, settled, now, load_schedule(repo, cell["sport"]), min((r["ts_utc"] for r in ledger_rows), default=None)), "last_row": last,
                "prereg": policy.citation, "source": str(cell["ledger"].relative_to(repo))})
    return res


def run(repo: Path, now: datetime | None = None, persist: bool = False) -> dict:
    now = now or datetime.now(timezone.utc)
    gg = {"GG-401": gg_is_open(repo, "GG-401")}
    cells = [evaluate_cell(c, repo, now, gg, persist) for c in discover_cells(repo)]
    return {"generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "gg_open": gg, "cells": cells,
            "historical": [{"family": k, "status": STATUS_HISTORICAL, "source": v} for k, v in HISTORICAL.items()],
            "summary": {"cells": len(cells),
                        "logging": sum(1 for c in cells if c["rows"] > 0),
                        "with_outcomes": sum(1 for c in cells if c["settled_games"] > 0),
                        "reached_look": sum(1 for c in cells if c["status"] == STATUS_JUDGED)}}

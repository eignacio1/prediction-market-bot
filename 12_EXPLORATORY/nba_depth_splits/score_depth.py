"""W118.2 Part B -- score the five PREREG'd NBA depth splits per leaf per arm on settled 2026-27 shadow rows (EXP-NBADEPTH-001).

Run: PYTHONPATH=src python3 12_EXPLORATORY/nba_depth_splits/score_depth.py <settled_dir> <archive_checkout> [--rebuild]
Rule is PREREG.md section 3 + A1, frozen before any outcome was read: per (split filter x leaf x family x band) the earliest 70% of
games (rr.split_games, by game) pick the arm (RIDE / FADE / MODEL_FADE / MOMENTUM, best fit mean net per contract after fee, else
NO_BET); the latest 30% score it with a game-clustered bootstrap; BH across every test (q=0.10). KEPT = not thin, arm != NO_BET,
held-out games >= MIN_TEST_GAMES, held-out mean net > 0. Shadow rows are paper rows, not fills (GG-527). Unknown leaves never scored.
Writes results.json and nba_depth_v2.candidate.json under 12_EXPLORATORY/ only (fence); the leaf map is copied by hand in Part C.
Applies when: refreshing the depth-split scores as shadow rows accumulate.
"""
from __future__ import annotations

import bisect
import glob
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.archive_intake.archive import Archive, _read_jsonl  # noqa: E402
from prediction_market_bot.decision_trees.filters import nba_depth as nd  # noqa: E402
from prediction_market_bot.quant import retro_route as rr  # noqa: E402

ARMS = ("RIDE", "FADE", "MODEL_FADE", "MOMENTUM")
ROW_SEASON = 2026  # 2026-27
FAMS = {"pace_prod@total": ("GAME_TOTAL", "TEAM_TOTAL"), "net_rating@side": ("SPREAD", "MONEYLINE"),
        "shotzone_matchup@total": ("GAME_TOTAL",), "shotzone_matchup@side": ("SPREAD", "MONEYLINE"),
        "lineup_status": ("GAME_TOTAL", "TEAM_TOTAL", "SPREAD", "MONEYLINE"), "home_road_gap@side": ("SPREAD", "MONEYLINE"),
        "ref_crew@total": ("GAME_TOTAL", "TEAM_TOTAL")}
SPLIT_OF = {"pace_prod@total": "S1", "net_rating@side": "S1", "shotzone_matchup@total": "S2", "shotzone_matchup@side": "S2",
            "lineup_status": "S3", "home_road_gap@side": "S4", "ref_crew@total": "S5"}


def load_rows(settled: str) -> list:
    rows = []
    for p in sorted(glob.glob(f"{settled}/NBA_*.jsonl")):
        with open(p) as fh:
            rows += [json.loads(l) for l in fh if l.strip()]
    rows = rr.dedupe(rows)
    rr.add_moves(rows)
    return rows


def _t(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00"))


class Snapshots:
    """Lineup and referee snapshots indexed by game_key; lookups are 'latest at or before ts' only."""

    def __init__(self, arch: Archive, name2abbr: dict):
        self.lineup: dict = defaultdict(list)   # game_key -> [(status_at, rec)] sorted
        self.refs: dict = defaultdict(list)     # game_key -> [(snapshot_at, rec)]
        self.rot: dict = defaultdict(list)      # team -> [(status_at, set(names >= 20 min))]
        for p in arch.snapshot_files("nba", "lineups"):
            for r in _read_jsonl(p):
                gid = r["game_id"]  # AWAY@HOME-YYYY-MM-DD
                matchup, date = gid[:-11], gid[-10:]
                key = f"{date}:{matchup}"
                at = _t(r["status_at_utc"])
                self.lineup[key].append((at, r))
                away, home = matchup.split("@")
                for side, ab in (("away", away), ("home", home)):
                    names = {d["name"] for d in r.get(f"{side}_starters_detail", []) if (d.get("min") or 0) >= 20}
                    self.rot[ab].append((at, names))
        for p in arch.snapshot_files("nba", "refs"):
            for r in _read_jsonl(p):
                a, h = name2abbr.get(r["away_team"]), name2abbr.get(r["home_team"])
                if not a or not h:
                    continue
                self.refs[f"{r['game_id'][:10]}:{a}@{h}"].append((_t(r["snapshot_at_utc"]), r))
        for d in (self.lineup, self.refs, self.rot):
            for k in d:
                d[k].sort(key=lambda x: x[0])

    @staticmethod
    def _latest(lst, ts):
        if not lst:
            return None
        i = bisect.bisect_right([x[0] for x in lst], ts)
        return lst[i - 1] if i else None

    def lineup_at(self, key, ts):
        return self._latest(self.lineup.get(key), ts)

    def refs_at(self, key, ts):
        return self._latest(self.refs.get(key), ts)

    def rotation_at(self, team, ts):
        out = set()
        for at, names in self.rot.get(team, []):
            if at <= ts:
                out |= names
        return out


def tag_rows(rows: list, prof: dict, snaps: Snapshots) -> None:
    cache: dict = {}
    for r in rows:
        date, m = r["game_key"].split(":")
        away, home = m.split("@")
        ts = _t(r["ts_utc"])
        key = r["game_key"]
        ln = snaps.lineup_at(key, ts)
        rf = snaps.refs_at(key, ts)
        ck = (home, away, ln[0] if ln else None, rf[0] if rf else None)
        if ck not in cache:
            snap = ln[1] if ln else None
            crew = [rf[1][k] for k in ("crew_chief", "referee", "umpire") if rf and rf[1].get(k)] if rf else []
            rot = {"away": snaps.rotation_at(away, ts), "home": snaps.rotation_at(home, ts)} if snap else {}
            cache[ck] = nd.depth_filters(home, away, prof, row_season=ROW_SEASON, lineup_snap=snap, rotation=rot, crew=crew,
                                         refs_snap_at=rf[1]["snapshot_at_utc"] if rf else None, ts_utc=r["ts_utc"])
        r["_depth"] = cache[ck]


def score(rows: list) -> tuple:
    fit_g, test_g = rr.split_games(rows)
    res, pv = [], {}
    for filt, fams in FAMS.items():
        for fam in fams:
            sub = [r for r in rows if r["market_type"].endswith(fam)]
            by = defaultdict(lambda: ([], []))
            for r in sub:
                by[(r["_depth"][filt], r["band"])][0 if rr.game_id(r) in fit_g else 1].append(r)
            fam_test = defaultdict(list)
            for r in sub:
                if rr.game_id(r) in test_g:
                    fam_test[r["band"]].append(r)
            for (leaf, band), (f, t) in sorted(by.items()):
                fg = len({rr.game_id(r) for r in f})
                rec = {"split": SPLIT_OF[filt], "filter": filt, "family": fam, "band": band, "leaf": leaf, "fit_rows": len(f),
                       "fit_games": fg, "arm": "NO_BET", "thin": False, "test_rows": len(t), "test_games": len({rr.game_id(r) for r in t})}
                if leaf == "unknown" or len(f) < rr.MIN_FIT_ROWS or fg < rr.MIN_FIT_GAMES:
                    rec["thin"] = True
                else:
                    tab = {}
                    for a in ARMS:
                        v = [x for x in (rr.arm_nets(r)[a] for r in f) if x is not None]
                        if len(v) >= rr.MIN_FIT_ROWS:
                            tab[a] = sum(v) / len(v)
                    rec["fit"] = tab
                    best = max(tab.items(), key=lambda kv: kv[1], default=None)
                    if best and best[1] > 0:
                        rec["arm"] = best[0]
                if rec["arm"] != "NO_BET":
                    g = defaultdict(list)
                    for r in t:
                        x = rr.arm_nets(r)[rec["arm"]]
                        if x is not None:
                            g[rr.game_id(r)].append(x)
                    if len(g) >= rr.MIN_TEST_GAMES:
                        m, lo, hi, p = rr.boot_ci(g)
                        rec.update(test_mean=m, test_lo=lo, test_hi=hi, test_p=p, test_n=sum(map(len, g.values())), test_n_games=len(g))
                        pv[(filt, fam, band, leaf)] = p
                        ref = defaultdict(list)
                        for r in fam_test[band]:
                            x = rr.arm_nets(r)[rec["arm"]]
                            if x is not None:
                                ref[rr.game_id(r)].append(x)
                        if len(ref) >= rr.MIN_TEST_GAMES:
                            rm = rr.boot_ci(ref)
                            rec["family_same_arm_mean"], rec["family_same_arm_lo"], rec["family_same_arm_hi"] = rm[0], rm[1], rm[2]
                res.append(rec)
    keep = rr.bh_reject(pv) if pv else set()
    for rec in res:
        rec["bh"] = (rec["filter"], rec["family"], rec["band"], rec["leaf"]) in keep
        rec["kept"] = bool(not rec["thin"] and rec["arm"] != "NO_BET" and rec.get("test_n_games", 0) >= rr.MIN_TEST_GAMES
                           and rec.get("test_mean", -1) > 0)
        rec["draft"] = bool(rec["kept"] and rec["bh"] and rec.get("test_lo", -1) > 0 and rec.get("test_n_games", 0) >= rr.DRAFT_TEST_GAMES)
    return res, fit_g, test_g


def coverage(rows: list) -> dict:
    out = {}
    for filt, fams in FAMS.items():
        for fam in fams:
            sub = [r for r in rows if r["market_type"].endswith(fam)]
            j = sum(1 for r in sub if r["_depth"][filt] != "unknown")
            out[f"{filt}|{fam}"] = {"joined": j, "total": len(sub), "pct": round(100 * j / max(1, len(sub)), 1)}
    return out


def main():
    settled, ckout = sys.argv[1], sys.argv[2]
    arch = Archive(ckout, nd.ARCHIVE_SHA)
    cache = HERE / "profiles.json"
    if "--rebuild" in sys.argv or not cache.exists():
        safe_out(cache).write_text(json.dumps(nd.build_profiles(arch), indent=1))
    prof = json.loads(cache.read_text())
    rows = load_rows(settled)
    tag_rows(rows, prof, Snapshots(arch, prof["name2abbr"]))
    res, fit_g, test_g = score(rows)
    per_split = {}
    for s in sorted(set(SPLIT_OF.values())):
        rs = [r for r in res if r["split"] == s]
        per_split[s] = {"leaves": len(rs), "thin": sum(r["thin"] for r in rs), "routed": sum(r["arm"] != "NO_BET" for r in rs),
                        "reportable": sum("test_mean" in r for r in rs), "kept": sum(r["kept"] for r in rs),
                        "bh": sum(r["bh"] for r in rs), "draft": sum(r["draft"] for r in rs)}
    summ = {"archive_sha": nd.ARCHIVE_SHA, "rows": len(rows), "fit_games": len(fit_g), "test_games": len(test_g), "per_split": per_split,
            "coverage": coverage(rows)}
    safe_out(HERE / "results.json").write_text(json.dumps({"summary": summ, "leaves": res}, indent=1))
    splits = []
    for r in res:
        if r["thin"] and r["leaf"] == "unknown":
            continue
        why = ("thin_fit" if r["thin"] else "no_arm_positive_in_fit" if r["arm"] == "NO_BET" else
               "held_out_games_below_min" if "test_mean" not in r else "held_out_net_not_positive" if not r["kept"] else "kept")
        splits.append({"arm": r["arm"], "bh": r["bh"], "filter": r["filter"], "kept": r["kept"], "leaf": r["leaf"], "series": r["family"],
                       "band": r["band"], "split": r["split"], "fit_games": r["fit_games"], "test_games": r["test_games"],
                       "test_mean": r.get("test_mean"), "why": why, "source": "118.2 results.json", "sport": "NBA"})
    closed = [{"exp_id": f"EXP-NBADEPTH-001-{s}", "status": "hypothesis closed (parked for R&D)",
               "reason": "no leaf kept; " + ("all leaves thin: snapshots begin 2026-11-10, join coverage in results.json" if per_split[s]["reportable"] == 0 else "no leaf positive held out")}
              for s, v in per_split.items() if v["kept"] == 0]
    safe_out(HERE / "nba_depth_v2.candidate.json").write_text(json.dumps(
        {"version": "nba_depth_v2", "archive_sha": nd.ARCHIVE_SHA, "n": len(splits), "n_kept": sum(s["kept"] for s in splits),
         "rule": "kept = not thin, arm != NO_BET, held-out games >= min, held-out mean net > 0", "min_held_games": rr.MIN_TEST_GAMES,
         "splits": splits, "closed_hypotheses": closed}, indent=1, sort_keys=True))
    print(json.dumps({k: v for k, v in summ.items() if k != "coverage"}, indent=1))
    print(json.dumps(summ["coverage"], indent=1))


if __name__ == "__main__":
    main()

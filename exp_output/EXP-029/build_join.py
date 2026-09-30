"""EXP-029 D2: join extended feature matrix to KXMLBHIT price archive on REAL tickers.

No model is scored here. Output: joined.jsonl (one row per surviving ticker) and
join_yield.json (rows attempted / kept / dropped by reason, in rows AND games).
Run from repo root (worktree) with the shared-tree data paths in env SHARED.
"""
import collections, glob, json, os, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from prediction_market_bot.c5_execution.market_type_registry import derive_game_date
from prediction_market_bot.c3_forecasting import pregame_hits_model as M

SHARED = Path(os.environ["SHARED"])
OUT = Path("exp_output/EXP-029")
WIN = ("2026-08-01", "2026-09-30")
SNAP_MAX_AGE_MIN = 60           # latest pre-first-pitch snapshot must be within 60 min
EDT = timedelta(hours=4)        # ticker HHMM is US Eastern; Aug-Oct 2026 = EDT (UTC-4)

drops = collections.OrderedDict()
def drop(reason, ticker, gid=None):
    drops.setdefault(reason, []).append((ticker, gid))

# --- archive: all KXMLBHIT tickers in window, keep every snapshot
snaps = collections.defaultdict(list)
for f in sorted(glob.glob(str(SHARED / "exp_output/PRICE_ARCHIVE/prices_2026-0[89]*.jsonl"))):
    for l in open(f):
        if '"KXMLBHIT-' not in l:
            continue
        r = json.loads(l)
        if r.get("series_ticker") != "KXMLBHIT":
            continue
        snaps[r["ticker"]].append((r["run_ts"], float(r["yes_bid"]), float(r["yes_ask"])))

# --- bridge: ticker -> player_id from live-pipeline artifacts (never inferred)
bridge = collections.defaultdict(set)
for l in open(OUT / "ticker_bridge_cyclelog.jsonl"):
    r = json.loads(l)
    bridge[r["ticker"]].add(int(r["player_id"]))
for l in open(SHARED / "logs/t4_mlb_outcome_store.jsonl"):
    r = json.loads(l)
    bridge[r["ticker"]].add(int(r["player_id"]))
outstore = {}
for l in open(SHARED / "logs/t4_mlb_outcome_store.jsonl"):
    r = json.loads(l); outstore[r["ticker"]] = r

forbidden = set(json.load(open("scripts/t4_forbidden_cohort_manifest.json"))["tickers"])

# --- matrix (frozen loader, population filter ab>=1 & ba_l10 notna); keep full raw for reasons
raw = pd.read_csv("exp_output/MLB/mlb_feature_matrix.csv", low_memory=False)
raw["game_date"] = raw["game_date"].astype(str)
raw_idx = collections.defaultdict(list)
for i, (pid, gd) in enumerate(zip(raw.player_id, raw.game_date)):
    raw_idx[(int(pid), gd)].append(i)
pop = M.load_population(Path("exp_output/MLB/mlb_feature_matrix.csv"), verify_sha=False)
pop_idx = {(int(p), g, int(gid)): i for i, (p, g, gid) in enumerate(zip(pop.player_id, pop.game_date, pop.game_id))}

kept = []
attempted = 0
for t in sorted(snaps):
    gd = derive_game_date(t)
    if not (WIN[0] <= gd <= WIN[1]):
        continue
    attempted += 1
    thr = int(t.rsplit("-", 1)[1])
    if thr != 1:
        drop("threshold != 1 (model target is P(h>=1))", t); continue
    if t in forbidden:
        drop("in T-577 forbidden-cohort manifest (harness refuses)", t); continue
    pids = bridge.get(t)
    if not pids:
        drop("no authoritative ticker->player_id mapping (not evaluated by T4 / not in outcome store)", t); continue
    if len(pids) > 1:
        drop("bridge sources disagree on player_id", t); continue
    pid = next(iter(pids))
    rows = raw_idx.get((pid, gd), [])
    if not rows:
        drop("no matrix row for (player_id, ticker date)", t); continue
    if len(rows) > 1:
        drop("multiple matrix rows same player/date (doubleheader or dup) - not disambiguated", t); continue
    rr = raw.iloc[rows[0]]
    gid = int(rr.game_id)
    if rr.ab < 1:
        drop("player did not bat (ab==0) - outside frozen population", t, gid); continue
    if pd.isna(rr.ba_l10):
        drop("ba_l10 null - outside frozen population", t, gid); continue
    key = (pid, gd, gid)
    if key not in pop_idx:
        drop("removed by frozen loader (duplicate player/game)", t, gid); continue
    # pre-game snapshot rule
    hhmm = t.split("-")[1][7:11]
    start_utc = datetime.strptime(gd + hhmm, "%Y-%m-%d%H%M").replace(tzinfo=timezone.utc) + EDT
    best = None
    for ts, bid, ask in snaps[t]:
        dts = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if dts < start_utc and (best is None or dts > best[0]):
            best = (dts, bid, ask)
    if best is None:
        drop("no snapshot before scheduled first pitch", t, gid); continue
    age = (start_utc - best[0]).total_seconds() / 60
    if age > SNAP_MAX_AGE_MIN:
        drop(f"latest pre-first-pitch snapshot older than {SNAP_MAX_AGE_MIN} min", t, gid); continue
    _, bid, ask = best
    if not (bid > 0 and ask > 0 and ask < 1.0 and ask >= bid):
        drop("pre-first-pitch quote one-sided/empty (bid<=0 or ask not in (0,1))", t, gid); continue
    p = (bid + ask) / 2
    y = int(rr.h >= 1)
    x = {"ticker": t, "game_id": gid, "game_date": gd, "player_id": pid, "p_incumbent": round(p, 6),
         "outcome": y, "resolution_source": "boxscore_rederived", "cohort_band": "PREGAME-NA",
         "logic_epoch": 0, "snap_age_min": round(age, 1), "bid": bid, "ask": ask,
         "pop_idx": pop_idx[key]}
    o = outstore.get(t)
    if o is not None and o.get("actual_hits") is not None:
        x["outstore_actual_hits"] = o["actual_hits"]
    kept.append(x)

Path(OUT / "joined.jsonl").write_text("\n".join(json.dumps(k) for k in kept) + "\n")
games_kept = len({k["game_id"] for k in kept})
tot_dates = len({derive_game_date(t) for t in snaps if WIN[0] <= derive_game_date(t) <= WIN[1]})
y = {
    "window": WIN, "rows_attempted": attempted,
    "rows_kept": len(kept), "games_kept": games_kept, "dates_kept": len({k["game_date"] for k in kept}),
    "dates_in_archive_window": tot_dates,
    "dropped_by_reason": {r: {"rows": len(v), "games": len({g for _, g in v if g is not None}) or None}
                          for r, v in drops.items()},
}
mism = [(k["ticker"], k["outcome"], k["outstore_actual_hits"]) for k in kept
        if "outstore_actual_hits" in k and int(k["outstore_actual_hits"] >= 1) != k["outcome"]]
y["outcome_crosscheck_vs_T421_store"] = {"n_compared": sum("outstore_actual_hits" in k for k in kept), "n_disagree": len(mism)}
Path(OUT / "join_yield.json").write_text(json.dumps(y, indent=1))
print(json.dumps(y, indent=1))

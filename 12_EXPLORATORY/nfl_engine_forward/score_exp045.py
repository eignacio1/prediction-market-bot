"""EXP-045 scoring script: reads the price archive, prices board v2 at each post-freeze snapshot, settles, writes the look.

  python3 score_exp045.py --freeze 2026-10-29T03:00:00Z --out look.json [--results results.json] [--fetch]
  python3 score_exp045.py --replay --out replay.json     # in-sample: every archived game with a schedule score

Read-only on the archive and the schedule; writes only inside 12_EXPLORATORY/ (fence). Results: a JSON
{event_suffix: [home_pts, away_pts]}, or --fetch to read finals from the public ESPN scoreboard.
"""
import argparse, glob, json, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out
from prediction_market_bot.nfl_engine import forward_test as ft
from prediction_market_bot.nfl_engine.board_v2 import build_library

MDE = 0.02       # smallest true net P&L per contract worth detecting
FREEZE_DEFAULT = "2026-10-29T03:00:00Z"


def read_archive(archive_dir):
    for f in sorted(glob.glob(str(Path(archive_dir) / "prices_*.jsonl"))):
        with open(f) as fh:
            for line in fh:
                if '"KXNFL' in line:
                    yield json.loads(line)


def run(archive_dir, schedule, freeze, results=None, replay=False, fetch=False):
    sched = pd.read_parquet(schedule)
    games = ft.games_from_schedule(sched)
    lib = build_library(sched, before_season=2026)
    res = {e: (g["hp"], g["ap"]) for e, g in games.items() if g["hp"] is not None}
    if results:
        res.update({e: tuple(v) for e, v in json.load(open(results)).items()})
    if fetch:
        from prediction_market_bot.c1_signal_ingestion.nfl_espn_results import fetch_nfl_final_score
        for e, g in games.items():
            if e in res or g["ko"] >= pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"):
                continue
            r = fetch_nfl_final_score(g["ko"][:10], g["home"], g["away"])
            if r:
                res[e] = (int(r.home_score), int(r.away_score))
    start = "2000-01-01T00:00:00Z" if replay else freeze
    if replay:   # replay: score every archived game that already has a result, as if each were post-freeze
        games = {e: {**g, "ko": g["ko"]} for e, g in games.items() if e in res}
    pos = ft.find_triggers(ft.iter_snapshots(read_archive(archive_dir)), games, ft.BoardCache(lib), start) if not replay \
        else _replay_triggers(archive_dir, games, lib)
    settled = ft.settle(pos, games, res)
    out = dict(freeze=freeze, replay=replay, triggered=len(pos), settled=len(settled),
               games_with_result=len({p["event"] for p in settled}), fam=ft.score(settled),
               games_remaining=sum(1 for e, g in games.items() if g["ko"] > freeze and e not in res))
    sds = [v["sd_game"] for v in out["fam"].values() if v["games"] > 1]
    if sds:
        out["judged_n_games"] = {f: ft.power_n(v["sd_game"], MDE) for f, v in out["fam"].items() if v["games"] > 1}
    return out


def _replay_triggers(archive_dir, games, lib):
    """Replay treats the first archived snapshot of each game as the freeze for that game."""
    first = {}
    snaps = list(ft.iter_snapshots(read_archive(archive_dir)))
    for ts, byev in snaps:
        for e in byev:
            first.setdefault(e, ts)
    g2 = {e: g for e, g in games.items() if e in first}
    return ft.find_triggers(iter(snaps), g2, ft.BoardCache(lib), "2000-01-01T00:00:00Z")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default="exp_output/PRICE_ARCHIVE")
    ap.add_argument("--schedule", default=sorted(glob.glob("exp_output/NFL_EVENTS/raw/schedules/schedules_*.parquet"))[-1])
    ap.add_argument("--freeze", default=FREEZE_DEFAULT)
    ap.add_argument("--results"); ap.add_argument("--fetch", action="store_true"); ap.add_argument("--replay", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    o = run(a.archive, a.schedule, a.freeze, a.results, a.replay, a.fetch)
    json.dump(o, open(safe_out(a.out), "w"), indent=1, default=float)
    print(json.dumps(o, indent=1, default=float))

#!/usr/bin/env python3
"""T-589 D2: cost of one PaperTrader._save() on a COPY of a real pool.

Never touches the source pool: the source is copied into a temp dir and every
measurement runs against that copy. Row count is scaled by duplicating real
closed_positions rows (fresh position_id) in the copy.

Usage: bench_paper_trader_save.py SOURCE_POOL.json [--reps N] [--scales 1,2,5,10]
"""
from __future__ import annotations

import argparse, copy, json, os, shutil, statistics, sys, tempfile, time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("BOT_ENV", "paper")
from prediction_market_bot.c5_execution.paper_trader import PaperTrader  # noqa: E402


def rows(state: dict) -> int:
    return sum(len(state.get(k, [])) for k in ("open_positions", "closed_positions", "rejected_positions"))


def scaled(base: dict, k: int) -> dict:
    s = copy.deepcopy(base)
    closed = base.get("closed_positions", [])
    extra = []
    for rep in range(1, k):
        for i, r in enumerate(closed):
            c = dict(r)
            c["position_id"] = f"{r.get('position_id', 'P')}-dup{rep}-{i}"
            extra.append(c)
    s["closed_positions"] = closed + extra
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--reps", type=int, default=15)
    ap.add_argument("--scales", default="1,2,5,10")
    a = ap.parse_args()
    base = json.load(open(a.source))
    src_bytes = os.path.getsize(a.source)
    tmp = Path(tempfile.mkdtemp(prefix="bench_save_"))
    try:
        print(f"source={a.source} bytes={src_bytes} rows={rows(base)} (copy in {tmp})")
        print("| scale | rows | bytes indent=2 | ms/save indent=2 | MB/save | bytes compact | ms/save compact | saving |")
        print("|---|---|---|---|---|---|---|---|")
        for k in [int(x) for x in a.scales.split(",")]:
            pool = tmp / f"pool_x{k}.json"
            st = scaled(base, k)
            pool.write_text(json.dumps(st))
            tr = PaperTrader(pool, MagicMock())
            tr._save()
            b_ind = os.path.getsize(pool)
            t = []
            for _ in range(a.reps):
                t0 = time.perf_counter(); assert tr._save(); t.append((time.perf_counter() - t0) * 1000)
            ms_ind = statistics.median(t)
            # compact: same serialisation cost minus whitespace, timed in isolation
            t = []
            for _ in range(a.reps):
                t0 = time.perf_counter()
                txt = json.dumps(tr._state, separators=(",", ":"))
                tr._atomic_write_text(txt)
                t.append((time.perf_counter() - t0) * 1000)
            ms_cmp = statistics.median(t); b_cmp = os.path.getsize(pool)
            print(f"| {k}x | {rows(tr._state)} | {b_ind} | {ms_ind:.1f} | {b_ind/1e6:.2f} | {b_cmp} | {ms_cmp:.1f} | {100*(1-b_cmp/b_ind):.0f}% bytes, {100*(1-ms_cmp/ms_ind):.0f}% ms |")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()

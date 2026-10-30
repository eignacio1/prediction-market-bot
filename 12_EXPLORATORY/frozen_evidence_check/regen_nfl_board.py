"""W96.2 Part A: re-generate the three `nfl_board_v2` JSONs on the box without dirtying the repo tree.

Runs 93.4's scripts UNCHANGED (heldout_keynumbers.py, kalshi_compare.py x {gt off3, gt off6}, n15_interpret.py) from the repo root with
`_fence.safe_out` redirected to a scratch directory, then prints every JSON they wrote. The scripts' inputs (the 2026-10-20 schedules
parquet, the price archive) exist only on the box. The box's repo tree and archive are read, never written.

  regen_nfl_board.py --archive exp_output/PRICE_ARCHIVE [--out DIR]

Applies to: re-running 93.4's NFL board v2 checks on the box's full archive. Not a new test.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import runpy
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
SCRIPTS = os.path.join(EXP, "nfl_board_v2")
RUNS = (("heldout_keynumbers.py", []), ("kalshi_compare.py", ["{PR}", "3", "gt"]), ("kalshi_compare.py", ["{PR}", "6", "gt"]),
        ("n15_interpret.py", []))


def nfl_rows(archive: str, dest: str) -> int:
    """Stream the archive's KXNFL* rows into one file (kalshi_compare.py reads a single JSONL path)."""
    n = 0
    with open(dest, "w") as out:
        for f in sorted(glob.glob(os.path.join(archive, "prices_*.jsonl"))):
            with open(f) as fh:
                for line in fh:
                    if '"series_ticker": "KXNFL' in line or '"series_ticker":"KXNFL' in line:
                        out.write(line)
                        n += 1
    return n


def regenerate(archive: str, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    sys.path[:0] = [os.path.join(EXP, "..", "src"), EXP]
    import _fence

    def scratch_out(path):
        p = os.path.join(out_dir, os.path.basename(str(path)))
        return type(_fence.ROOT)(p)

    _fence.safe_out = scratch_out
    pr = os.path.join(out_dir, "_nfl_rows.jsonl")
    n_rows = nfl_rows(archive, pr)
    for script, argv in RUNS:
        sys.argv = [script] + [pr if a == "{PR}" else a for a in argv]
        runpy.run_path(os.path.join(SCRIPTS, script), run_name="__main__")
    os.remove(pr)
    res = {"archive_nfl_rows": n_rows}
    for p in sorted(glob.glob(os.path.join(out_dir, "*.json"))):
        res[os.path.basename(p)] = json.load(open(p))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    out = a.out or tempfile.mkdtemp(prefix="w96_2_nfl_board_")
    print(json.dumps(regenerate(a.archive, out), indent=1))


if __name__ == "__main__":
    main()

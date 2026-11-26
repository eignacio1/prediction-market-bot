"""W129.2 Part C: freeze the 2025-26 per-player season totals (by norm_name) as the previous-season table for the 2026-27 forward shadow.
Usage: build_prev_table.py <NBA_EVENTS root> <out.json inside 12_EXPLORATORY>; the file is then copied to data/reference/ by hand (the fence allows no other write path). Reads outcomes through 2026-07-31 only; no 2026-27 row."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_shrunk as RS  # noqa: E402
from _fence import safe_out  # noqa: E402

SEASON = ("2025-08-01", "2026-07-31")


def main(root: Path, out: Path) -> None:
    reg, _tips, pb = RS.R.load(root)
    ids = [g for g in reg.index if SEASON[0] <= str(reg.loc[g, "game_date"])[:10] <= SEASON[1]]
    table = RS.prev_table(pb[pb.game_id.isin(ids)])
    safe_out(out).write_text(json.dumps(dict(season="2025-26", games=len(ids), data_through=SEASON[1], players=table), sort_keys=True, indent=0))
    print(f"games={len(ids)} players={len(table)} -> {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))

#!/usr/bin/env python3
"""Calibration engine CLI (W58.3). Read-only on every ledger; writes only exp_output/CALIBRATION/ (engine_<UTC>.json and the write-once release manifests).

Prints counts, status and projected first-look date per cell. Score fields exist only for cells the
pre-registration allows; sealed cells never carry one, so nothing sealed can be printed.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
from prediction_market_bot.pregame_shadow import calibration_engine as ce  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--out-dir", default=None, help="default <repo>/exp_output/CALIBRATION")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--synthetic-report", metavar="PATH", help="write a first-look REPORT rehearsal on generated data and exit")
    a = ap.parse_args(argv)
    repo = Path(a.repo)
    if a.synthetic_report:
        from prediction_market_bot.pregame_shadow import first_look_report as flr
        txt = flr.render_report(flr.synthetic_cells(), "First-look REPORT - synthetic rehearsal", synthetic=True,
                                note="NHL synthetic cell uses bootstrap B=400 for runtime (the pre-registration is B=10,000).")
        Path(a.synthetic_report).write_text(txt)
        print(f"wrote {a.synthetic_report}")
        return 0
    res = ce.run(repo, persist=not a.no_write)
    if not a.no_write:
        d = Path(a.out_dir) if a.out_dir else repo / "exp_output/CALIBRATION"
        d.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        (d / f"engine_{stamp}.json").write_text(json.dumps(res, indent=1, default=str))
        released = [c for c in res["cells"] if c.get("release") and c.get("verdict")]
        if released:        # only cells the engine itself released; frozen manifests make this report reproducible
            from prediction_market_bot.pregame_shadow import first_look_report as flr
            (d / "FIRST_LOOK_REPORT.md").write_text(flr.render_report(released, "First-look REPORT (released cells only)"))
    print(f"{'cell':34} {'status':26} {'rows':>7} {'games':>6} {'%look':>6}  first look")
    for c in res["cells"]:
        pj = c["projection"]
        print(f"{c['cell']:34} {c['status_text']:26} {c['rows']:>7} {c['settled_games']:>6} "
              f"{(c['pct_to_first_look'] if c['pct_to_first_look'] is not None else '-')!s:>6}  "
              f"{pj['date'] or pj['note']}")
    print(json.dumps(res["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""W108.5: peak resident memory of ONE build of each heavy dashboard page, each in a fresh subprocess so the numbers do
not contaminate each other. READ-ONLY: imports scripts/web_dashboard.py, calls its builders, prints sizes and ru_maxrss.
Usage: dashboard_build_peak.py [--log-dir DIR]     (the service's own log dir by default)"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHILD = r"""
import resource, sys, time
_D = 1024 if sys.platform == 'darwin' else 1  # macOS reports bytes, Linux KB
from pathlib import Path
sys.path.insert(0, {here!r})
import web_dashboard as wd
wd._log_dir = Path({log_dir!r})
base = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // _D
t = time.time()
what = {what!r}
if what == "import_only":
    size = 0
elif what == "visual":
    v = wd._build_visual_page(); size = len(v)
elif what == "project":
    v = wd._build_project_page(); size = len(v)
else:
    v = wd._build_data_body(); size = len(v)
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // _D
print(what, "bytes=%d" % size, "seconds=%.1f" % (time.time() - t), "baseline_rss_kb=%d" % base, "peak_rss_kb=%d" % peak)
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-dir", default="/opt/prediction-market-bot/logs/")
    a = ap.parse_args()
    for what in ("import_only", "visual", "project", "data"):
        code = CHILD.format(here=str(HERE), log_dir=a.log_dir, what=what)
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=300)
        print((r.stdout.strip() or "(no output)") + (("  ERR " + r.stderr.strip()[-300:]) if r.returncode else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

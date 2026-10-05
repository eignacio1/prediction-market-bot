#!/usr/bin/env python3
"""GG-477: de-stampede the :00/:30 cron minute on the 961 MB VPS.

Run ON the VPS:  ssh prediction-market-vps 'python3 -' < scripts/ops/gg477_cron_stagger.py
Dry-run by default; pass APPLY=1 in the environment to install.
Changes ONLY the minute field of the schedule lines below. Commands, hours, and
run_paper_trade / run_pregame timings are untouched. Backs up the crontab first.
"""
import os, re, subprocess, sys, time

# (command marker, old minute field, new minute field, expected line count)
RULES = [
    ("nhl_shadow_eval.py --band T2", "*/30", "4,34", 2),
    ("nhl_shadow_eval.py --band T3", "*/10", "6,16,26,36,46,56", 2),
    ("run_pregame_shadow.py --bands T3", "*/10", "8,18,28,38,48,58", 1),
    ("run_t3_pretip.py", "*/15", "1,16,31,46", 2),
    ("run_t3_mlb_pretip.py", "*/15", "2,17,32,47", 2),
]

cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=True).stdout
lines, counts = [], {r[0]: 0 for r in RULES}
for ln in cur.splitlines():
    for marker, old, new, _ in RULES:
        if marker in ln and not ln.lstrip().startswith("#"):
            f = ln.split(None, 1)
            if f[0] == old:
                ln = new + " " + f[1]
                counts[marker] += 1
                break
    lines.append(ln)

bad = {m: (counts[m], n) for m, _, _, n in RULES if counts[m] != n}
if bad:
    sys.exit(f"ABORT: unexpected match counts (found, expected): {bad}")

new = "\n".join(lines) + "\n"
bak = f"/root/crontab.bak.{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
open(bak, "w").write(cur)
open("/tmp/crontab.new", "w").write(new)
print("backup:", bak)
print(subprocess.run(["diff", bak, "/tmp/crontab.new"], capture_output=True, text=True).stdout)
if os.environ.get("APPLY") == "1":
    subprocess.run(["crontab", "/tmp/crontab.new"], check=True)
    print("INSTALLED. Restore with: crontab", bak)
else:
    print("DRY RUN only. Re-run with APPLY=1 to install.")

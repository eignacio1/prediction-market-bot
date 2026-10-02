"""Detach the D1(b)-2 sampler into its own session (macOS has no setsid) and record its PID."""
import os
import subprocess
import sys

D = "exp_output/EXP-034-NONSPORTS-CONTROL"
log = open(f"{D}/d1b2_sampler.log", "a")
p = subprocess.Popen(
    [sys.executable, "scripts/board_survey_nonsports_d1b2_sampler.py", f"{D}/d1b2_live_quotes.jsonl", sys.argv[1]],
    stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
with open(f"{D}/d1b2_sampler.pid", "w") as f:
    f.write(str(p.pid))
print(p.pid)

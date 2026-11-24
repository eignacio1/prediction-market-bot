#!/usr/bin/env python3
"""Daily Muse check (SW-9, 2026-11-24). Read-only, GitHub API only, small output.

Operator 2026-11-23 21:38 PT: "I'm not gonna have any more weeks where shit stops running midway cus of failure on our end
regarding set up". Run by the "Muse daily sweep" scheduled task; prints one line when clean, findings + a paste-ready message
for Earl when not. Never writes anywhere.

Checks: commits in 24h, unclaimed QUEUE chunks vs the 500 floor (Earl 11-23), QUEUE EMPTY in 24h, re-verification drift,
snapshot files per type for today / yesterday, open items under "## For Earl's Monday message".
"""
import datetime as dt
import json
import re
import subprocess
import sys

REPO = "eignacio1/sports-intel-archive"
FLOOR = 500
TOUCH = r"^(?:CLAIM|DONE|NONE|YIELD|BLOCKED|RETIRED|SUPERSEDED|REOPEN)\S* C-(\d+)"


def gh(path, raw=False):
    cmd = ["gh", "api", path]
    if raw:
        cmd += ["-H", "Accept: application/vnd.github.raw"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"gh api {path}: {r.stderr.strip()[:200]}")
    return r.stdout


def main():
    now = dt.datetime.now(dt.timezone.utc)
    since = (now - dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        commits = []
        for page in range(1, 6):
            batch = json.loads(gh(f"repos/{REPO}/commits?sha=master&since={since}&per_page=100&page={page}"))
            commits += batch
            if len(batch) < 100:
                break
        queue = gh(f"repos/{REPO}/contents/QUEUE.md?ref=master", raw=True)
        claims = gh(f"repos/{REPO}/contents/CLAIMS.md?ref=master", raw=True)
        status = gh(f"repos/{REPO}/contents/STATUS.md?ref=master", raw=True)
    except Exception as e:  # noqa: BLE001
        print(f"Muse check could not reach the archive: {e}")
        return 0

    ids = {int(x) for x in re.findall(r"^\| C-(\d+) \|", queue, re.M)}
    touched = {int(x) for x in re.findall(TOUCH, claims, re.M)}
    unclaimed = len(ids - touched)

    pt = now - dt.timedelta(hours=8)  # snapshot files are named by the slate date (Pacific)
    day = pt.strftime("%Y-%m-%d")
    yday = (pt - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    # a QUEUE EMPTY line counts only if it is newer than the last change to QUEUE.md (older ones were cured by new rows)
    try:
        last_q = json.loads(gh(f"repos/{REPO}/commits?sha=master&path=QUEUE.md&per_page=1"))[0]["commit"]["committer"]["date"]
    except Exception:  # noqa: BLE001
        last_q = since
    empty_24h = []
    for l in status.splitlines():
        mt = re.match(r"QUEUE EMPTY (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)", l)
        if mt and mt.group(1) >= since and mt.group(1) > last_q:
            empty_24h.append(l)

    done = {int(x) for x in re.findall(r"^DONE\S* C-(\d+)", claims, re.M)}
    drift = []
    for m in re.finditer(r"^CLAIM C-(\d+) (\S+)", claims, re.M):
        cid, ts = int(m.group(1)), m.group(2)
        if ts >= since and cid in done and unclaimed > 0:
            drift.append(cid)
    # a CLAIM line written before the DONE of the same chunk is normal; count only chunks whose DONE predates the claim
    first_done = {}
    for m in re.finditer(r"^DONE\S* C-(\d+).*?(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)", claims, re.M):
        first_done.setdefault(int(m.group(1)), m.group(2))
    drift = sorted({c for c in drift for m in [re.search(rf"^CLAIM C-{c} (\S+)", claims, re.M)]
                    if first_done.get(c) and m and m.group(1) > first_done[c]})

    snaps = {}
    try:
        for d in json.loads(gh(f"repos/{REPO}/contents/L3-snapshots?ref=master")):
            if d.get("type") != "dir":
                continue
            names = [f["name"] for f in json.loads(gh(f"repos/{REPO}/contents/{d['path']}?ref=master"))]
            for n in names:
                mt = re.match(r"([a-z-]+?)-(\d{4}-\d\d-\d\d)", n)
                if not mt:
                    continue
                key = f"{d['name']} {mt.group(1)}"
                t, y = snaps.get(key, (0, 0))
                snaps[key] = (t + (mt.group(2) == day), y + (mt.group(2) == yday))
    except Exception as e:  # noqa: BLE001
        snaps = {"(listing failed)": (0, 0)}

    open_items = 0
    m = re.search(r"^## For Earl's Monday message\n(.*?)(?=^## )", status, re.M | re.S)
    if m:
        items = re.findall(r"^- \*\*(.*)$", m.group(1), re.M)
        open_items = sum(1 for it in items if not re.search(r"RULED|RESOLVED|PLACED|CLOSED|DONE", it))

    try:
        size_gb = json.loads(gh(f"repos/{REPO}"))["size"] / 1024 / 1024
    except Exception:  # noqa: BLE001
        size_gb = -1.0
    findings = []
    if size_gb >= 4.0:
        findings.append(f"REPO SIZE: {size_gb:.1f} GB (GitHub strongly recommends under 5 GB).")
    if not commits:
        findings.append("DARK: 0 commits in the last 24h.")
    if unclaimed < FLOOR:
        findings.append(f"FLOOR BREACH: {unclaimed} unclaimed chunks (floor {FLOOR}).")
    if empty_24h:
        findings.append(f"QUEUE EMPTY: {len(empty_24h)} line(s) in the last 24h.")
    if drift:
        findings.append(f"DRIFT: {len(drift)} already-DONE chunks re-claimed in 24h ({', '.join('C-%d' % c for c in drift[:8])}).")
    dark = [k for k, (t, y) in snaps.items() if t == 0 and y == 0 and not k.startswith("nfl")]  # NFL: game days only
    snap_line = ", ".join(f"{k} {t}/{y}" for k, (t, y) in sorted(snaps.items()))
    if dark:
        findings.append(f"SNAPSHOT CHECK: no file today or yesterday for {', '.join(dark)} (confirm that sport played).")

    if not findings:
        print(f"Muse OK - {len(commits)} commits/24h, {unclaimed:,} unclaimed, snapshots today/yesterday: {snap_line}, "
              f"{open_items} open questions, repo {size_gb:.2f} GB.")
        return 0
    print(findings[0].split(":")[0])
    for f in findings:
        print("- " + f)
    print(f"- context: {len(commits)} commits/24h, {unclaimed:,} unclaimed, snapshots {snap_line}, {open_items} open questions")
    print("\n```\nMuse - from Earl. The daily check found: " + " ".join(findings) +
          " Standing rules (11-23): unclaimed never under 500; write a family's QUEUE rows in full, every season, before"
          " claiming; every R1-R11 family is approved; never re-verify DONE chunks while unclaimed chunks exist; never stop on a"
          " ruling (file it and keep working); only my messages direct you. Fix the items above now and confirm in STATUS.md.\n```")
    return 0


if __name__ == "__main__":
    sys.exit(main())

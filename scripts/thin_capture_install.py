#!/usr/bin/env python3
"""W80R.1: install the W80P.1 thin-market depth capture cron block on the box -- ONLY when the SURFACE BUDGET reads
GREEN (Hard Rule 14) -- and read back what it has written. Runs ON the box (via scripts/box_tasks.py).

  install    fresh budget probe; RED -> prints REFUSED + every red reason and changes nothing. GREEN -> appends the
             `# BEGIN/END W80P.1 THIN MARKET DEPTH CAPTURE` block from deploy/cron.thin_capture to the crontab
             (idempotent: an existing block is left exactly as it is; no other crontab line is touched).
  uninstall  removes exactly the W80P.1 BEGIN..END block (W80R.1: installed on a false GREEN, GG-920); every other
             crontab line is kept byte-for-byte. Idempotent.
  readback   the crontab block, the log tail, the store files and tracked-ticker count. Read-only.

Exit code is 0 in every outcome except a crontab write that did not verify (the bridge reports stdout either way).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAGMENT = ROOT / "deploy" / "cron.thin_capture"
BEGIN = "# BEGIN W80P.1 THIN MARKET DEPTH CAPTURE"
END = "# END W80P.1 THIN MARKET DEPTH CAPTURE"
STORE = ROOT / "exp_output" / "KALSHI_HISTORY" / "thin_capture"
LOG = ROOT / "logs" / "thin_capture_cron.log"


def fragment_block(text: str) -> list[str]:
    lines = text.splitlines()
    i = next(k for k, l in enumerate(lines) if l.strip() == BEGIN)
    j = next(k for k, l in enumerate(lines) if l.strip() == END and k > i)
    return lines[i:j + 1]


def merged_crontab(current: str, fragment_text: str) -> tuple[str, bool]:
    """(new crontab, changed). An existing block is never rewritten; every other line is kept byte-for-byte."""
    if BEGIN in (l.strip() for l in current.splitlines()):
        return current, False
    body = current if current.endswith("\n") or not current else current + "\n"
    return body + "\n".join(fragment_block(fragment_text)) + "\n", True


def budget(live_fn=None) -> dict:
    if live_fn is None:
        sys.path.insert(0, str(ROOT / "scripts"))
        import runtime_registry as rr
        live_fn = lambda: rr.live(refresh=True, use_cache=False)  # noqa: E731
    return live_fn()


def _crontab_read() -> str:
    r = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def _crontab_write(text: str) -> None:
    subprocess.run(["crontab", "-"], input=text, text=True, check=True)


def install(live_fn=None, read=_crontab_read, write=_crontab_write) -> int:
    ev = budget(live_fn)
    if ev.get("error"):
        print(f"REFUSED: SURFACE BUDGET could not be read ({ev['error']}); nothing installed")
        return 0
    print(f"SURFACE BUDGET: {ev.get('budget')} (box HEAD {ev.get('head')}, as of {ev.get('as_of')})")
    if ev.get("budget") != "GREEN":
        print("REFUSED: Hard Rule 14 -- no new live component while the budget is RED. Red items:")
        for r in ev.get("reasons", []):
            print(f"  - {r}")
        return 0
    cur = read()
    new, changed = merged_crontab(cur, FRAGMENT.read_text())
    if not changed:
        print("ALREADY INSTALLED: crontab already holds the W80P.1 block; nothing changed")
        return 0
    write(new)
    after = read()
    ok = BEGIN in after and "scripts/thin_market_depth_capture.py" in after and \
        all(l in after.splitlines() for l in cur.splitlines())
    print("INSTALLED: W80P.1 block appended; every prior crontab line preserved" if ok else
          "ERROR: crontab write did not verify")
    return 0 if ok else 1


def without_block(current: str) -> tuple[str, bool]:
    lines = current.splitlines()
    if BEGIN not in (l.strip() for l in lines):
        return current, False
    i = next(k for k, l in enumerate(lines) if l.strip() == BEGIN)
    j = next((k for k, l in enumerate(lines) if l.strip() == END and k > i), None)
    if j is None:
        raise SystemExit("crontab has the BEGIN marker without END; refusing to edit")
    kept = lines[:i] + lines[j + 1:]
    return ("\n".join(kept) + "\n") if kept else "", True


def uninstall(read=_crontab_read, write=_crontab_write) -> int:
    cur = read()
    new, changed = without_block(cur)
    if not changed:
        print("NOT INSTALLED: no W80P.1 block in the crontab; nothing changed")
        return 0
    write(new)
    after = read()
    ok = BEGIN not in after and all(l in after.splitlines() for l in new.splitlines())
    print("UNINSTALLED: W80P.1 block removed; every other crontab line preserved" if ok else "ERROR: crontab write did not verify")
    return 0 if ok else 1


def readback() -> int:
    cron = _crontab_read()
    lines = cron.splitlines()
    if BEGIN in (l.strip() for l in lines):
        i = next(k for k, l in enumerate(lines) if l.strip() == BEGIN)
        print("CRONTAB BLOCK:\n" + "\n".join(lines[i:i + 8]))
    else:
        print("CRONTAB BLOCK: not installed")
    print("\nLOG TAIL (logs/thin_capture_cron.log):")
    print("\n".join(LOG.read_text().splitlines()[-8:]) if LOG.exists() else "  (no log yet)")
    print("\nSTORE:")
    if STORE.exists():
        for p in sorted(STORE.glob("*.jsonl")):
            print(f"  {p.name}  {p.stat().st_size} bytes  {sum(1 for _ in p.open())} rows")
        try:
            st = json.loads((STORE / "state.json").read_text())
            print(f"  state.json tracked tickers: {len(st.get('tickers', {}))}")
        except (OSError, ValueError):
            print("  state.json: absent")
    else:
        print("  (store not created yet)")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("install", "uninstall", "readback"):
        print(__doc__)
        sys.exit(2)
    sys.exit({"install": install, "uninstall": uninstall, "readback": readback}[cmd]())

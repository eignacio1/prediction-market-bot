#!/usr/bin/env python3
"""CLAUDE.md "Right now" block (operator 2026-11-10 22:28 PT). Alarm-only: always exits 0 unless --strict.

CLAUDE.md is loaded into every Claude Code session before anything else, so the operator's rule is that it must be accurate
"to the exact state of the project AT THAT EXACT MOMENT". The facts that live in code are not typed by hand: this script
computes them and writes them between the NOW markers.

  python3 scripts/claude_md_now.py --write   # regenerate the generated part of the block (the window, at every wave close)
  python3 scripts/claude_md_now.py           # check: RED if the block disagrees with the code, or either part is stale

Generated part: registry cells by sport and status, the non-shadow cells by name, bands with a non-zero Kelly fraction and
whether any ACTIVE cell sits on them, the OPEN governance-gap count. The window-maintained lines just below the block carry
their own "as of" date; older than --max-days (default 7) is RED.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- NOW:BEGIN"
END = "<!-- NOW:END -->"
HAND_RE = re.compile(r"\*\*Window-maintained \(as of (\d{4}-\d{2}-\d{2})")
ASOF_RE = re.compile(r"^Generated (\d{4}-\d{2}-\d{2})")

# Plain words for the registry enum (DOCTRINE.md section 1b: human text never says "ruled out" for a model that lost).
LABEL = {
    "shadow": "shadow (no orders; logs when its sport is in season)",
    "active": "active",
    "blocked": "blocked",
    "dark": "dark",
    "ruled_out": "fade arm closed (routed; provisional, DOCTRINE 8)",
    "not_implemented": "registered, not built",
}


SHORT = {"shadow": "shadow", "active": "active", "blocked": "blocked", "dark": "dark",
         "ruled_out": "fade arm closed", "not_implemented": "not built"}


def _v(x) -> str:
    return str(getattr(x, "value", x))


def compute(root: Path = ROOT) -> list[str]:
    """The generated lines (no date line). Pure function of the repo at HEAD."""
    sys.path.insert(0, str(root / "src"))
    lines: list[str] = []
    try:
        from prediction_market_bot.c5_execution.market_type_registry import MARKET_TYPE_REGISTRY as reg
        from prediction_market_bot.execution_bands import BAND_CONFIGS
    except Exception as exc:  # alarm-only: never break a session start
        return [f"- Registry: UNKNOWN (import failed: {type(exc).__name__})"]
    cells = list(reg.values()) if isinstance(reg, dict) else list(reg)
    total = Counter(_v(c.status) for c in cells)
    order = ["shadow", "active", "blocked", "dark", "ruled_out", "not_implemented"]
    lines.append(f"- Registry: {len(cells)} cells - " + " · ".join(
        f"{total[s]} {LABEL[s]}" for s in order if total[s]) + ".")
    by: dict[str, Counter] = defaultdict(Counter)
    for c in cells:
        by[_v(c.market_type).split("_")[0].upper()][_v(c.status)] += 1
    for sport in sorted(by):
        lines.append(f"  - {sport}: " + " · ".join(f"{by[sport][s]} {SHORT[s]}" for s in order if by[sport][s]))
    odd = sorted(f"{_v(c.market_type)} / {_v(c.band)} - {LABEL.get(_v(c.status), _v(c.status))}"
                 for c in cells if _v(c.status) not in ("shadow", "not_implemented"))
    if odd:
        lines.append("- Not shadow, not unbuilt: " + "; ".join(odd) + ".")
    active_bands = {_v(c.band) for c in cells if _v(c.status) == "active"}
    zero = sorted(_v(b) for b, cfg in BAND_CONFIGS.items() if not getattr(cfg, "kelly_fraction", 0))
    pos = sorted((_v(b), cfg.kelly_fraction) for b, cfg in BAND_CONFIGS.items() if getattr(cfg, "kelly_fraction", 0))
    pos_live = [f"{b} {k}" for b, k in pos if b in active_bands]
    lines.append(f"- Kelly (execution_bands.py): 0.0 on {', '.join(zero) or 'none'}. Non-zero on a band with an ACTIVE cell: "
                 + (", ".join(pos_live) if pos_live else "none") + f". Provisional non-zero values on {len(pos)} bands with "
                 "no ACTIVE cell; no real capital anywhere (Hard Rule 2).")
    ggl = root / "03_DECISIONS" / "GOVERNANCE_GAP_LOG.md"
    if ggl.exists():
        n = len(re.findall(r"^\*\*Status:\*\* OPEN\b", ggl.read_text(encoding="utf-8"), re.M))
        lines.append(f"- Open governance gaps: {n} (03_DECISIONS/GOVERNANCE_GAP_LOG.md).")
    return lines


def _split(text: str):
    b, e = text.find(BEGIN), text.find(END)
    if b < 0 or e < 0 or e < b:
        return None
    head_end = text.find("\n", b) + 1
    return text[:head_end], text[head_end:e], text[e:]


def write(path: Path, today: dt.date) -> bool:
    text = path.read_text(encoding="utf-8")
    parts = _split(text)
    if parts is None:
        print(f"claude_md_now: RED - no NOW markers in {path.name}")
        return False
    head, _, tail = parts
    body = f"Generated {today.isoformat()} by `scripts/claude_md_now.py --write` from the code at that commit.\n" + \
        "\n".join(compute(path.parent)) + "\n"
    path.write_text(head + body + tail, encoding="utf-8")
    print(f"claude_md_now: wrote the NOW block ({today.isoformat()})")
    return True


def check(path: Path, today: dt.date, max_days: int) -> list[str]:
    reds: list[str] = []
    if not path.exists():
        return [f"{path.name} missing"]
    text = path.read_text(encoding="utf-8")
    parts = _split(text)
    if parts is None:
        return ["no NOW markers in CLAUDE.md"]
    _, body, tail = parts
    blines = body.strip("\n").splitlines()
    m = ASOF_RE.match(blines[0]) if blines else None
    if not m:
        reds.append("NOW block has no 'Generated YYYY-MM-DD' line")
    else:
        age = (today - dt.date.fromisoformat(m.group(1))).days
        if age > max_days:
            reds.append(f"NOW block generated {m.group(1)} ({age} days old > {max_days})")
    want = compute(path.parent)
    have = blines[1:]
    if have != want:
        for w in want:
            if w not in have:
                reds.append(f"code says: {w.strip()}")
    h = HAND_RE.search(tail)
    if not h:
        reds.append("no 'Window-maintained (as of YYYY-MM-DD' line under the NOW block")
    else:
        age = (today - dt.date.fromisoformat(h.group(1))).days
        if age > max_days:
            reds.append(f"window-maintained lines as of {h.group(1)} ({age} days old > {max_days})")
    return reds


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--file", default=str(ROOT / "CLAUDE.md"))
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--max-days", type=int, default=7)
    ap.add_argument("--today", default=None, help="YYYY-MM-DD (tests)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on RED (off by default; alarm-only)")
    a = ap.parse_args(argv)
    today = dt.date.fromisoformat(a.today) if a.today else dt.datetime.now(dt.timezone.utc).date()
    path = Path(a.file)
    if a.write:
        return 0 if write(path, today) or not a.strict else 1
    reds = check(path, today, a.max_days)
    if reds:
        print("CLAUDE.md RIGHT NOW: RED - the file every session reads first is not current. Fix it this turn "
              "(python3 scripts/claude_md_now.py --write; update the window-maintained lines):")
        for r in reds:
            print(f"  RED {r}")
    else:
        print("CLAUDE.md RIGHT NOW: current (generated block matches the code; window lines within "
              f"{a.max_days} days)")
    return 1 if (reds and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())

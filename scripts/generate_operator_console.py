#!/usr/bin/env python3
"""Generate OPERATOR_CONSOLE.md from GOVERNANCE_GAP_LOG.md's live (non-archived) entries.

T-420 (2026-08-05, console/archive split, agreed 2026-08-02 per
04_EXECUTION/SCALING_MANDATE_PARKED.md "What was already agreed"). Read-only
against GOVERNANCE_GAP_LOG.md -- never writes to it. Output is fully generated;
never hand-patch OPERATOR_CONSOLE.md for content, edit this script and re-run.

Ranking is "blocks operator" not severity (17 open gaps is not the problem;
not knowing which 3 need Earl specifically is). Every live entry lands in
exactly one of three sections, by mechanical priority:

  1. DECISIONS BLOCKED ON EARL -- body text matches BLOCKED_RE (explicit
     operator/Earl/DS-sign-off/awaiting-direction language already present
     in the entry's own prose -- nothing invented, nothing inferred from
     severity or status token alone).
  2. WHAT IS ACTUALLY BROKEN -- not blocked-on-operator, and either
     severity is HIGH/CRITICAL or body text matches BROKEN_RE (HALT, silent
     failure, blind spot, undetected, regression, contradiction language).
  3. WHAT IS ACCRUING AND ITS CLOCK -- everything else that is still open.
     Default bucket, not a weaker signal -- it means no explicit
     blocked/broken language was found, not that nothing matters.

Both regexes are grounded in vocabulary actually observed in the log's own
prose (verified via direct grep before this script was written), not
invented categories. If a bucket looks wrong, the fix is to correct the
regex here and regenerate -- never to hand-edit the console output.
"""
import re
import sys
from pathlib import Path

GGL = Path("03_DECISIONS/GOVERNANCE_GAP_LOG.md")
OUT = Path("03_DECISIONS/OPERATOR_CONSOLE.md")

HEADER_RE = re.compile(r"^### (GG-\d+) — (.+)$", re.M)
STATUS_RE = re.compile(r"^\*\*Status:\*\* (.+?) · \*\*Severity:\*\* (.+)$", re.M)

BLOCKED_RE = re.compile(
    r"operator (decision|direction|sign-?off|approval)|Earl'?s decision|"
    r"DS sign-?off|awaiting (operator|Earl)|requires (operator|Earl)|"
    r"register (the )?(operator|Earl)|pending operator|not yet directed|"
    r"operator must|operator has not|awaiting direction",
    re.I,
)
BROKEN_RE = re.compile(
    r"\bHALT\b|silently (wrong|failing|fail)|silent failure|blind spot|"
    r"undetected|contradict|never (existed|caught)|regression|incorrect|"
    r"does not match|failure mode",
    re.I,
)

SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNSPECIFIED": 4}


def parse_entries(text):
    starts = [(m.start(), m.group(1), m.group(2)) for m in HEADER_RE.finditer(text)]
    starts = [s for s in starts if re.match(r"GG-\d+$", s[1])]  # exclude GG-NNN template
    starts.append((len(text), None, None))
    entries = []
    for i in range(len(starts) - 1):
        s, gid, title = starts[i]
        e = starts[i + 1][0]
        block = text[s:e]
        m = STATUS_RE.search(block)
        token, sev = (m.group(1), m.group(2)) if m else ("UNKNOWN", "UNSPECIFIED")
        entries.append({"id": gid, "title": title, "token": token, "severity": sev, "block": block})
    return entries


def classify(entry):
    if BLOCKED_RE.search(entry["block"]):
        return "blocked"
    if entry["severity"] in ("HIGH", "CRITICAL") or BROKEN_RE.search(entry["block"]):
        return "broken"
    return "accruing"


def render_row(e):
    return f"- **[{e['id']}]** {e['title']} — `{e['token']}` · severity `{e['severity']}`"


def main():
    if not GGL.exists():
        print(f"ERROR: {GGL} not found", file=sys.stderr)
        return 1
    text = GGL.read_text()
    entries = parse_entries(text)

    buckets = {"blocked": [], "broken": [], "accruing": []}
    for e in entries:
        buckets[classify(e)].append(e)

    for b in buckets.values():
        b.sort(key=lambda e: (SEV_ORDER.get(e["severity"], 4), e["id"]))

    lines = []
    lines.append("# Operator Console")
    lines.append("")
    lines.append(
        "> **GENERATED FILE — do not hand-patch.** Produced by "
        "`scripts/generate_operator_console.py` from `GOVERNANCE_GAP_LOG.md`'s "
        f"live entries on every governance scan. Regenerated "
        "{count} open/in-progress entries into three sections, ranked by "
        "**blocks operator**, not severity. To change what appears here, fix "
        "the entry in GOVERNANCE_GAP_LOG.md or the classification regex in the "
        "generator script — never this file directly."
        .replace("{count}", str(len(entries)))
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append(f"## 1. Decisions blocked on Earl ({len(buckets['blocked'])})")
    lines.append("")
    lines.append(
        "Nothing else in this project moves on these until the operator decides. "
        "Detected via explicit operator/Earl/sign-off/awaiting-direction language "
        "already present in the entry's own text."
    )
    lines.append("")
    if buckets["blocked"]:
        for e in buckets["blocked"]:
            lines.append(render_row(e))
    else:
        lines.append("_None currently detected._")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append(f"## 2. What is actually broken ({len(buckets['broken'])})")
    lines.append("")
    lines.append(
        "Something is silently wrong right now — a HALT, an undetected blind spot, "
        "a contradiction between claim and code, or HIGH/CRITICAL severity."
    )
    lines.append("")
    if buckets["broken"]:
        for e in buckets["broken"]:
            lines.append(render_row(e))
    else:
        lines.append("_None currently detected._")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append(f"## 3. What is accruing and its clock ({len(buckets['accruing'])})")
    lines.append("")
    lines.append(
        "Open, tracked, not currently blocking Earl and not flagged as actively "
        "broken — but still open, and the clock (epoch resets, n* thresholds, "
        "re-check triggers) keeps running. Default bucket: absence of "
        "blocked/broken signal, not absence of importance."
    )
    lines.append("")
    if buckets["accruing"]:
        for e in buckets["accruing"]:
            lines.append(render_row(e))
    else:
        lines.append("_None currently detected._")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        f"**Full record for every entry above:** `03_DECISIONS/GOVERNANCE_GAP_LOG.md`. "
        f"**Resolved/closed history:** `03_DECISIONS/GOVERNANCE_GAP_LOG_ARCHIVE.md`."
    )
    lines.append("")

    OUT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT}: blocked={len(buckets['blocked'])} broken={len(buckets['broken'])} "
          f"accruing={len(buckets['accruing'])} total={len(entries)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

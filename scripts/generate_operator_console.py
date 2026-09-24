#!/usr/bin/env python3
"""Generate OPERATOR_CONSOLE.md from GOVERNANCE_GAP_LOG.md's live (non-archived) entries.

T-420 (2026-08-05, console/archive split, agreed 2026-08-02 per
04_EXECUTION/SCALING_MANDATE_PARKED.md "What was already agreed"). Read-only
against GOVERNANCE_GAP_LOG.md -- never writes to it. Output is fully generated;
never hand-patch OPERATOR_CONSOLE.md for content, edit this script and re-run.

Ranking is "blocks operator" not severity (17 open gaps is not the problem;
not knowing which 3 need Earl specifically is). Every live entry lands in
exactly one of three sections, by mechanical priority:

  1. DECISIONS BLOCKED ON EARL -- entry carries an explicit
     `**Blocked-On-Operator:** YES` field.
  2. WHAT IS ACTUALLY BROKEN -- not blocked-on-operator, and entry carries
     an explicit `**Actively-Broken:** YES` field.
  3. WHAT IS ACCRUING AND ITS CLOCK -- everything else that is still open.
     Default bucket, not a weaker signal -- it means no explicit
     blocked/broken field was set, not that nothing matters.

T-423 (2026-08-06): classification was originally two regexes matching
prose vocabulary (BLOCKED_RE/BROKEN_RE below, removed this pass). That
approach put severity one layer up from where it belonged -- an entry's
narrative saying "operator" or "HALT" anywhere in its Discovery/Impact/
Resolution text was enough to misclassify it (e.g. GG-040 matched on
"DS sign-off" appearing in a historical/future-tense sentence, not a live
pending decision; GG-159/GG-162 matched BROKEN_RE despite neither being
"silently wrong right now"). The fix is a field, not a better regex:
`**Blocked-On-Operator:** YES` / `**Actively-Broken:** YES` are hand-set
per entry by whoever registers or triages the gap, defaulting to absent
(-> accruing) so most entries need no touch. If a bucket looks wrong, the
fix is to correct the field on the entry in GOVERNANCE_GAP_LOG.md -- never
to hand-edit the console output, and never to reintroduce a prose regex.
"""
import re
import subprocess
import sys
from pathlib import Path

GGL = Path("03_DECISIONS/GOVERNANCE_GAP_LOG.md")
OUT = Path("03_DECISIONS/OPERATOR_CONSOLE.md")
CLAIMS = Path("04_EXECUTION/SESSION_CLAIMS.md")

HEADER_RE = re.compile(r"^### (GG-\d+) — (.+)$", re.M)
STATUS_RE = re.compile(r"^\*\*Status:\*\* (.+?) · \*\*Severity:\*\* (.+)$", re.M)
BLOCKED_FIELD_RE = re.compile(r"^\*\*Blocked-On-Operator:\*\* YES\s*$", re.M)
BROKEN_FIELD_RE = re.compile(r"^\*\*Actively-Broken:\*\* YES\s*$", re.M)
TID_RE = re.compile(r"T-\d+")

SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNSPECIFIED": 4}

# T-570 (2026-09-23, retirement-mechanism): reuse, not reinvent -- both
# scripts already do exactly the work Section 0 below needs.
import check_register_parity as _crp  # noqa: E402
from retire_resolved_gaps import is_resolved_class  # noqa: E402


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
    # T-570: a resolved-class entry still sitting in the LIVE log is retirement
    # debt, not a live operator/broken/accruing concern -- it takes priority
    # over the other three fields so it never double-counts into them.
    if is_resolved_class(entry["token"]):
        return "retirement_debt"
    if BLOCKED_FIELD_RE.search(entry["block"]):
        return "blocked"
    if BROKEN_FIELD_RE.search(entry["block"]):
        return "broken"
    return "accruing"


def render_row(e):
    return f"- **[{e['id']}]** {e['title']} — `{e['token']}` · severity `{e['severity']}`"


def _git(*args):
    """Best-effort git call. Returns None on any failure -- Section 0's
    retirement-debt rollup is informational, never worth crashing console
    generation over a git hiccup."""
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, timeout=15
        )
    except Exception:
        return None


def merged_undeleted_branches():
    """Local branches that are already an ancestor of origin/main (fully
    landed) but still sitting around undeleted. Mirrors the detection logic
    in scripts/sweep_stray_branches.sh's landed-branch section (T-570) --
    read-only here, never deletes anything."""
    _git("fetch", "--quiet", "origin", "main")
    current = _git("rev-parse", "--abbrev-ref", "HEAD")
    current_branch = current.stdout.strip() if current and current.returncode == 0 else ""
    refs = _git("for-each-ref", "--format=%(refname)", "refs/heads")
    if refs is None or refs.returncode != 0:
        return []
    landed = []
    for ref in refs.stdout.splitlines():
        branch = ref[len("refs/heads/"):] if ref.startswith("refs/heads/") else ref
        if not branch or branch in ("main", current_branch):
            continue
        check = _git("merge-base", "--is-ancestor", ref, "origin/main")
        if check is not None and check.returncode == 0:
            landed.append(branch)
    return sorted(landed)


def prunable_worktrees():
    """Dry-run (`-n`) worktree-prune candidates -- administrative metadata for
    worktree directories already gone from disk. Never actually prunes."""
    out = _git("worktree", "prune", "-n", "-v")
    if out is None:
        return []
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


_NO_ROW_MARKERS = (
    "no APPROVALS_REGISTER.md row at all",
    "never mentioned in APPROVALS_REGISTER.md",
    "no OWN dedicated row",
)


def accepted_without_register_row():
    """ADR/APR docs that are resolved/ACCEPTED but have no register
    accountability at all -- reuses check_register_parity.py's rules 1, 2,
    and 5 rather than re-deriving them. Deliberately excludes rules 3/4
    (stale PENDING / premature ACCEPTED) since those are drift findings, not
    "missing row" findings, and are out of scope for this rollup."""
    if not _crp.REGISTER.exists():
        return []
    findings, _checked = _crp.collect_findings()
    return [f for f in findings if any(marker in f for marker in _NO_ROW_MARKERS)]


def unclosed_session_claims():
    """T-NNN tokens that have a claim row in SESSION_CLAIMS.md but no row
    whose free-text begins "CLOSED" -- i.e. still open per the log, whether
    actively in progress, PARKED, or awaiting merge. This is filing (reading
    the log), never adjudication of whether the work is actually done."""
    if not CLAIMS.exists():
        return []
    claimed: set[str] = set()
    closed: set[str] = set()
    for line in CLAIMS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        id_cell, desc_cell = cells[1], cells[2]
        ids = TID_RE.findall(id_cell)
        if not ids:
            continue
        for tid in ids:
            claimed.add(tid)
            if desc_cell.startswith("CLOSED"):
                closed.add(tid)
    return sorted(claimed - closed, key=lambda t: int(t.split("-")[1]))


def main():
    if not GGL.exists():
        print(f"ERROR: {GGL} not found", file=sys.stderr)
        return 1
    text = GGL.read_text()
    entries = parse_entries(text)
    unspecified_n = sum(1 for e in entries if e["severity"] == "UNSPECIFIED")

    buckets = {"retirement_debt": [], "blocked": [], "broken": [], "accruing": []}
    for e in entries:
        buckets[classify(e)].append(e)

    for b in buckets.values():
        b.sort(key=lambda e: (SEV_ORDER.get(e["severity"], 4), e["id"]))

    landed_branches = merged_undeleted_branches()
    prunable_wt = prunable_worktrees()
    no_row_findings = accepted_without_register_row()
    open_claims = unclosed_session_claims()

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
    if unspecified_n:
        lines.append(
            f"> **Severity debt:** {unspecified_n}/{len(entries)} live entries have no "
            "explicit severity (`UNSPECIFIED`) — sort order below is unreliable wherever "
            "it relies on severity for entries not in this backfill's scope. See GG-165."
        )
        lines.append("")
    lines.append("---")
    lines.append("")

    retirement_n = (
        len(buckets["retirement_debt"])
        + len(landed_branches)
        + len(prunable_wt)
        + len(no_row_findings)
        + len(open_claims)
    )
    lines.append(f"## 0. Overdue for retirement ({retirement_n})")
    lines.append("")
    lines.append(
        "Artifact CREATION (session claims, gap registration) is mechanical and "
        "enforced. Artifact RETIREMENT (archiving resolved gaps, deleting merged "
        "branches, closing register rows) is manual and gets forgotten -- it does "
        "not scale across a growing gap log and, per direct enumeration "
        "(`ls -d [0-9][0-9]_*`), **13** top-level department directories -- not "
        "the 12 this rollup's originating task assumed; `09_INTEGRATION_PATCHES` "
        "and `09_SECURITY_PRIVACY_COMPLIANCE` share the `09_` prefix. This "
        "section is filing, never adjudication: everything below is something "
        "already marked done elsewhere that hasn't been filed away yet. Nothing "
        "here is deleted or archived by generating this file "
        "(T-570, 2026-09-23)."
    )
    lines.append("")

    lines.append(f"**Unarchived resolved gaps ({len(buckets['retirement_debt'])})** "
                  "-- RESOLVED/CLOSED-AS-ARTIFACT entries still in the live "
                  "GOVERNANCE_GAP_LOG.md instead of the archive "
                  "(`scripts/retire_resolved_gaps.py`):")
    if buckets["retirement_debt"]:
        for e in buckets["retirement_debt"]:
            lines.append(render_row(e))
    else:
        lines.append("_None currently detected._")
    lines.append("")

    lines.append(f"**Merged-but-undeleted local branches ({len(landed_branches)})** "
                  "-- ancestors of origin/main, safe to `git branch -d` "
                  "(`scripts/sweep_stray_branches.sh --execute`):")
    if landed_branches:
        for b in landed_branches:
            lines.append(f"- `{b}`")
    else:
        lines.append("_None currently detected._")
    lines.append("")

    lines.append(f"**Prunable worktree metadata ({len(prunable_wt)})** "
                  "-- `git worktree prune -v` dry-run output:")
    if prunable_wt:
        for w in prunable_wt:
            lines.append(f"- {w}")
    else:
        lines.append("_None currently detected._")
    lines.append("")

    lines.append(f"**ADRs/APRs missing register accountability ({len(no_row_findings)})** "
                  "-- `scripts/check_register_parity.py` rules 1, 2, and 5. Rule 1 "
                  "requires EVERY APR to have its own row regardless of status "
                  "(so a non-ACCEPTED APR like APR-0034/0035/0036, still "
                  "DECISION REQUEST, correctly appears below); rules 2/5 apply "
                  "only to resolved (ACCEPTED-class) ADRs, requiring their own "
                  "dedicated row, not just a mention. Stale-PENDING/premature-"
                  "ACCEPTED drift findings (rules 3/4) are excluded, out of "
                  "scope for a \"missing entirely\" rollup:")
    if no_row_findings:
        for f in no_row_findings:
            lines.append(f"- {f}")
    else:
        lines.append("_None currently detected._")
    lines.append("")

    lines.append(f"**Session claims with no closure row ({len(open_claims)})** "
                  "-- `04_EXECUTION/SESSION_CLAIMS.md` T-NNN tokens with a claim "
                  "row but no row whose text starts \"CLOSED\" (includes work "
                  "that is genuinely still in flight, not only forgotten "
                  "closures -- this is a filing signal, not a verdict). "
                  "**Known noise (T-570):** the literal \"CLOSED —\" prefix is a "
                  "convention that hardened over time -- older rows often record "
                  "closure in free text that doesn't start with that word (e.g. "
                  "T-224's row ends \"...T-224 close (...)\" rather than opening "
                  "with CLOSED), so this list over-reports for anything claimed "
                  "before the convention was consistent. Treat entries below the "
                  "most recent ~50 rows as needing a manual skim, not a trusted "
                  "count, until a follow-on tightens the detection or the older "
                  "rows are normalized:")
    if open_claims:
        for tid in open_claims:
            lines.append(f"- `{tid}`")
    else:
        lines.append("_None currently detected._")
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
    print(f"Wrote {OUT}: retirement_debt={retirement_n} "
          f"blocked={len(buckets['blocked'])} broken={len(buckets['broken'])} "
          f"accruing={len(buckets['accruing'])} total={len(entries)}", file=sys.stderr)
    if unspecified_n:
        print(f"SEVERITY DEBT: {unspecified_n}/{len(entries)} live entries UNSPECIFIED "
              f"(see GG-165)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env bash
# ============================================================================
# check_id_collision.sh — pre-claim ID collision check (GG-107 root-cause fix,
# GG-169 revision)
#
# GG-107's recurring failure mode: a session claims a T-/GG-/ADR- ID that is
# already registered/in use elsewhere, because nothing checked before the
# claim was committed. GG-107's original fix (below, pre-GG-169) treated any
# textual mention of an ID anywhere in TODO_NEXT.md, SESSION_CLAIMS.md, or
# DECISION_LOG.md as a collision. That over-blocked: a TODO_NEXT.md backlog
# line or a DECISION_LOG.md narrative mention is a REFERENCE, not a CLAIM —
# but the broad grep couldn't tell the two apart, so citing an already
# pre-reserved or already-registered ID collided every time (GG-169: 8+
# collisions, twice in one run, including this file's own governing gap
# numbers).
#
# GG-169 fix, two rules:
#
#   Rule A — a GG-/ADR- id that already has a CANONICAL entry (a
#   "### GG-NNN" header in GOVERNANCE_GAP_LOG.md or its archive, or an
#   ADR-NNNN_*.md file) is never a collision, no matter how many places
#   mention it. Citing/working an already-registered gap or decision is
#   normal and expected — SESSION_CLAIMS.md history shows the same GG
#   number reappearing across dozens of rows as different sessions touch
#   it (GG-105: 21 rows, GG-045: 16, GG-113: 14). This is not the failure
#   GG-107 exists to catch.
#
#   Rule B — for everything else (T- ids always; GG-/ADR- ids with no
#   canonical entry yet, i.e. genuinely about to be freshly minted), the
#   only real collision signal is an ACTIVE claim: the id appearing in the
#   id/range column (2nd pipe field) of a SESSION_CLAIMS.md row. TODO_NEXT.md
#   and DECISION_LOG.md are narrative/reference documents, not claim
#   registries, and a bare mention there (including a pre-reserved,
#   unstaffed backlog line — exactly the case GG-169 was filed over) must
#   not block a session from claiming that id.
#
# This does not reopen the T-247 concurrent-grab race: that race is closed
# by claim_session.sh's fetch/rebase -> check -> push-with-retry sequence,
# not by this function's breadth of matching. Rule B still catches a
# genuinely concurrent claim the moment the first claimant's row lands in
# SESSION_CLAIMS.md's id column, which is the only place an active claim is
# actually recorded.
#
# Pure/offline: no git network calls, so it can be sourced and unit-tested
# without a live remote. claim_session.sh sources this and calls the function
# before appending a new claim row.
#
# check_id_collision <range> <repo_root> [exclude_row]
#   exclude_row (GG-322/T-595): a SESSION_CLAIMS.md line, matched whole-line and
#   exactly, ignored by Rule B. claim_session.sh passes the claimant's OWN
#   already-committed row when it re-verifies after a rebase, so the check sees
#   every OTHER session's claims without colliding with itself.
#   Prints one "COLLISION: <id> already appears in <file>" line per hit to
#   stderr. Returns 0 (no collision) or 1 (at least one collision found).
# ============================================================================

check_id_collision() {
  local range="$1" repo_root="$2" exclude_row="${3:-}"
  local ids
  ids="$(grep -oE '(T|GG|ADR)-[0-9]+' <<< "$range" | sort -u || true)"
  [ -z "$ids" ] && return 0

  local claims_file="$repo_root/04_EXECUTION/SESSION_CLAIMS.md"
  local gap_log="$repo_root/03_DECISIONS/GOVERNANCE_GAP_LOG.md"
  local gap_archive="$repo_root/03_DECISIONS/GOVERNANCE_GAP_LOG_ARCHIVE.md"

  local hit=0 id
  while IFS= read -r id; do
    [ -z "$id" ] && continue

    # Rule A: already-canonical GG-/ADR- ids are references, never collisions.
    case "$id" in
      GG-*)
        if { [ -f "$gap_log" ] && grep -qE "^### ${id}([^0-9]|\$)" "$gap_log"; } || \
           { [ -f "$gap_archive" ] && grep -qE "^### ${id}([^0-9]|\$)" "$gap_archive"; }; then
          continue
        fi
        # GG-236: the two greps above only see the gap log as checked out on
        # THIS branch (origin/main as of claim_session.sh's last fetch/pull).
        # A GG number already given a canonical header on a pushed-but-
        # unlanded session branch is invisible to them — this exact blind
        # spot predicted, and then still failed to prevent, T-513's GG-237
        # near-collision (see GOVERNANCE_GAP_LOG.md GG-162/GG-236/GG-237).
        # Close it by also checking every branch tip (local heads + fetched
        # remote-tracking refs) for the same header — a live snapshot of
        # each branch's current gap log, not a commit-history walk, so a
        # since-renumbered/removed id on some stale branch doesn't false-
        # positive forever. Guarded on being a real git repo so this stays
        # offline-testable per this file's own docstring: the existing
        # fixture-dir tests pass a bare tmp_path with no .git, and must
        # continue to no-op here exactly as before.
        if git -C "$repo_root" rev-parse --git-dir > /dev/null 2>&1; then
          local branch_refs match_ref
          branch_refs="$(git -C "$repo_root" for-each-ref --format='%(refname)' refs/heads refs/remotes 2>/dev/null)"
          if [ -n "$branch_refs" ]; then
            # shellcheck disable=SC2086  # word-splitting refs into args is intended
            # `|| true` matters under `set -euo pipefail`: git grep exits 1
            # (no match) on the common no-collision path, and pipefail would
            # otherwise propagate that through `| head -1` into this bare
            # assignment and abort the caller before the empty-match check
            # below ever runs.
            match_ref="$(git -C "$repo_root" grep -lE "^### ${id}([^0-9]|\$)" $branch_refs -- \
              03_DECISIONS/GOVERNANCE_GAP_LOG.md 03_DECISIONS/GOVERNANCE_GAP_LOG_ARCHIVE.md 2>/dev/null | head -1 || true)"
            if [ -n "$match_ref" ]; then
              echo "COLLISION: ${id} already has a canonical header on unlanded branch '${match_ref%%:*}' (not yet on this checkout's gap log — GG-236)" >&2
              hit=1
              continue
            fi
          fi
        fi
        ;;
      ADR-*)
        if compgen -G "$repo_root/03_DECISIONS/${id}_*.md" > /dev/null 2>&1; then
          continue
        fi
        ;;
    esac

    # Rule B: real collision = an active claim in SESSION_CLAIMS.md's own
    # id/range column (field 3 of a "| ts | ids | focus |" row), not a
    # mention anywhere else.
    if [ -f "$claims_file" ] && \
       awk -F'|' -v skip="$exclude_row" '$0 != skip && NF>=3{print $3}' "$claims_file" | grep -qE "(^|[^0-9A-Za-z])${id}([^0-9]|\$)"; then
      echo "COLLISION: ${id} already appears in ${claims_file#"$repo_root"/} (active claim)" >&2
      hit=1
    fi
  done <<< "$ids"
  return "$hit"
}

#!/usr/bin/env bash
# ============================================================================
# check_id_collision.sh — pre-claim ID collision check (GG-107 root-cause fix)
#
# GG-107's recurring failure mode: a session claims a T-/GG-/ADR- ID that is
# already registered/in use elsewhere (TODO_NEXT.md, a prior SESSION_CLAIMS.md
# row, or DECISION_LOG.md), because nothing checked before the claim was
# committed. Recurred repeatedly (GG-109->GG-110, GG-111->GG-112, and this
# session's own T-352/T-353 collision with UNWIND_PLAN.md's Window B).
#
# Pure/offline: no git network calls, so it can be sourced and unit-tested
# without a live remote. claim_session.sh sources this and calls the function
# before appending a new claim row.
#
# check_id_collision <range> <repo_root>
#   Prints one "COLLISION: <id> already appears in <file>" line per hit to
#   stderr. Returns 0 (no collision) or 1 (at least one collision found).
# ============================================================================

check_id_collision() {
  local range="$1" repo_root="$2"
  local ids
  ids="$(grep -oE '(T|GG|ADR)-[0-9]+' <<< "$range" | sort -u || true)"
  [ -z "$ids" ] && return 0

  local registries=(
    "$repo_root/04_EXECUTION/TODO_NEXT.md"
    "$repo_root/04_EXECUTION/SESSION_CLAIMS.md"
    "$repo_root/03_DECISIONS/DECISION_LOG/DECISION_LOG.md"
  )

  local hit=0 id f
  while IFS= read -r id; do
    [ -z "$id" ] && continue
    for f in "${registries[@]}"; do
      [ -f "$f" ] || continue
      if grep -qE "(^|[^0-9A-Za-z])${id}([^0-9]|\$)" "$f"; then
        echo "COLLISION: ${id} already appears in ${f#"$repo_root"/}" >&2
        hit=1
      fi
    done
  done <<< "$ids"
  return "$hit"
}

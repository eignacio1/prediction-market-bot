#!/usr/bin/env bash
# ============================================================================
# vps_deploy.sh — VPS-side deploy (W67.3 / T-813). GitHub Actions at $0.
#
# Replaces .github/workflows/deploy.yml's push trigger. Run from cron on the VPS
# (deploy/cron.conf: every 5 minutes, off :00/:30). It does what deploy.yml did,
# in the same order, with the same rules:
#
#   fetch origin/main -> nothing new? exit quietly
#   docs-only push (deploy.yml's paths-ignore list)  -> heal dirty tree, ff-pull, NO restart
#   anything else -> approval-path gate (T-327) on the NEW code in a scratch worktree,
#                    FAIL-CLOSED (red = nothing is pulled) ->
#                    dirty-tree guard (GG-130) -> ff-pull ->
#                    scripts/deploy_restart_policy.py (GG-432, unchanged) ->
#                    restart pmbot-web-dashboard always, t4-mlb only if the policy says so ->
#                    verify HEAD + ActiveEnterTimestamp.
#
# W72.3 (GG-661/GG-668): a skipped t4-mlb restart writes a pending marker (scripts/ops/deploy_truth.py)
# and every tick retries it, so the restart fires at the first no-live-game tick instead of waiting for
# an unrelated deploy. Every outcome also writes $STATE_DIR/deploy_status.json, which the governance scan
# reads (alarm, not log-only). Not changed: the restart policy rules, dirty-tree roots, the gate.
#
# Idempotent and lock-protected (flock). A red gate records the rejected SHA so the
# same commit is not re-tested every 5 minutes; a new commit on main re-arms it.
# Every run that finds something to do appends one line to logs/vps_deploy.log and one
# JSON record (incl. the t4-mlb decision) to logs/vps_deploy_decisions.jsonl.
#
# Env overrides exist for the test suite only (tests/test_vps_deploy_script.py):
#   PMBOT_DIR PMBOT_PYTHON PMBOT_SYSTEMCTL PMBOT_GATE_CMD PMBOT_STATE_DIR PMBOT_REMOTE_REF
# ============================================================================
set -uo pipefail

PROJ="${PMBOT_DIR:-/opt/prediction-market-bot}"
PYTHON="${PMBOT_PYTHON:-$PROJ/venv/bin/python}"
SYSTEMCTL="${PMBOT_SYSTEMCTL:-systemctl}"
STATE_DIR="${PMBOT_STATE_DIR:-/var/lib/pmbot-deploy}"
REMOTE_REF="${PMBOT_REMOTE_REF:-origin/main}"
REMOTE_NAME="${REMOTE_REF%%/*}"
REMOTE_BRANCH="${REMOTE_REF#*/}"
GATE_TESTS=(tests/test_approval_path_invariants.py tests/test_golden_replay.py)

# Same list as deploy.yml's paths-ignore (verified-non-code governance directories).
DOCS_ONLY_ROOTS=(03_DECISIONS/ 04_EXECUTION/ 11_MEMORY_HANDOFF/ 00_ADMIN/ 02_ARCHITECTURE_DESIGN/
                 05_RESEARCH_EXPERIMENTS/ 07_TEST_VALIDATION_EVIDENCE/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/)
# Tracked files under these roots are cron-regenerated runtime output (GG-130).
REGEN_ROOTS=(exp_output/ data/ logs/ models/)

LOG="$PROJ/logs/vps_deploy.log"
DECISIONS="$PROJ/logs/vps_deploy_decisions.jsonl"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$LOG"; }

record() {  # record <outcome> <before> <after> <t4_verdict> <detail>
  "$PYTHON" - "$DECISIONS" "$@" <<'PY' 2>/dev/null || true
import json, sys, datetime
path, outcome, before, after, verdict, detail = sys.argv[1:7]
rec = {"ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
       "outcome": outcome, "before": before, "after": after,
       "t4_mlb_verdict": verdict, "detail": detail}
with open(path, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(rec) + "\n")
PY
  "$PYTHON" "$PROJ/scripts/ops/deploy_truth.py" --proj "$PROJ" --state-dir "$STATE_DIR" status \
    --outcome "$1" --detail "${5:-}" >/dev/null 2>&1 || true
}

retry_pending_t4() {  # GG-661: restart t4-mlb once no game is live, if an earlier restart was skipped
  [ -f "$STATE_DIR/t4_pending_restart.json" ] || return 0
  local out verdict head
  out="$(mktemp)"; head="$(git rev-parse HEAD)"
  GITHUB_OUTPUT="$out" python3 scripts/deploy_restart_policy.py --pending >> "$LOG" 2>&1 || true
  verdict="$(sed -n 's/^verdict=//p' "$out" | tail -1)"; rm -f "$out"
  if [ "$verdict" = "restart" ]; then
    if "$SYSTEMCTL" restart t4-mlb >> "$LOG" 2>&1; then
      rm -f "$STATE_DIR/t4_pending_restart.json"
      log "pending t4-mlb restart done at ${head:0:8}"
      record pending_restart_done "$head" "$head" restart "t4-mlb restarted by pending-restart retry"
    else
      log "ERROR: pending t4-mlb restart failed"; record restart_failed "$head" "$head" restart "t4-mlb pending retry"
    fi
  else
    "$PYTHON" "$PROJ/scripts/ops/deploy_truth.py" --proj "$PROJ" --state-dir "$STATE_DIR" marker set \
      --verdict "${verdict:-policy_failed}" --sha "$head" --reason "pending retry still blocked" >/dev/null 2>&1 || true
  fi
}

is_docs_only() {  # stdin: changed paths, one per line. exit 0 iff every path is under a docs root
  local f root hit
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    hit=0
    for root in "${DOCS_ONLY_ROOTS[@]}"; do
      case "$f" in "$root"*) hit=1; break ;; esac
    done
    [ "$hit" -eq 1 ] || return 1
  done
  return 0
}

heal_dirty_tree() {  # GG-130 guard, identical to deploy.yml. exit 1 = unexpected tracked edits.
  local dirty line fpath root matched
  local -a healed=() unexpected=()
  dirty="$(git status --porcelain --untracked-files=no 2>/dev/null || true)"
  [ -z "$dirty" ] && return 0
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    fpath="${line:3}"
    matched=0
    for root in "${REGEN_ROOTS[@]}"; do
      case "$fpath" in "$root"*) matched=1 ;; esac
    done
    if [ "$matched" -eq 1 ]; then
      git checkout -- "$fpath" && healed+=("$fpath")
    else
      unexpected+=("$line")
    fi
  done <<< "$dirty"
  [ "${#healed[@]}" -gt 0 ] && log "AUTO-HEALED (GG-130): ${#healed[@]} tracked cron-output file(s) reset: ${healed[*]:0:5}"
  if [ "${#unexpected[@]}" -gt 0 ]; then
    log "ERROR: tracked files modified outside cron-output roots; pull aborted: ${unexpected[*]}"
    return 1
  fi
  return 0
}

run_gate() {  # approval-path suites against the NEW commit, in a scratch worktree
  local after="$1" wt rc
  if [ -n "${PMBOT_GATE_CMD:-}" ]; then
    ( cd "$PROJ" && bash -c "$PMBOT_GATE_CMD" ) >> "$LOG" 2>&1
    return $?
  fi
  wt="$(mktemp -d /tmp/pmbot-deploy-gate.XXXXXX)"
  git worktree add --detach -q "$wt" "$after" >> "$LOG" 2>&1 || { rm -rf "$wt"; return 1; }
  (
    cd "$wt" || exit 1
    export PYTHONPATH="$wt/src"
    # Fail closed if the editable install would shadow the worktree: the gate must test the NEW code.
    resolved="$("$PYTHON" -c 'import prediction_market_bot,os;print(os.path.dirname(prediction_market_bot.__file__))')"
    case "$resolved" in "$wt"/*) ;; *) echo "gate imports $resolved, not $wt/src -- refusing to certify"; exit 1 ;; esac
    "$PYTHON" -m pytest -q -p no:cacheprovider "${GATE_TESTS[@]}"
  ) >> "$LOG" 2>&1
  rc=$?
  git worktree remove --force "$wt" >> "$LOG" 2>&1 || rm -rf "$wt"
  git worktree prune >> "$LOG" 2>&1 || true
  return $rc
}

main() {
  mkdir -p "$STATE_DIR" "$PROJ/logs" 2>/dev/null || true
  if command -v flock >/dev/null 2>&1; then
    exec 9>"$STATE_DIR/deploy.lock"
    flock -n 9 || exit 0                    # another deploy is running
  else                                      # no flock (macOS test runs): mkdir is atomic
    mkdir "$STATE_DIR/deploy.lockdir" 2>/dev/null || exit 0
    trap 'rmdir "$STATE_DIR/deploy.lockdir" 2>/dev/null' EXIT
  fi

  cd "$PROJ" || exit 1
  local TMO=""; command -v timeout >/dev/null 2>&1 && TMO="timeout 90"   # absent on macOS test runs
  $TMO git fetch -q "$REMOTE_NAME" "$REMOTE_BRANCH" 2>>"$LOG" || {
    log "fetch failed; will retry next tick"; "$PYTHON" "$PROJ/scripts/ops/deploy_truth.py" --proj "$PROJ" --state-dir "$STATE_DIR" status \
      --outcome fetch_failed --detail "git fetch failed" >/dev/null 2>&1 || true; exit 0; }
  retry_pending_t4

  local before after
  before="$(git rev-parse HEAD)"
  after="$(git rev-parse "$REMOTE_REF")"
  if [ "$before" = "$after" ]; then
    # quiet tick: refresh the status file (keeps last_ok fresh) without a decision record
    "$PYTHON" "$PROJ/scripts/ops/deploy_truth.py" --proj "$PROJ" --state-dir "$STATE_DIR" status \
      --outcome noop >/dev/null 2>&1 || true
    exit 0
  fi
  # Local is ahead of / diverged from origin: never deploy backwards.
  if ! git merge-base --is-ancestor "$before" "$after"; then
    log "HEAD $before is not an ancestor of $REMOTE_REF $after; refusing to deploy"
    exit 0
  fi
  [ "$(cat "$STATE_DIR/rejected_sha" 2>/dev/null || true)" = "$after" ] && exit 0

  log "deploy start: ${before:0:8} -> ${after:0:8}"

  if git diff --name-only "$before" "$after" | is_docs_only; then
    heal_dirty_tree || { record dirty_tree_abort "$before" "$after" none "tracked edits outside cron roots"; exit 1; }
    git merge --ff-only -q "$after" >> "$LOG" 2>&1 || { log "ff-merge failed"; record pull_failed "$before" "$after" none "docs-only ff failed"; exit 1; }
    log "docs-only: pulled to ${after:0:8}; no gate, no restart"
    record docs_only "$before" "$after" not_applicable "no code path changed"
    exit 0
  fi

  if ! run_gate "$after"; then
    echo "$after" > "$STATE_DIR/rejected_sha"
    log "GATE RED for ${after:0:8}: nothing pulled (fail-closed). Re-armed by the next commit on main."
    record gate_red "$before" "$after" none "approval-path gate failed; see logs/vps_deploy.log"
    exit 1
  fi

  heal_dirty_tree || { record dirty_tree_abort "$before" "$after" none "tracked edits outside cron roots"; exit 1; }
  git merge --ff-only -q "$after" >> "$LOG" 2>&1 || { log "ff-merge failed"; record pull_failed "$before" "$after" none "ff failed"; exit 1; }

  local out verdict_line verdict restart services
  out="$(mktemp)"
  GITHUB_OUTPUT="$out" python3 scripts/deploy_restart_policy.py --before "$before" --after "$after" >> "$LOG" 2>&1 || true
  restart="$(sed -n 's/^restart_t4=//p' "$out" | tail -1)"
  verdict="$(sed -n 's/^verdict=//p' "$out" | tail -1)"
  rm -f "$out"
  [ -n "$verdict" ] || { verdict="policy_failed"; restart="false"; }   # fail safe: do not restart t4-mlb blind

  services="pmbot-web-dashboard"
  [ "$restart" = "true" ] && services="t4-mlb $services"
  local TRUTH=("$PYTHON" "$PROJ/scripts/ops/deploy_truth.py" --proj "$PROJ" --state-dir "$STATE_DIR")
  case "$verdict" in
    skip_live_game|skip_game_state_unknown|policy_failed)
      "${TRUTH[@]}" marker set --verdict "$verdict" --sha "$after" --reason "restart skipped at deploy ${after:0:8}" >/dev/null 2>&1 || true ;;
  esac
  log "t4-mlb restart decision: ${verdict}; restarting: ${services}"
  # shellcheck disable=SC2086
  "$SYSTEMCTL" restart $services >> "$LOG" 2>&1 || { log "ERROR: systemctl restart failed"; record restart_failed "$before" "$after" "$verdict" "$services"; exit 1; }

  local pull_epoch svc ts ep rc=0
  pull_epoch="$(date +%s)"
  for svc in $services; do
    ts="$("$SYSTEMCTL" show "$svc" --property=ActiveEnterTimestamp --value 2>/dev/null || true)"
    ep="$(date -d "$ts" +%s 2>/dev/null || echo 0)"
    if [ "$ep" -lt "$((pull_epoch - 120))" ]; then
      log "ERROR: $svc did not restart within 2 minutes; deploy did not take effect on the running process"
      rc=1
    fi
  done
  [ "$restart" = "true" ] && [ $rc -eq 0 ] && "${TRUTH[@]}" marker clear >/dev/null 2>&1
  log "deploy done: HEAD $(git log -1 --oneline) rc=$rc"
  record "$([ $rc -eq 0 ] && echo deployed || echo verify_failed)" "$before" "$after" "$verdict" "$services"
  exit $rc
}

main "$@"
exit $?

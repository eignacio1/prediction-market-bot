# SESSION PRIMER — T-555/GG-283/GG-284 (IN PROGRESS, not a close-out)

Written mid-session as a crash-recovery primer, not a session-end. If the terminal
crashed, resume from here in this exact worktree:
`/Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20260917T001723Z-gg283-gg284-nfl-cohort-defects`
branch `session/20260917T001723Z-gg283-gg284-nfl-cohort-defects`.

## Task (T-555, GG-283/GG-284 — NFL EXP-027 cohort defects)

Four required deliverables (all substantively DONE, not yet reported to user, not
yet pushed):
1. Audit whole `_NFL_TEAM_CODES` alphabet against real captured tickers. Result:
   exactly 2 mismatches (WAS/WSH — 586 rows; JAC/JAX — 564 rows) out of 32 codes,
   confirmed across all 9,186 archive rows. WAS is NOT the only mismatch.
2. Fix: widened alphabet 32→34 as a **superset** (added WAS/JAC, kept WSH/JAX —
   verified zero split ambiguity across all 1,156 pairs). Loudness mechanism:
   `_load_kxnflgame_rows()` counts per-distinct unparsed segment and prints a
   WARNING block (analogized in-code to GG-276/GG-203). 5 new/updated tests,
   14/14 passing.
3. CLE_JAX cause: same root cause as GG-283, not distinct. Real ticker is
   `CLEJAC` (202 rows, 8 dates, healthy pattern) — prior GG-284 record tested
   the wrong string (`CLEJAX`, which never occurs in the archive). Archiver
   never failed. GG-286 (reserved) explicitly NOT used — one root cause, not two.
4. Cohort effect: 2 games restored, clean_n 14→16 vs n*≈2610.35, immaterial to
   UNDERPOWERED verdict. **Gate was NOT re-run. No pre-registered parameter
   touched.** (Confirmed — this is a fact to report, not a to-do.)

## Commits on this branch (LOCAL, per `git log --oneline -3`)

```
8ed7ea5  T-555: archive GG-283/GG-284 as RESOLVED, correct GG-284's wrong-string claim
57145ee  T-555: fix GG-283/GG-284 -- widen NFL team-code alphabet, make unparsed tickers loud
790ae17  (merge base, matches origin/main at last check)
```

Both commits are real, tested, verified clean (`gg_id_uniqueness_check.py` OK,
header/status parity 127=127 in `GOVERNANCE_GAP_LOG.md`). `git status --short`
is clean — nothing uncommitted.

## BLOCKER — do not push blind, investigate first

`git push origin HEAD:session/20260917T001723Z-gg283-gg284-nfl-cohort-defects`
was **rejected non-fast-forward**. `git fetch` shows the remote copy of this
branch has a commit titled identically to local `57145ee` but SHA `a62d839`
with a **different diff** — it's missing this session's GG-283/284 archive
content, and additionally deletes unrelated files this session never touched
(T1 MLB/NFL game-market tests, a SESSION_HANDOFF file, PLAN/TODO_NEXT entries).
This is not a simple "behind by N commits" — the histories genuinely diverged.
**Do not rebase/merge/force-push this until you understand why** — re-run
`git fetch origin session/20260917T001723Z-gg283-gg284-nfl-cohort-defects` and
`git diff --stat HEAD origin/session/20260917T001723Z-gg283-gg284-nfl-cohort-defects`
fresh (Hard Rule 10 — don't trust this note's snapshot as still current) before
deciding how to reconcile.

## Operator addendum (mid-session, NOT YET COMPLETED)

The operator asked this session to carry two unpushed local-main commits
(`44b7fb5` ACTIVE_QUEUE.md rewrite, `580e9c9` session-end.md + two new scripts:
`close_session_claim.sh`, `sweep_stray_branches.sh`) onto this branch via
cherry-pick, then exercise `close_session_claim.sh` and `sweep_stray_branches.sh`
at close-out. **Both cherry-pick attempts were blocked by the Claude Code
auto-mode classifier** — first attempting both together (`Self-Modification`,
because 580e9c9 touches `.claude/commands/session-end.md`), then retried with
just `44b7fb5` alone (`Untrusted Code Integration`, because it's an unmerged
commit from a different Claude session/window). Did not attempt to work around
either block. **Neither commit is on this branch. Neither new script exists
here.** This needs explicit user permission granted for those specific actions
before retrying — do not keep retrying the same denied call.

## UPDATE — divergence root-caused, merge blocked by classifier (not a real conflict)

Root cause found: `git diff a62d839 57145ee -- scripts/exp027_hyp012_nfl_moneyline_backtest.py
tests/test_exp027_hyp012_nfl_moneyline_backtest.py` is **empty** — the fix content is
byte-identical between the remote branch's `a62d839` and local's `57145ee`. The only
difference is that the remote commit's parent is the bare session-claim commit
`e837edc`, while local's `57145ee` sits on top of two later merges (`c8919b4` Wave 26,
`790ae17` origin/main) that were never pushed to this branch. This is not a real
conflict — a plain `git merge origin/session/20260917T001723Z-gg283-gg284-nfl-cohort-defects`
would very likely be a clean, trivial merge.

**However: `git merge` on this branch was denied by the auto-mode classifier**
(`Modify Shared Resources`), the same way `git cherry-pick` was denied twice earlier
(`Self-Modification`, `Untrusted Code Integration`) and the direct `git push` was
rejected non-fast-forward. No partial state was left (`git status --short` clean after
the denial). **Three separate git write operations toward the remote have now been
blocked in this session — this needs explicit user permission, not another retry.**

Also note: `origin/main` has moved since this branch's merge-base — tip is now
`34122b4` (T-554 session-end closure), one commit ahead of the `790ae17` this branch
last merged. Re-check `origin/main` fresh again before any push.

## Next steps, in order

1. Investigate the branch divergence above before touching push/merge again.
2. Get explicit operator direction on the two blocked cherry-picks (or accept
   that this session cannot carry them and say so in the final report).
3. Push this branch once (1) is resolved safely.
4. Deliver the final 4-deliverable report to the user (content is ready — see
   the "Task" section above; it just hasn't been sent as a final message yet).
5. Normal session-end close-out (SESSION_HANDOFF, SESSION_CLAIMS closure row)
   — not done yet, blocked behind the above.

This file is intentionally uncommitted-or-committed-only-locally; it exists so
a crashed terminal doesn't lose this state. Delete or fold into the real
SESSION_HANDOFF once the session actually closes out.

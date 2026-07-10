# SESSION HANDOFF — 2026-07-10 (Workstream C1/C2 — approval-path test hardening)

**Worktree/branch:** isolated worktree `20260710T151127Z-workstream-b-edge-sign`
**Trigger:** Operator redirected work from Workstream B (T-322/323/324, blocked on a concurrent session's Workstream A) to Workstream C: "shift correctness LEFT (stop producing contaminated bets) — the GG-077/087 bug classes become impossible to ship silently. This is the item that most directly answers 'will cracks get flagged BEFORE they hit the bet stream,' which today they do not." Session ended on operator instruction to stop before T-327 due to token budget.

---

## Status

- **Phase:** 6/7 ACTIVE (unchanged)
- **Tests:** 2412 passed / 30 skipped (up from 2405/30 — +7 new tests, zero regressions)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — unchanged, no deploy this session (test-only additions, nothing deployed)
- **Paper bets:** MLB 169/30 resolved, NBA 158/30 (frozen/historical) — unchanged, no bet-stream code touched

---

## Strategic Decisions This Session

| Decision | Rationale | Canonical Reference | Owner |
|---|---|---|---|
| Pin T4's inline direction-derivation block via a literal source-text match against `run_t4_mlb_live.py`, rather than importing it | The logic isn't independently importable; a copy-and-hope test would silently drift from production. A source-drift pin fails loudly if the production block changes without the test being updated. | DECISION_LOG.md 2026-07-10 | Claude |
| Golden-replay harness explicitly replicates the forecast-field merge (`model_p`/`edge`/`gross_edge`) that both real T1/T4 callers perform post-approval, rather than importing a shared helper | No such helper exists — both call sites (`run_mlb_paper_trade.py:946-951`, `run_t4_mlb_live.py:1069-1071`) inline the merge. Documenting and replicating it in the test is the correct fix; extracting a new shared helper was out of scope for a test-hardening task. | DECISION_LOG.md 2026-07-10 | Claude |
| T-327 deferred to next session, not started | Operator: "Do not move on to T-327, we have no more tokens." T-325/T-326 are both functionally complete and independently valuable even without T-327 wired in yet. | This handoff | Operator |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T-325 — approval-path property tests | `tests/test_approval_path_invariants.py` (new, 287 lines). Hypothesis-based properties: direction symmetry (GG-087), fee-sign invariance (GG-077), no-double-flip edge-frame invariance. Verified failing on pre-fix commits, passing on HEAD. |
| T-326 — golden-replay harness | `tests/golden/*.json` × 6 (new) + `tests/test_golden_replay.py` (new, 195 lines). Replays real `RiskEngine.evaluate_forecast()` → `PaperTrader.open_position()` against frozen fixtures (T1 YES, T1 NO/GG-077, insufficient-edge reject, min-bet-floor reject, drawdown kill-switch, T4 NO/GG-087 override). Verified failing against `0797c32^` (GG-077 pre-fix), passing on HEAD. |
| `pyproject.toml` | Added `hypothesis>=6.100.0,<7.0` to dev deps; registered `property`/`golden` pytest markers. |
| Regression check | Full suite: `2412 passed, 30 skipped, 1 pre-existing unrelated warning, 120.63s` — +7 over the 2405 baseline, exactly matching the 7 new tests, no other file affected. |
| DECISION_LOG.md | Entry appended documenting both tasks' design decisions and verification method (Hard Rule 7). |
| TODO_NEXT.md / MEMORY_BANK.md | Updated with session summary and T-327 deferred status. |

**T-327 (pre-deploy gate wiring T-325+T-326 into `.github/workflows/deploy.yml`) is NOT started** — depends on T-325+T-326, both now complete, so next session can begin immediately with no further investigation needed.

---

## ONE THING PENDING

**Wire `tests/test_approval_path_invariants.py` and `tests/test_golden_replay.py` into `.github/workflows/deploy.yml`** so that any diff touching `paper_trader.py` / `run_*_paper_trade.py` / `run_t4_mlb_live.py` / `risk.py` fails deploy unless both suites (`-m "property or golden"` or equivalent marker selection) run green. This is T-327, the last item in Workstream C, and closes the loop this workstream exists for: GG-077/GG-087-class bugs currently reach the bet stream before any automated gate catches them — T-325/T-326 built the tests, T-327 makes CI actually enforce them.

**Also pending, not yet done:** commit and push this session's new files (`tests/test_approval_path_invariants.py`, `tests/golden/*.json` × 6, `tests/test_golden_replay.py`, `pyproject.toml`, `DECISION_LOG.md`, `TODO_NEXT.md`, `MEMORY_BANK.md`, this handoff). Nothing has been pushed yet — do this as the final action of this session, immediately after this handoff is written.

---

## Resume Command

```
cd /Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20260710T151127Z-workstream-b-edge-sign
git log --oneline -5
cat 04_EXECUTION/.last_session_checkpoint
```

Read `04_EXECUTION/TODO_NEXT.md`'s top entry (2026-07-10 Workstream C1/C2), then `.github/workflows/deploy.yml` to see current CI wiring, then start T-327: add both new test files to whatever test-selection step already runs in that workflow (check for an existing `pytest` invocation and marker filter), and add a job/step that fails if either suite doesn't run or doesn't pass on a diff touching the four approval-path files.

---

## Next Session Primer

Read `tests/test_approval_path_invariants.py` and `tests/test_golden_replay.py` (both complete, both passing) to understand what T-327 needs to gate on, then open `.github/workflows/deploy.yml` and add the fail-closed check — a path-filter on the four approval-path files plus a required green run of `pytest -m "property or golden"` (or equivalent) before deploy proceeds. This is the last task in Workstream C; once merged, `git worktree remove` this session's worktree per the standard retirement flow.

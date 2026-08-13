# Active queue — Phase 1, abstraction repair

**Updated:** 2026-08-13 by the strategic window (Cowork: no SSH, no push — GG-154).
**Verified against `origin/main` = `0b42a04`** (cached ref; this window cannot `git fetch` — no credentials. Re-fetch and re-verify before trusting anything below).
**Gap log at write time: 57 entries / 46 OPEN** on `origin/main`; **58 / 47** on D's unmerged branch. Do not quote either — re-run `grep -cE "^### GG-[0-9]"` and `grep -cE "^\*\*Status:\*\* OPEN\b"`.
**Free IDs:** T-443+ · GG-175+ · ADR-0054+. (Taken: T-442, GG-174, ADR-0053.)

---

## STATUS — verified against commits, not summaries

| Block | Task | State | Evidence |
|---|---|---|---|
| **A** | Registry, boxes 1.1+1.3 | ✅ **MERGED** | `b636408`, PR #72 `bb42743`. Registered GG-173. |
| **B** | Replay baseline, boxes 1.6+1.7 | ✅ **MERGED** | `187ee94`, close-out `4336b4c`/`e13eec5`. |
| **C** | GG-172 + ADR-0053 | ✅ **MERGED** | `7cd9b5c`, close-out `999030b`/`2654c9c`. ADR-0053 correctly left **PROPOSED**. |
| **D** | Write path, boxes 1.2+1.4+1.5 | ⚠️ **DONE BUT NOT MERGED** | 7 commits on `origin/session/20260813T001221Z-phase1-write-path`, head `583e1db`. `git merge-base --is-ancestor <branch> origin/main` → **NOT MERGED**. The only T-442 commit on `main` is the *claim* row `0b42a04`. |

**D's work is sound — I checked it against source, not against its handoff:**

- `open_position()` keeps `player_name`/`player_id`/`kalshi_threshold` as optional defaulted params ✓. Positional order *did* change (`kalshi_ticker` moved to slot 2), but every caller in `src/`, `scripts/` and `tests/` uses keyword args — verified across all 13 call sites. Safe in-repo; latent hazard for any future positional caller.
- Vig cascade extracted to `_NO_DIRECTION_VIG_COEFFICIENT[(market_type, band)]` with `T4M-PROJ: 2.0`, `T1: 1.0`, missing-key fallthrough `0.0` — reproduces the old `else: -gross_edge` branch exactly ✓. All four branches preserved.
- **The one thing that could have silently re-priced the live book:** the new lookup keys on the *pair*, so a `None` market_type would miss the table and turn `-gross_edge - 2.0*vig` into `-gross_edge`. `paper_trader.py` line ~513 resolves `market_type or MarketType.MLB_PLAYER_PROP_HITS` first, so existing T4M-PROJ/T1 traffic hits the table. **Behavior-preserving, confirmed by reading the resolution line — not by trusting the coefficient table.**
- GG-166's three `_ticker_to_game_date(ticker, game_date)` call sites intact at `run_t4_mlb_live.py:1094,1160,1390` ✓, with a new regression test (`tests/test_t442_box14_gg166_regression.py`) asserting exactly that.
- `logic_epoch.py` untouched ✓. GG-174 registered (Polymarket hardcoded `nba` tag) and **not fixed** — register-and-stop honored ✓.

**Two things nobody has done yet, and they are cheap:**

1. **Not one Phase 1 box is checked.** 1.1 through 1.8 are all `[ ]` on `origin/main` *and* on D's branch, despite 1.1/1.3/1.6/1.7 being merged and complete. The plan's own rule — "a box is checked only when the artifact exists and is committed" — is satisfied for those four.
2. **Box 1.1's text is now actively wrong.** It reads "*`market_mapper.py` currently has no such thing*". A built the registry at `market_type_registry.py`, a different file — so the box describes a state that no longer exists and points at the wrong module. Box 1.5 still cites `L460/462/464`; D corrected that citation in the T-427 audit doc but not in the plan.

**Also carried forward, unresolved:** the stale zero-byte `.git/index.lock` in the shared main tree. `rm -f "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets/.git/index.lock"` if any terminal hits "Unable to create index.lock".

---

## HOW TO RUN

| Block | Terminal | Start when | Deliverable | Touches `src/`? | Tier |
|---|---|---|---|---|---|
| **G** | 1 | **now** | Merge D to `main`; check boxes 1.1–1.7; fix stale box text. | Merge only (no new edits) | STANDARD |
| **E** | 2 | **after G merges** | Re-run replay harness against refactored code. **Phase 1's exit gate.** | No | STANDARD |
| **F** | 3 | **after G merges** | CLAUDE.md corrections. Box 1.8. | No | MICRO |

**G runs alone and first** — it is a merge into shared `main`; nothing else should be moving `main` while it runs. **E and F then run at once** — E owns `scripts/`+`MARKET_EXPANSION_ACTION_PLAN.md` box 1.6, F owns `CLAUDE.md`. They share only `DECISION_LOG.md`, which is append-only per Hard Rule 7; commit path-scoped and re-read before writing (Hard Rule 10).

Letters are labels, not sequence — the "Start when" column is the ordering.

**Every block launches its own worktree.** GG-169 will false-positive the collision check on a pre-reserved ID; use the T-357/GG-113 manual workaround and note it in the claim row.

**Delete a block from this file when its window closes.**

---

# BLOCK G · Terminal 1 · Merge D, close the Phase 1 boxes

```
Read CLAUDE.md and run the full session-start protocol before anything else. Step 4 (VPS health) requires SSH — run it if you have a route and say explicitly whether you did or did not. That blind spot is GG-154.

PRE-FLIGHT:
  cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
  ls -la .git/index.lock 2>/dev/null && rm -f .git/index.lock   # stale 0-byte lock, safe to remove
  git fetch origin
  git log --oneline -1 origin/main                              # PASTE
  git status --porcelain | grep -v '^??'                        # PASTE — expect near-empty
STOP AND REPORT if git status shows modified tracked files you did not create. Per Hard Rule 10 do NOT stash, reset --hard, checkout -- , or clean -fd — any of those can permanently destroy a concurrent session's work (GG-101).

Claim as T-443, TIER: STANDARD, deliverable: "Merge T-442 (Phase 1 boxes 1.2/1.4/1.5) to main; check Phase 1 boxes 1.1-1.7; correct stale box text in MARKET_EXPANSION_ACTION_PLAN.md".

YOUR ONE DELIVERABLE: get D's branch onto main safely, then make the plan's checkbox state match reality. Nothing else.

CONTEXT — what happened. Blocks A (T-439), B (T-440) and C (T-441) are merged. Block D (T-442) completed all its work and ran session-end, but its branch was never merged:
  origin/session/20260813T001221Z-phase1-write-path   head 583e1db, 7 commits
  git merge-base --is-ancestor origin/session/20260813T001221Z-phase1-write-path origin/main   -> NOT an ancestor
The only T-442 commit on main is its claim row (0b42a04), which claim_session.sh pushes at session START. Verify all of this yourself before merging — do not take my word for it.

STEP 1 — MERGE D.
  git fetch origin
  git merge-base --is-ancestor origin/session/20260813T001221Z-phase1-write-path origin/main && echo "ALREADY MERGED - stop, re-scope this session" || echo "not merged, proceed"
  git log --oneline origin/main..origin/session/20260813T001221Z-phase1-write-path   # PASTE — expect 7 commits

Prefer a PR merge over a direct push to main, matching how A/B/C landed (PR #72 etc.). If you merge locally instead, rebase or merge origin/main into the branch FIRST, resolve conflicts, and re-run the full suite before pushing.

Expect conflicts in nav files only — DECISION_LOG.md, TODO_NEXT.md, MEMORY_BANK.md, GOVERNANCE_GAP_LOG.md. These are deliberately NOT merge=union (union would silently double their in-place edits), so resolve by hand and preserve BOTH sessions' content. The gap log is the one to watch: main has 57 headers / 46 OPEN, D's branch has 58 / 47 (D added GG-174). After merge you should have 58 / 47 — if you get 57 or 59, an entry was lost or duplicated. Assert it:
  grep -cE "^### GG-[0-9]" 03_DECISIONS/GOVERNANCE_GAP_LOG.md      # expect 58
  grep -cE "^\*\*Status:\*\*" 03_DECISIONS/GOVERNANCE_GAP_LOG.md   # must EQUAL the above
  grep -cE "^\*\*Status:\*\* OPEN\b" 03_DECISIONS/GOVERNANCE_GAP_LOG.md   # expect 47
PASTE all three.

STEP 2 — VERIFY THE MERGE DIDN'T CHANGE BEHAVIOR. Run, and paste:
  python3 -m pytest -q                          # baseline is 2,847 passed / 28 skipped / 0 failed (T-440, 2026-08-12, box 1.7). D added tests, so a HIGHER pass count with 0 failed is expected and fine. Any FAILURE is a stop condition.
  python3 scripts/assert_ledger_invariants.py   # ALARM-ONLY, exits 0 regardless — read the printed summary yourself, do not trust the exit code
Assertion A violations concentrated in epoch 12 are GG-170, already OPEN — do not re-register. A NEW assertion going from clean to violating is a stop condition; say so and register a T-number rather than fixing it.

STEP 3 — CHECK THE BOXES. In 04_EXECUTION/MARKET_EXPANSION_ACTION_PLAN.md, Phase 1. Every box 1.1 through 1.7 is currently "[ ]" even though the work is merged and committed. The plan's own rule is "a box is checked only when the artifact exists and is committed" — that condition is now met for 1.1-1.7. Before checking each one, VERIFY THE ARTIFACT EXISTS, do not check on the strength of a commit message:
  1.1 — src/prediction_market_bot/c5_execution/market_type_registry.py exists, MarketTypeCell is keyed (market_type, band), CellStatus.RULED_OUT requires reason + measured_date (enforced in __post_init__)
  1.2 — venue_adapter.py has fetch_markets(market_type) on the Protocol and all three adapters, with fetch_player_points_markets retained as a delegating shim
  1.3 — kalshi_client.py's SERIES_* constants resolve through the registry, and both legacy names still resolve to "KXNBAPTS" / "KXMLBHIT"
  1.4 — open_position() takes player_name/player_id/kalshi_threshold as optional defaulted params
  1.5 — the vig cascade is extracted to _NO_DIRECTION_VIG_COEFFICIENT with T4M-PROJ=2.0, T1=1.0, fallthrough 0.0
  1.6 — the corrected gate wording is landed verbatim (it already is, T-440) AND E has returned a verdict. **LEAVE 1.6 UNCHECKED** — the gate has not been RUN against refactored code yet. That is Block E. Checking it now would be checking a gate nobody passed.
  1.7 — 2,847/28/0 recorded (T-440). Re-check against your own STEP 2 run and update the figure with today's date if it moved.
So: check 1.1, 1.2, 1.3, 1.4, 1.5, 1.7. Leave 1.6 and 1.8 unchecked.

STEP 4 — CORRECT TWO STALE TEXTS, in the same file, nothing more:
  Box 1.1 reads "Market-type registry built (`market_mapper.py` currently has no such thing)". That parenthetical describes a pre-A state and points at the wrong module — the registry landed at c5_execution/market_type_registry.py, and market_mapper.py was not where it went. Rewrite to name the actual module and drop the stale "currently has no such thing".
  Box 1.5 cites "(L460/462/464)". Those line numbers were already off by one before D, and are now obsolete entirely since the cascade moved into _directional_edge(). D corrected this citation in T427_REPLAY_DETERMINISM_AUDIT.md (commit afcc76d) but not here. Replace the line-number citation with the function name.

DO NOT:
  - Do not check box 1.6. E owns that verdict.
  - Do not start box 1.8. F owns it.
  - Do not fix GG-174, GG-173, GG-170, or anything else you find. Register and stop (Hard Rule 11).
  - Do not bump logic_epoch. Phase 1 must not.
  - Do not change any kelly_fraction or any sizing. Four bands sit at 0.0 under ADR-0048 on ruin geometry (GG-135). Sizing needs its own ADR.
  - Do not promote scripts/assert_ledger_invariants.py to --strict. Alarm-only by operator decision.
  - Do not mark ADR-0053 ACCEPTED. It is PROPOSED pending operator sign-off.

REPORT BACK: the merge commit and full commit range, the three gap-log counts, the pytest tail, the invariant-suite summary, which boxes you checked and the artifact you verified for each, and — unprompted — WHAT YOU DID NOT CHECK.
```

---

# BLOCK E · Terminal 2, after G merges · Phase 1 exit gate — box 1.6 verdict

```
Read CLAUDE.md and run the full session-start protocol first. Step 4 needs SSH — say whether you ran it. GG-154.

PRECONDITION: Block G (T-443) merged, which means T-442's write-path refactor is on main. Verify, do not assume:
  cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
  ls -la .git/index.lock 2>/dev/null && rm -f .git/index.lock
  git fetch origin
  git merge-base --is-ancestor origin/session/20260813T001221Z-phase1-write-path origin/main && echo "D IS MERGED - proceed" || echo "*** D NOT MERGED - STOP ***"
If D is not merged, STOP AND REPORT. Running this gate against unrefactored code produces a pass that means nothing — it would compare the baseline to itself.

  scripts/new_session_worktree.sh phase1-exit-gate
  # cd into the printed path, then:
  git rebase origin/main || git merge --ff-only origin/main
  git log --oneline -1     # PASTE

Claim as T-444, TIER: STANDARD, deliverable: "Phase 1 exit gate — replay harness re-run against the refactored write path, box 1.6 verdict". GG-169 false-positive expected; manual workaround.

YOUR ONE DELIVERABLE: run the gate, report the verdict, check or fail box 1.6. You are the independent check on T-442.

DO NOT READ T-442's SESSION_HANDOFF OR ITS DECISION_LOG ENTRIES BEFORE FORMING YOUR OWN READ OF THE DIFF. A summary reproduces the executing window's framing, which is exactly what a review has to be independent of. Read the diff:
  git log --oneline origin/main -12
  git show 5a2360a --stat && git show 175fc7d --stat
Read them afterward if you want, to compare against what you found.

READ FIRST:
  05_RESEARCH_EXPERIMENTS/T427_REPLAY_DETERMINISM_AUDIT.md — the whole thing, including D's correction in commit afcc76d.
  04_EXECUTION/MARKET_EXPANSION_ACTION_PLAN.md box 1.6 — the corrected gate wording T-440 landed verbatim.
  T-440's re-baselined pre-refactor numbers (its SESSION_HANDOFF and the harness output it committed). THESE ARE YOUR COMPARISON POINT — the whole gate is "does the post-refactor run reproduce the pre-refactor run."

THE GATE: positions written under the CURRENT logic_epoch, replayed through the refactored path, reproduce every field open_position() writes, EXCEPT (a) kalshi_order_id / kalshi_order_status / kalshi_contracts, permanently excluded wherever the original shows a real submission (status != "local_only"); (b) position_id / entered_at / logic_epoch / approval_commit, pinned via harness-injected stored values. Everything else byte-for-byte, plus status for still-OPEN positions.

STEPS:
  1. Re-check logic_epoch.CURRENT_LOGIC_EPOCH. T-427 recorded 12 as of 2026-08-06 and Phase 1 must not bump it. If it moved, the gate's scope changed — say so loudly and stop.
  2. Run scripts/replay_harness_t427.py. Paste pass/fail/error counts and per-branch coverage verbatim.
  3. Compare against T-440's pre-refactor baseline.

WHAT PASS ACTUALLY MEANS — read before interpreting your own output:
  - The current-epoch subset must match T-440's PRE-refactor baseline EXACTLY. Same pass count, same fail count, same per-branch coverage. The refactor was behavior-preserving or it was not.
  - A FULL-LEDGER 100% PASS IS A RED FLAG, NOT A WIN. T-427's Class D finding: the vig-cascade formula changed three times across epochs 1-12, and those old formulas do not exist in the current checkout. Superseded-epoch positions CANNOT reproduce. If they suddenly do, your harness is not testing what you think it is. Investigate; do not celebrate.
  - All four cascade branches must still be exercised (T-427 Task 3: YES n=703, T4M-PROJ-NO n=1552, T1-NO n=450, else-fallthrough n=196). If a branch dropped to zero, D's extraction lost a path.

ONE SPECIFIC THING TO PROBE, because it is the highest-risk edge in the refactor and a passing aggregate could hide it: the extracted cascade now keys on the PAIR (market_type, band), where the old one keyed on band alone. paper_trader.py resolves `market_type or MarketType.MLB_PLAYER_PROP_HITS` before the lookup, which is what makes existing traffic land on the right coefficient. Confirm by construction, not by aggregate: assert that replayed T4M-PROJ NO positions still get coefficient 2.0 and T1 NO positions still get 1.0. A silent miss on that table turns "-gross_edge - 2.0*vig" into "-gross_edge" and would mis-price every NO bet on the only band placing bets. If the harness cannot see this directly, add a targeted check — this is worth the extra effort.

ALSO RUN AND REPORT: python3 scripts/assert_ledger_invariants.py — compare against the counts T-443 reported in Block G. If they disagree, THAT disagreement is your headline finding. An independent path disagreeing with the executing window's own numbers is exactly how GG-166 was caught.
Full pytest suite, paste the tail, compare against box 1.7's figure.

IF THE GATE FAILS: do not fix it. Report exactly which fields diverge on which positions, and whether the divergence concentrates in the CURRENT epoch (live regression — serious) or in SUPERSEDED epochs (expected Class D — not a defect). Register a T-number. Hard Rule 11.

BOX 1.6: check it only on a genuine pass. If it fails, leave it unchecked and write the failure into the box.

DO NOT: do not fix anything you find; do not bump logic_epoch; do not touch sizing or any kelly_fraction; do not promote the invariant suite to --strict; do not mark ADR-0053 ACCEPTED.

REPORT BACK: branch and full commit range, harness output verbatim, pre-vs-post baseline comparison, the coefficient probe result, invariant-suite counts vs G's, pytest tail, PASS or FAIL with reasoning, and — unprompted — WHAT YOU DID NOT CHECK.
```

---

# BLOCK F · Terminal 3, after G merges · Box 1.8 — CLAUDE.md correction

```
Read CLAUDE.md and run the session-start protocol first. Step 4 needs SSH — say whether you ran it.

PRECONDITION: Block G (T-443) merged.
  cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
  ls -la .git/index.lock 2>/dev/null && rm -f .git/index.lock
  git fetch origin && git log --oneline -1 origin/main   # PASTE
  scripts/new_session_worktree.sh phase1-claudemd-correction
  # cd in, then: git rebase origin/main ; git log --oneline -1   # PASTE

Claim as T-445, TIER: MICRO, deliverable: "Phase 1 box 1.8 — CLAUDE.md market-type-registry claim and efficiency-gradient departure corrected against post-Phase-1 source".

YOUR ONE DELIVERABLE: box 1.8. Two corrections. Nothing else — this is MICRO, and CLAUDE.md has twice drifted back into carrying decaying state (see its own remediation note at the top).

CORRECTION 1 — the market-type registry claim. CLAUDE.md's "Adding a new sport" section says adding NFL means "new market type registered in `market_mapper.py`".

That sentence is wrong in a NEW way as of Phase 1, and the update is not a simple "now it's true":
  - Before Block A it was false because no registry existed anywhere — market_mapper.py held four functions over a PlayerMarketKey NamedTuple.
  - Block A (T-439, commit b636408) built the registry at src/prediction_market_bot/c5_execution/market_type_registry.py — a DIFFERENT module. market_mapper.py is still not where market types get registered.
  - The registry is keyed on the PAIR (market_type, band), not on market_type alone. So "register a new market type" is not a single-axis act: a new market type arrives with a set of cells, one per band, each with its own status.
READ THE MERGED MODULE AND WRITE WHAT IS ACTUALLY TRUE. Do not assume A built what its prompt asked for — verify MarketTypeCell's fields and CellStatus's members directly, then write the sentence to match. Name the real module path.

CORRECTION 2 — the efficiency-gradient departure. CLAUDE.md's "Market efficiency gradient" section says the strategy is designed for markets that are NOT maximally efficient: thin, low-attention, slow price discovery. The coverage target expands toward moneyline and totals — the most-attended, most-efficiently-priced markets on the board. That is a departure from the stated strategy and CLAUDE.md acknowledges it nowhere.

Add the acknowledgement. Frame it as COVERAGE_TARGET_MATRIX.md does: expanding to game markets tests GENERALITY and should be EXPECTED to yield thinner edge than props; if it does, that is informative, not failure — but it has to be predicted in advance or the result is unfalsifiable. Mark it explicitly as an OPEN OPERATOR DECISION. Do not resolve it for him, and do not soften it into a note about "monitoring" — the point is that it is undecided.

CHECK BEFORE EDITING — CLAUDE.md is read first by every session regardless of protocol, and a stale main tree has clobbered prior work in this exact file:
  git fetch origin
  git merge-base --is-ancestor HEAD origin/main && echo "clean base" || echo "DIVERGED - stop and reconcile"
  git log --oneline -5 -- CLAUDE.md   # PASTE

DO NOT:
  - Do not add state to CLAUDE.md. No n-counts, no bankroll figures, no gap counts, no band-status inventory, no test-suite figures. All of it decays within days and that exact failure has been remediated twice. Point to the file that owns it.
  - Do not touch the Principal Vision framing, the hard rules, or the session-start protocol. The operator has explicitly asked those be preserved.
  - Do not restate the coverage-target pointer in the vision section — it has been there since 2026-08-12.
  - Do not correct anything beyond these two items. Register and stop.
  - Do not mark ADR-0053 ACCEPTED.

Check box 1.8 in MARKET_EXPANSION_ACTION_PLAN.md when done. Log in DECISION_LOG.md per Hard Rule 7, in-session, not at close-out. That file is shared with Block E — commit path-scoped and re-read it fresh immediately before writing (Hard Rule 10).

REPORT BACK: branch and commit range, the two edits as diffs, and — unprompted — WHAT YOU DID NOT CHECK.
```

---

## Needs the operator's decision, not a window

1. **ADR-0053 sign-off** (`03_DECISIONS/ADR-0053_market-type-band-composition.md`, PROPOSED). Proposes a `MarketBandCell` keyed `(market_type, band)` carrying its own `clean_n`/`n*`/status/kill-switch state, plus a named-not-built game-key correlation group for cross-family exposure (Phase 3 box 3.7). **T-441 deliberately deferred implementation to strategic review — this is that review.** Phase 3's whole shape depends on it, and Hard Rule 3 makes it immutable once accepted.
2. **Generality vs. edge.** Is game-market expansion accepted as a test of generality at likely-thinner edge, or expected to produce edge? Predicted in advance either way, or the result is unfalsifiable. Block F documents the tension; it cannot decide it.
3. **Band activation order** (GG-172, OPEN, HIGH). Does "all five bands" mean reactivating T1 — dead on four exhausted model classes, needing GG-153's decision — or building new families only in bands that are structurally sound?
4. **Partial-game derivatives** (`KXMLBF3/F5/F7`). Best efficiency-gradient fit on the board, but `PARTIAL_GAME_WINNER` failed the depth gate at $1.28 against a $10 floor (0I.1). In or out of the standard-mechanisms target?
5. **ADR-0051** — 17 stuck T1 positions, $160.24 paper capital in limbo, awaiting sign-off. Premise verified (0/17 have a date mismatch — not GG-166 collateral).

## Queued behind Phase 1

- **Phase 2** — minimal falsification before any C2 build (LL-009). If the distribution gate fails, reroute to moneyline-first; do not terminate the phase.
- **GG-170** — OPEN, CRITICAL, mitigation unbuilt. New resolutions keep inheriting wrong-day outcomes. T-437 proposed reconcile-on-reread (provisional until a second re-fetch ≥7 days later agrees); not built.
- **GG-174** (new, D) — Polymarket hardcoded `nba` tag; wrong tag returns empty markets silently (KI-019). Dormant until T-077 KYC.
- **GG-173** (new, A) — CI-only test-clock flake straddling UTC midnight. LOW.
- **GG-164** — 45,217 historical cycle-log rows uncorrected.
- **T4M-PROJ n\*** — `clean_n=453` vs `n*=839`, 386 short. Not governance-grade; do not cite as such.

## Done this run

- **A / T-439** — market-type registry `(market_type × band)` + `kalshi_client` series constants registry-driven. Boxes 1.1, 1.3. `b636408`, PR #72 `bb42743`. Registered GG-173.
- **B / T-440** — replay baseline re-run post-T-437; T-427's corrected gate wording landed verbatim in box 1.6; box 1.7 settled at **2,847 / 28 / 0** (2026-08-12), superseding both the 2,813/14 and 2,827/0 figures. `187ee94`.
- **C / T-441** — GG-172 registered (band dimension unowned, HIGH); ADR-0053 drafted PROPOSED, implementation deferred to strategic review. `7cd9b5c`.
- **D / T-442** — `VenueAdapter.fetch_markets(market_type)`; `open_position()` generalized off player fields; vig cascade extracted to per-`(market_type, band)` config. Boxes 1.2, 1.4, 1.5. Branch head `583e1db`. Registered GG-174. **Merge pending — Block G.**

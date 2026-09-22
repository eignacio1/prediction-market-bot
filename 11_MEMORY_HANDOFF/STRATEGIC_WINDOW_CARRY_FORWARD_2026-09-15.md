# Strategic window carry-forward — Waves 20–24, 2026-09-15

**Outgoing window:** Cowork strategic window, Waves 10–24 (this document covers 20–24). Operator: Earl, sole operator and reviewer.
**Verified against:** `origin/main = 417663f`, derived 2026-09-15T00:0xZ.

**Do not trust any figure in this document without re-deriving it.** Every number below was derived by execution, not recall, at `417663f` — but this window could not `git fetch` (no network from its environment), so its ref was frozen at whatever a terminal last fetched, and it falsely reported landed work as unlanded once because of that. Two figures this window had been repeating for five waves turned out to be wrong the moment they were actually derived (see §1). That pattern applies to this document the moment another commit lands.

---

## §0 — RUN THIS FIRST. Literal commands. Do not design your own.

```
cd <repo> && git fetch origin && git log --oneline -1 origin/main

# Cells, bands, and — the number that matters — how many cells are actually live.
PYTHONPATH=src python3 - <<'EOF'
from prediction_market_bot.c5_execution.market_type_registry import MARKET_TYPE_REGISTRY as R
from prediction_market_bot.execution_bands import ExecutionBand
from collections import Counter
print("BANDS:", len(list(ExecutionBand)))
print("CELLS:", len(R))
print("STATUS:", dict(Counter(v.status for v in R.values())))
EOF

# Gap log state
G=03_DECISIONS/GOVERNANCE_GAP_LOG.md
grep -c '^### GG-' $G                 # total entries
grep -c '^\*\*Status:\*\* OPEN' $G    # open
grep -oE '^### GG-[0-9]+' $G | grep -oE '[0-9]+' | sort -n | tail -1   # highest used

# THE landing check. Run it on every branch you believe is merged.
git merge-base --is-ancestor <branch> origin/main && echo LANDED || echo NOT-LANDED

# Approvals — read directly, never paraphrased from this document
cat 00_ADMIN/APPROVALS_REGISTER.md
```

Then run the Princeton Protocol (`00_ADMIN/Princeton Protocol.txt`) in full — all four passes — and re-derive the state block yourself.

---

## §1 — Landmarks, derived 2026-09-15 at `417663f`

| Indicator | Value | How it was derived |
|---|---|---|
| Execution bands | **22** | `len(list(ExecutionBand))` |
| Registry cells | **92** | `len(MARKET_TYPE_REGISTRY)` |
| **Cells ACTIVE** | **1** | `Counter(v.status ...)` |
| Cells NOT_IMPLEMENTED | 88 | same |
| Cells BLOCKED | 2 | same |
| Cells DARK | 1 | same |
| Gap-log entries | 123 | `grep -c '^### GG-'` |
| Gaps OPEN | 86 | `grep -c '^**Status:** OPEN'` |
| Next free GG | **276** | highest used = 275 |
| Positions ever opened, any sport | **0** | see §3 |

**Two figures this window repeated for five waves and got wrong.** It cited "18 bands" throughout — the real number is 22. It cited cell counts without ever deriving the status split, so it never once reported the single most important fact about this system: **one cell out of ninety-two is active.** Both errors came from grepping source files instead of importing the real objects. Import the objects.

**What "1 ACTIVE" means:** everything built across Waves 20–24 — NFL and MLB game-market run scripts, settlement, the LR model, the dashboard panel — sits at NOT_IMPLEMENTED. The build is real and tested; none of it is switched on. Do not describe this system as "trading NFL." It is not.

---

## §2 — ⚠️ FIRST BLOCK OF YOUR FIRST WAVE. Non-negotiable.

**GG-271's fix is complete, correct, and not on `origin/main`.**

| | |
|---|---|
| Branch | `origin/session/20260911T152320Z-gg271-bound-t4-rejected-positions` |
| Tip | `8e25420` |
| Commits ahead of main | **7** |
| `git merge-base --is-ancestor <branch> origin/main` | **NO** |
| Contents | `MAX_REJECTED_POSITIONS=2000` ring buffer in `paper_trader.py` (+20 lines); `scripts/gg271_bound_t4_rejected_positions.py` (209 lines); a fixed unprotected read race in the migration backup/verify path; `tests/test_paper_trader.py` (+97 lines); live VPS migration recorded as completed |
| Gap status on the branch | RESOLVED |
| Gap status on `origin/main` | **OPEN** |

**The consequence is already measurable, not hypothetical.** `logs/.vps_portfolio_cache_mlb_t4.json`, mtime 2026-09-14T23:45Z: **15,360,965 bytes, 7,505 `rejected_positions` entries** — 3.75× the 2,000 cap the branch installs. The data migration ran; the code never reached the server, so the live writer is still unbounded and regrew ~7,500 entries in three days. At that rate it returns to the ~33MB that OOM-killed the dashboard (GG-270) in roughly two weeks.

**Directive:** land that branch, then verify against the live file — entry count must fall to ≤2000 and stay there across a subsequent writer cycle. Do not verify by the merge succeeding.

This is the **13th+ recurrence of GG-186** (complete work whose branch never reached `origin/main`). Assume it will happen to you. Put `git merge-base --is-ancestor` in every close-out.

---

## §3 — ALREADY ANSWERED. Do not re-investigate. Do not re-derive.

This section exists because the last window burned waves rediscovering things. Each item below is settled, with the artifact that settles it. Read the artifact if you doubt it; do not commission a task.

1. **GG-203 — order submission fails.** Root cause is **external and not fixable in this repo**: Kalshi's demo order-write path rejects every schema-valid, auth-valid order, account-wide, ticker-independent, with rotating non-diagnostic 404/403 bodies. Reads succeed; only writes fail. Credential, env, ticker-construction and paper-trader-leak hypotheses were all ruled out with direct evidence in T-492. **Operator-level only.** ~30 days standing. Do not open a task on this.
2. **A moneyline is a spread at zero.** `paper_trader.py::settle_position()` (~line 915, `yes_won = actual_stat >= threshold` at ~954) is already sport- and stat-agnostic. The 09-07 audit's "no categorical outcome model exists, 12–18h to build" was **overstated** and the operator caught it. Mapping: game total → combined score; team total → that team's score; spread → final margin; **moneyline → final margin vs threshold 0.** Built in T-527. Do not re-scope this.
3. **The price archiver is parser-independent.** `scripts/archive_market_prices.py:142` calls `client._get("/markets", ...)`; `kalshi_client.py:459` returns raw `r.json()`. Zero `_parse_market()` call sites. Parser changes cannot affect what is captured. Verified twice (T-528, and independently in preflight).
4. **ADR-0060 recommends option (c) as TARGET ARCHITECTURE with implementation DEFERRED.** Trigger is T4M-PROJ's `kelly_fraction` reactivation under ADR-0048. This window flattened it to "build (c)" three times without opening it. Read §5 of the ADR before citing it.
5. **ADR-0062 BOUNDARY: the conservative reading is correct.** ARITH + FLOW only, not BOUNDARY — §4 is the roster decision, §6 is only an arithmetic projection, and MLB has no `T4M_BOUNDARY` member to mirror. Yields 14 new cells, 78 → 92. Confirmed by the actual build (T-524/GG-251).
6. **`EXP-026` / `HYP-011` are taken** by a pre-existing MLB moneyline experiment. NFL's is **`EXP-027` / `HYP-012`** (GG-258). Never reuse an experiment ID without checking the register.
7. **NFL depth sampling is `--depth-sample-per-family 1`, deliberately not 2.** Half the added request volume; T4M-PROJ's live MLB reads outrank the archive per the Phase 0-C directive inherited at `deploy/cron.conf:405-407`. Operator-approved 2026-09-08. Do not raise it without a new decision.
8. **The NFL cron path was proven before it fired** (T-537): archiver hand-run with the flag, plus the day-3 cron line dry-run verbatim in an `env -i` shell simulating cron's stripped runtime — all five links ($PROJ, `.env` export, interpreter, PYTHONPATH, log writability) clean; VPS `crontab -l` byte-identical to the repo. Then it fired: **17,367 KXNFL price rows on 09-09.** Capture is not an open question.
9. **The dashboard outage was four stacked faults, all resolved:** unbounded 33MB `json.load()` OOM-killing the service (GG-270); `systemctl is-active` reporting healthy through an OOM crash-loop (GG-269); a latency regression introduced by GG-270's own fix (GG-272); and `CPUQuota=10%` throttling the fixed 0.39s request into ~3.8–4.15s wall time, proven via `cpu.stat` showing 38-of-38 periods throttled (GG-273). The **cause** is GG-271 — see §2.
10. **`fetch_game_markets()` covers NFL and MLB game markets.** Thresholds are read from the payload's `floor_strike`, never reconstructed from the ticker tail (team codes are variable-length: `KC`, `SF`, `NYG`, `LAR`). MLB prop parsing held 286/286 across both changes.

---

## §4 — Genuinely open, with the directive attached

| Gap | State | Directive |
|---|---|---|
| **GG-271** | Fixed on unmerged branch; file regrowing | §2. Wave 25 block 1. |
| **GG-274** | NFL T1 settlement path never exercised end-to-end | Needs a real position first. Wave 25 block 2. |
| **GG-257** | Kalshi splits a tied NFL moneyline $0.50/$0.50; boolean `>=` can't express it. Resolver **refuses** rather than guessing — correct. ~1 tie/season | Operator decision, only before a live NFL portfolio exists. Not a build task. |
| **GG-260** | `ACTIVE_QUEUE.md` drifts as an uncommitted working-tree edit, invisible to worktree sessions. Recurrence of what T-505 fixed in Wave 10 | **Every block needs a Deliverable 0 that installs and commits the queue.** |
| **GG-262** | Live VPS crontab's `run_mlb_pregame.py` schedule diverges from the repo; cause unknown | Means the repo is not a reliable picture of the server. Worth one MICRO block, not a wave. |
| **GG-266** | Operator's Mac Python (3.9.6/LibreSSL) can't TLS-handshake with ESPN; all local live-network tests silently skip | Run network-dependent steps on the VPS and say so. |
| **GG-256** | `claim_session.sh` allowed a duplicate T-number (two sessions claimed T-526 one second apart) | Every block: verify T-number uniqueness across `git log --all` before pushing. |
| **GG-255** | Run scripts exist for NFL and MLB T1 game markets. **No cron for either** — manual invocation only | Scheduling requires explicit operator authorization. Do not add a cron entry on your own judgment. |

---

## §5 — Operator-only. Neither you nor a terminal can move these.

| Item | Plain English | Consequence of waiting |
|---|---|---|
| **GG-203** | ~30 days. Every real order fails. Account/API-key problem. Support ticket or demo-key regeneration. | **Nothing can ever trade, regardless of what gets built.** Largest item on the board. |
| **ADR-0063** | Five-tier kill-switch / Kelly alignment hierarchy. Drafted 2026-09-05, unsigned. | Blocks the kill-switch write side and everything gated behind it. |

Surface both in every status report until they move. Do not let them go quiet.

---

## §6 — Your first three waves, pre-scoped. Do not spend a wave deciding what to do.

**Wave 25 — close the loop once.**
1. Land the GG-271 branch (§2); verify against the live file, not the merge.
2. Open **one** real paper position via `src/prediction_market_bot/run_t1_nfl_game_market.py` (PAPER ONLY — `PaperTrader` is constructed `kalshi_client=None` unconditionally in `main()`; quote that line as the structural guarantee) against a live market, using the EXP-027 adapter, not the stub.
3. Settle it via `scripts/apply_resolved_nfl_game_markets.py` after the game finals. Prove idempotency — run twice, ledger byte-identical. Closes GG-274.

**Wave 26 — the first real read on edge.** Re-run `scripts/exp027_hyp012_nfl_moneyline_backtest.py`. Its pre-registered gate returned **UNDERPOWERED** on 2026-09-09 because zero 2026 games had resolved (`clean_n=0`, `n*=inf`). Several weeks of results now exist and the archiver has been capturing closing lines the whole time. It re-scores automatically; only a re-run is needed. Out-of-sample 2025 baseline to compare against: accuracy 0.6056, Brier 0.2210, ECE 0.0661, n=284. **Do not change a pre-registered parameter or relabel the verdict after seeing it.**

**Wave 27 — depends on 26.** If the gate clears, the question becomes cell promotion and therefore ADR-0063. If it doesn't, the question is features, not sport. **Do not recommend against NFL on this result** — operator doctrine 2026-08-21, reaffirmed 2026-08-27: MLB, NBA, NFL and NHL are all being built; which cells calibrate edge is discovered per-cell, never decided in advance.

---

## §7 — How the operator wants you to work

- **Prompt blocks go in `04_EXECUTION/ACTIVE_QUEUE.md`**, not pasted into chat. He reads them against closed waves. Closed waves keep their rows with status + outcome; prompt blocks are deleted on close.
- **Blocks must be fenced and paste-in ready**: session-start protocol line, `scripts/new_session_worktree.sh "<name>"`, claim-at-run-time note, `*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***`, TIER, numbered deliverables, `DO NOT:` lines, `SCOPE FENCE:`, self-serialising close-out, `REPORT BACK:`. Prose bullet lists are **not usable** — this window shipped those once and wasted a turn.
- Fire one wave at a time, **three concurrent maximum, disjoint file surfaces.** Name the concurrency fence inside each block: which files the other live sessions own.
- **Plain English in chat.** He is a solo operator and will not decode jargon. Cut the acronym walls.
- Don't hand him work he must fire later; blocks are for now.
- Never say "did not land" — say "not visible at my ref `<SHA>`, which may be stale," and ask for `git fetch origin` before verification.
- Mark every claim's source: "verified at `file.py:954`" vs "from my working picture, unverified."

---

## §8 — The outgoing window's verdict on itself

**Waves 20–24 secured the one asset that could not be bought back later, and switched nothing on.**

NFL Week 1 price and depth history is captured and verified — un-backfillable per GG-156, and it was at zero four days before kickoff. Two near-misses: the archiver was MLB-only and nobody noticed for months, and the 2026 season opens on a **Wednesday** while the capture windows had been built around a Thursday opener, so the entire pregame window would have been missed. The second surfaced only because the operator corrected a timezone error — the audit meant to catch it had converted kickoff wrong by three hours, in the exact direction that hid the gap.

**Six errors, five of them the same one: asserting a fact about a file without opening it.** Flattening an ADR's recommendation without reading it; citing a superseded naming convention from memory; re-implementing a function in a test harness instead of importing it and reporting a false finding; generalising a landing theory from n=1; reporting landed work as unlanded from a frozen ref; reusing a live experiment ID. A seventh surfaced while writing this document — the "18 bands" figure repeated for five waves is actually 22, and the 1-of-92-active status split had never been derived at all.

**Every one was caught by a terminal or the operator. None by the window.** Cheap output and careful output are indistinguishable at the moment of production, and confidence is not calibrated to error rate. The countermeasure is not effort, it is mechanism: import the object, open the file, run the ancestor check, benchmark the deployed thing. GG-272 and GG-273 were caught *only* because a deliverable measured the live pipeline instead of trusting green unit tests.

**Standing instruction:** re-run §0 before trusting anything above, including this sentence.

---

## §9 — DO NOT — standing, carry forward verbatim

- Touch sizing or any `kelly_fraction` without an ADR, **including T1**. ADR-0058 authorizes measurement stake at 0.0 and no sizing change.
- Promote `assert_ledger_invariants.py` to `--strict`. Alarm-only is a standing operator decision.
- Bypass or disable a permission control — report the exact command and refusal text, hand back. Five waves were lost to workaround attempts; the diagnostic is worth more.
- Re-investigate GG-203 in-repo. The ruled-out list is exhaustive.
- Repair a derived file without establishing provenance first (GG-228).
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport or market family on one finding.
- Modify or re-time the MLB price capture (feeds T-488, T-494, Phase 2).
- Restart a production service without a scoped written authorization. The 2026-08-29 grant was scoped to the 11.1 repair only and does not extend.
- Add a cron entry for any T1 game-market run script without explicit operator authorization.
- Pre-assign T-/GG- numbers. Claim at run time; verify uniqueness across `git log --all`.

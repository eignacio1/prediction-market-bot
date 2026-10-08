# W60.3 — Dashboard truth gaps + gap-log hygiene (2026-10-08)

## Part A — DONE (PR #184, squash f94b5f6)
- **GG-525** (Live Terminal NBA row): Feeds & Health now always renders the NBA shadow row; with no ledger it reads "SHADOW NBA ledgers — no data - awaiting first regular-season rows", neutral (dim, not red). `Live Terminal.html` and embedded `_HTML` byte-identical (test).
- **GG-515** (390px overflow): global `td,th,code,.asof{overflow-wrap:anywhere}` + `section{overflow-x:auto}` backstop; link/path source in a `title` attribute. Real browser, `/project`: scrollWidth 1054 (before, local repro) → 390 = viewport (after). Live VPS, 1500px and 390px, `/` and `/project`: zero console/page errors, no failed requests, page width = viewport.
- Tests: `tests/test_w60_3_dashboard_truth.py` (5), dashboard suites 66 pass. CI "test" green (7m53s).
- Deploy run 37717295169: "t4-mlb restart decision: not_needed". pmbot-web-dashboard NRestarts=0, ActiveEnterTimestamp 2026-10-08 02:20:53 UTC; served `/` contains the NBA string, `/project` contains the wrap rule.
- Both GGs set RESOLVED with this proof. They were left in the live log (not archived): `retire_resolved_gaps.py --apply` on the live files would also move two other sessions' resolved entries, outside this block's scope.

## Part B — DONE
| Item | Before | After |
|---|---|---|
| Session-start hook OPEN count (GG-426) | printed **176** open / 365 total (hardcoded main-checkout path = stale tree) | **134** open / 373 total = anchored grep on the live log |
| Anchored grep (CLAUDE.md Step 3) | 134 | 134 |
| Parity (`### GG-` headers vs `**Status:**`) | 160 / 160 | 160 / 160 |
| `gg_id_uniqueness_check.py` | OK | OK |

- **GG-426 root cause:** `governance_scan.sh` hardcoded `PROJECT=".../Prediction Markets"`, so every worktree session read the main tree's gap log, which lagged origin/main. Fix: derive the repo root from the script's own location (hardcoded path kept as fallback).
- **Gaps by Arm:** no generator existed. Added `scripts/generate_gap_arm_index.py` → `03_DECISIONS/GOVERNANCE_GAP_ARM_INDEX.md` (160 live gaps; arm seed from the T-374 manual pass in `GOVERNANCE_GAP_ARM_SEED.txt`; 136+ later gaps are keyword-assigned and marked `(auto)`, i.e. unreviewed). The stale 126-gap index in the log is replaced by a pointer.
- **Severity tokens ("ADR-0052", "ledger"):** the entries involved are GG-164 (`MEDIUM`) and GG-166 (`CRITICAL`). Both already carry real tokens; the odd values were `generate_operator_console.py`'s `STATUS_RE` capturing everything after `Severity:**` (including a trailing `· **Assertion:** …` field). Fixed the parser to take the first token; no gap-entry content changed. All 134 OPEN entries now parse to a real token (CRITICAL 2 · HIGH 18 · MEDIUM 46 · LOW 47 · UNSPECIFIED 21).
- **OPEN before → after:** 136 (live log before GG-515/525 resolved; hook showed 176) → **134**.

## Decisions for the operator
- Review the `(auto)` arm assignments in the index if arm counts matter.
- 4 resolved-class entries remain in the live log (retirement debt, warn-only); archive them in a dedicated session.

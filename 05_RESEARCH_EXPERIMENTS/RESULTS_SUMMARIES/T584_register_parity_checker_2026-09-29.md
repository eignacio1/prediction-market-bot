# T-584 — register parity checker (GG-312)

Base 769d64d. Scope: `scripts/check_register_parity.py`, Section 0 row in `generate_operator_console.py`, tests.

## D1 — why 7 of 36
Reproduced: the 7 caught are ADR-0001/0010/0015/0024/0032/0045/0046.
The 29 misses: **27 hidden by `00_ADMIN/REGISTER_PARITY_EXEMPTIONS.txt`** (one cause) and **2 unparseable `## Status` headers** (ADR-0006, ADR-0007; the checker read only `**Status:**` lines and silently `continue`d).
GG-312's "rule 5 false positives" (ADR-0003/0018/0026/0027/0028) are covered by an APR row whose subject cell leads with that ADR.

## D2 — fix
- `## Status` heading format parsed; an unparseable status is now a finding, not a skip.
- Exemptions no longer suppress accepted-ADR rules (file is now redundant for the 27; not edited — out of fence).
- Accountability = own row, subject-cell lead, or enumerated in a RATIFY row's Population list.
- Reverse direction: RATIFY-enumerated ID with no doc; dated row whose Evidence cites no existing file or documented id (PENDING rows skipped).
- Negation guards unchanged. 38 tests, including the exact-36 ratification test run with exemptions disabled.

## D3 — Section 0 "missing register accountability": 15 -> 5
Genuine remaining: APR-0034/0035/0036 (pending decision requests, no row — not adjudicated); APR-0007, APR-0016 (dated rows, evidence points at nothing checkable). Not tuned to zero.

## Design judgments for the operator
Exemptions stop suppressing; PENDING rows skipped; ratification coverage depends on the free-text Population list; existing test `test_rule5_respects_exemptions_list` was inverted (renamed `..._ignores_...`) because it asserted the defect.

## Candidates for 38.1 (not written to GGL/DECISION_LOG)
APR-0007/0016 evidence; APR-0034/35/36 rows; exemptions file redundant; `SemanticFloorViolation` on 2026-09-29 0-player T1 run; stale T4 cycle log; MEMORY_BANK Compass OS Health 5159-char line.

# W64.1 — NFL deep challenger: QB-shrunk performance (EXPLORATORY)

Status: PART A DONE (plan frozen, features + look-ahead tests); PART B pending. Label: EXPLORATORY. No sizing change.

## Part A
- Step 0 (read-only): VPS checkout (e3353ad4, ancestor of main) now has `12_EXPLORATORY/NFL_FIRST_LOOK_EXPECTATIONS.md` and `NFL_TRANSLATION_MAP.md`. 63.3's UNAVAILABLE was a deploy-timing artifact; no gap registered.
- Plan frozen BEFORE fitting: `12_EXPLORATORY/20261009_nfl_qb_challenger/README.md` (M1 QB-shrunk EPA k=6, M2 EB-shrunk team rates K=2, M3 excluded: injury `date_modified` not in cache; m=8, alpha=0.00625, seed 20261009, B=2000).
- Features: `qb_features.py`; tests: `test_qb_features.py` (6 pass; K=0 reproduces the frozen builder on 2723 rows, 0 mismatches; poisoned-future and same-day rows never leak).
- Isolation tests + new tests: 24 passed.

## Part B
Pending.

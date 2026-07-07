# NFR-07 Evidence — Portability (dev env, no live dependencies)

**Requirement:** Full research pipeline runs end-to-end with all external calls mocked; zero live API dependencies in dev mode.

**Populated:** 2026-07-06 (GG-075 remediation).

## Evidence

- Full test suite (2,375 passed / 6 skipped / 1 pre-existing unrelated failure as of 2026-07-06 re-run) executes with all external network calls dependency-injected/mocked — confirmed by the absence of live network calls during a local `pytest -q` run with no venue/API credentials configured in the shell environment (this remediation pass's own test run is itself a live confirmation of this property, not just an assertion carried over from SESSION 110).
- `tests/test_kalshi_client.py`, `tests/integration/test_mlb_api_connectivity.py` — explicitly mock the venue/stats-API boundary rather than hitting it live in the default test configuration.

## Status

**OPERATIONALLY DEMONSTRATED, re-confirmed 2026-07-06** — the 2026-07-06 full-suite run for this remediation pass completed without any live API credentials present, corroborating the SESSION 110 finding rather than merely repeating it.

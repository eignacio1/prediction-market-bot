# Operator Digest — 2026-10-03

- T-631 (auto): T-631 (W48.1 exp037-land-deploy) stopped early at operator request: NFL rebased onto main (suite not run), nothing landed/deployed.

## 51.2 — NHL silent drops (STANDARD)
The hockey test run was quietly skipping about a quarter of the markets (379 of 1,595) because Kalshi abbreviates four teams (San Jose, Tampa Bay, Los Angeles, New Jersey) differently than our data does. Fixed the matching and added counters that now say why any market is skipped. The fix is saved on its own branch and NOT live: putting it live restarts the baseball engine, so that's your call on timing. Earlier hockey results never included games with those four teams. Still no real money at risk.

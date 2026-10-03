# Operator Digest — 2026-10-03

- T-631 (auto): T-631 (W48.1 exp037-land-deploy) stopped early at operator request: NFL rebased onto main (suite not run), nothing landed/deployed.

## 50.1 (cloud) — fixes to how sessions work; nothing new trading
- Fixed the session tool that accidentally put unreviewed work live last night, and made the test suite pass cleanly in cloud sessions. All checks are green.
- Checked all 30 recently logged problems: 5 can likely be closed, a few are real and worth fixing soon, and three NHL items must be fixed before any NHL result is read.
- Correction: last night's work *did* go live. Every code change to main automatically updates the server and restarts the live MLB process. That is probably who kept restarting it.
- Because merging restarts the live MLB process, this session's changes wait for you to merge them.
- Most urgent: a local session must turn on the NFL/MLB shadow jobs before Sunday's NFL games.
- Still zero real money at risk.

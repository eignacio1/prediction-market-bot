# Operator Digest — 2026-10-22 (W83.2, NBA lineup + usage)

- Status: PARTIAL. Two PRs merged on green CI (#313 capture, #317 play-type x absorption).
- DEPTH moved only on paper. The NBA lineup factor is now frozen and testable, but nothing is accruing.
- The report capture is blocked: the NBA's injury-report host returns 403 to the box (GG-1030). It works from your Mac. Order-book snapshots are being taken; injury reports are not.
- No scored games accrue until that is fixed. A free non-datacenter route (e.g. a scheduled GitHub Actions run) would need its own permission, so it is a strategic-window call.
- Muse's play-type class graded PARTIAL: four of seven types track the proxy at 0.5 or better, none failed.
- Absorber-profile cross is null at n=131 (Spearman +0.06, CI -0.11 to 0.24). It is underpowered, not disproven.
- The installer appended the cron line while the surface budget read RED, and the reason was not recorded (the GG-990 shape).
- Nothing for you to run. No capital, orders or sizing changed.

## GA-5 gap burn-down (2026-10-22)
Open gaps went from 207 to 205. Two were closed with evidence: one about the NBA auto-promotion, one about the approvals register being out of step with the decision documents. A third, a bug that made the MLB schedule check fail every day since July, now has a fix in the code and a test. It stays open until the fix is deployed and the box runs cleanly. No money, orders or live components were touched. Most of the remaining gaps need deploys, your sign-off, or are data work, so they will not clear quickly. Pillar: plumbing.

## GS-3 — gap sweep (process one-offs and observations)
Plumbing only; no money, orders or models touched. Seven old housekeeping gaps are closed with evidence, and four observations (things with nothing to fix) are now watch items instead of open problems. Under your keep-the-folder rule, the three "folder fell behind" gaps are closed too. The open-gap count went from 210 to 199. Two gaps about a stuck git lock stay open because they need a small code fix.

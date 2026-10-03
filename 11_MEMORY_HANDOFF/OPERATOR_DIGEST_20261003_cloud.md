# Operator Digest — 2026-10-03 (cloud blocks 49.1–49.3)

- The NFL and MLB shadow-testing code is now on the main branch and its tests pass. Nothing is running on the VPS yet — the cloud session cannot reach it.
- Slip to know about: a bookkeeping script pushed the NFL code to main a few minutes before I had run its tests. The tests then passed, so no harm, but it is logged as a gap so the script gets fixed.
- A script to switch the shadow jobs on safely is written. Run it from your Mac; it will stop and list 14 files for you to approve first.
- The live dashboard used to keep showing old numbers if its data source died. It now blanks out and says NOT LIVE. Both pages were checked in a real browser. It still needs deploying.
- 30 open issues from the last two waves are now written into the gap log, and the NHL test plan is on main.
- Still zero real money at risk.

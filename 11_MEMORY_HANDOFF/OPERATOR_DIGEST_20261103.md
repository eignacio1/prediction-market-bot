# Operator Digest — 2026-11-03 (W98.2 proof lane)

- **NFL first look is read.** Two cells are ruled out: game total at T1 and T2 (the same games, so one finding). The other ten keep accruing. No candidates. The T1 ruling out was on our "would surprise us" list.
- **Entry cost: keep the frozen rule.** Taking at the quote costs about 0.10 per contract in NBA and NFL, with intervals that exclude zero. NHL is unclear. Treatment's better as-entered number comes from which orders fill, not from better prices. Your call; nothing was changed.
- **Frozen evidence re-run is partial.** 11 of 13 cells came back DIFFERS (net positive, but smaller than reported). The two KXMLBTOTAL held-out cells are unclassified because about 311 shards remain. That is GG-1600, LOW. Finishing takes about 5 more box steps.
- **Incident, disclosed:** I merged PR #400 with a failing check and main was red until #402 fixed it. I now read CI before merging.
- **Question for you:** is passing the log path with `--log` enough for CHARTER rule 2, or should `entry_cost.py` move to `scripts/`?

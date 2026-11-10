# Muse - items for the Monday 2026-11-16 message (SW-9, collected through the week)

Not a file Muse fetches. The window folds these into the one weekly message the operator sends.

## 1. NBA.com tables that do not reproduce (found 11-10)
Evidence: STATUS.md "For Earl's Monday message" (C-400, C-411, C-417); ~1/3 of overnight chunks NONE (22 of 66, 05:15-15:50Z 11-10).
Closed seasons (2020-21) give different values on back-to-back reads and FREQ% partitions fail - the data cannot be changing,
so the READING METHOD is the problem (the rendered table mixes filter bands mid-load), not the source.
- Method rule: on NBA.com stats pages, read the JSON response the page itself requests (one request per filter value, e.g. per
  shot-clock band), from inside the browser session; record the request URL in provenance. Not the rendered table.
- Pause rule: 3 NONEs in one family for the same reason = pause that family like a block (rule c), move on, re-probe once a day
  with the JSON method.
- Re-verify every DONE chunk in an affected family (C-400 first) with the JSON method; a mismatch reopens it.

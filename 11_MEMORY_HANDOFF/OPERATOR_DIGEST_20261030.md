
## W95.3 — the box tells the truth (T-1480, PARTIAL)
- **Shipped (#378, live on box):** deploy-lag alarm (box HEAD vs origin/main, 45 min bound; measured median 2.1 min over 325 deploys) and a 30-min start grace for the t4_mlb silent-arm, so a :00 game start no longer reads false RED. Real outages still alarm.
- **Not solved:** demo orders refused for `insufficient_balance` (demo cash is $3,287, stakes $0.50). The cash guard is active yet logged zero skips; likely resting shadow orders reserving cash. Cause unproven — GG-1481.
- **Registered:** GG-1480 (docs-only pushes under 12_EXPLORATORY run the full deploy gate, up to 23 min).
- **Operator action:** none. Demo-only plumbing.

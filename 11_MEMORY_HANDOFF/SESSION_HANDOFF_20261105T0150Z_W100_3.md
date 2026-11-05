# SESSION HANDOFF — W100.3 (flex lane: B-026 + B-027 + B-040)

```
vision_pillar: PLUMBING
gap_measure: surface budget; OOM kills per 24h; picks-sheet panel nights read
gap_delta: OOM kills 142 -> 24 -> 39 (read 00:57Z 11-05; not 0); surface budget GREEN; picks nights read 0 -> 1 of 2; leftovers closed 2 of 2
pattern_sweep: tomllib import swept across tests/ and scripts/ (2 tests + 2 renderers fixed, others already had the fallback); installer MARKERS swept across all four *_cron_install.py (3 fixed to marker_in, 1 shared helper); lock-wrapper sweep across deploy/cron* (10 T1/T2 shadow lines wrapped in the mirrors)
surface_delta: none live (no new cron, service or workflow); one read-only script scripts/picks_sheet_read.py + its box task
```

## States
- **B-040 DONE** — PR #415 (73eda44). Boundary-safe MARKERS; both Py3.9 collection failures fixed (GG-1650 resolved).
- **B-027 PARTIAL** — kills 39/24h, not 0. Fix merged as PR #416 (c3a2fcc) but **not installed**. Window: after the operator approves **`t3_lock_stagger_install`** by name, run it, then `t3_lock_stagger_readback`, then `box_memory_read` after a full NBA + NHL night.
- **B-026 PARTIAL** — first night read and healthy on reasons (90%) and orders (2609/2614); results not filled yet (sheet built mid-games). Read the 05:37Z sheet with `picks_sheet_read`. GG-1690 registered (duplicate presentation).
- t4-mlb decision: no restart needed; `deploy_truth_read` at 01:43Z shows t4-mlb and the dashboard running the box HEAD code.

## For the next window, in plain English
The box is healthy but tight: about 985 MB of memory, one core, and it kills a runner now and then when too many copies pile up. Last night 39 runners were killed (down from 142 two days ago). The cause is that the earlier-in-the-day shadow runners had no guard against running twice at once; only the evening ones did. I extended the same guard to them, tested and merged it, but it is not on the box. It goes on only when the operator approves `t3_lock_stagger_install`. The picks sheet works: 134 games, 2614 picks, reasons on 90%, demo orders on nearly all. It overstates how many distinct opinions there are (GG-1690), and yesterday's results cannot show until after the games settle.

Registered (not fixed): GG-1690. Reserved unused: GG-1691, GG-1692, T-1691, T-1692.

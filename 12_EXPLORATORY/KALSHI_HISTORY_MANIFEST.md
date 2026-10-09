# Kalshi pre-2026 price history — manifest (EXPLORATORY data custody)

**Written:** 2026-10-09 (W62.2, T-759, GG-538). Not a verdict; a custody record. Pre-2026 here means the **2025 NFL season**
(Aug-2025 → Jan-2026 close dates). The same store also holds 226 **2026-season** KXNFLGAME markets (Aug–Oct 2026 close dates) that are
**NOT eligible** as pre-2026 data and must not be read by any exploratory study (sealed-cell rule, CHARTER §2).

## Locations (two independent copies)
| Where | Path |
|---|---|
| Operator machine (untracked, gitignored) | `exp_output/KALSHI_HISTORY/raw/` (main tree); rebuilt derived files are in the session scratch store and on the VPS |
| VPS 157.230.91.33 (durable) | `/opt/prediction-market-bot/exp_output/KALSHI_HISTORY/raw/` and `.../rebuilt_2026-10-09/` (12G free of 24G at copy time; not under `logs/`, no ledger path) |

## Files (sha256 verified identical on both machines, 2026-10-09)
| File | Bytes | sha256 |
|---|---:|---|
| `raw/raw_2026-10-02.jsonl` | 385,957,666 | `fe2b702ff37a4b858ff3c587d3fd0656f68d6cc6af95d1853ef8f51eb2a8d9b2` |
| `raw/raw_2026-10-09.jsonl` | 444,936,370 | `509af26effb36e565c2deba940f6a66413749aec0040e8487eac3e42936b3bf4` |
| `rebuilt_2026-10-09/candles/KXNFLGAME.jsonl` | 358,219,234 | `58efa2e379afddc2bc6a4ead0c18c0c3722d13c250b8e99c5c8765b9621ff7ed` |
| `rebuilt_2026-10-09/markets/KXNFLGAME.jsonl` | 714,418 | `b871700cedc8701ac884be79f60e0dc85c98db1011b71e45b57d2881c0b6a45e` |
| `rebuilt_2026-10-09/VALIDATION.json` | 420 | `3e1823360603a2a81b086f54c81d314628ffbbff9ceac7efea393efce63de982` |

`raw_digest_sha256` (store-level, in VALIDATION.json): `df8d5dd3889d3a7a9bd6d9f5785a52c8ac61ab2ba0731c4994796914b351882d`.
The derived files were rebuilt from the extended `raw/` into a scratch `--store`; the **tracked** `exp_output/KALSHI_HISTORY/markets/` and
`VALIDATION.json` in git are the older partial build (862 markets / 415 sets) and were deliberately left untouched. Refreshing them is a separate,
operator-visible change.

## Coverage
Family: **KXNFLGAME only** (moneyline). 892 markets, 892 candle sets at 1m and 892 at 60m (all `ok`), 0 markets without hourly candles.
Market validation: 880 ok, 12 flagged (same 12 flagged in the earlier build). **Fetch is complete: 892 listed settled = 892 candle sets.**
There is no pre-2026 history for spread, total or team-total families (none was ever fetched; Kalshi history coverage for those is unverified).

By market close month: 2025-08 98 · 2025-09 128 · 2025-10 116 · 2025-11 136 · 2025-12 132 · 2026-01 56 (= **666, the 2025 season incl. preseason**)
· 2026-08 98 · 2026-09 96 · 2026-10 32 (= 226, 2026 season, ineligible). No month gap inside Aug-2025 → Jan-2026.
(The month tally read `close_time` only; no 2026-season outcome or price was read.)

## Restore
Copy `raw/` back; `python3 scripts/kalshi_history_build.py build --store <dir>` regenerates candles/markets/VALIDATION deterministically.

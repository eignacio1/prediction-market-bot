# W92.1 winter archive: measurement and readback (2026-10-28)

Source: box result files `04_EXECUTION/BOX_TASKS/results/20261028T051546Z_w921b_archive_cron_readback.md` and `..._budget_read.md`. Public unauthenticated Kalshi market-data GETs only.

## One archiver run, per series (box, `--pause 0.30`)

| Series | Rows | Bytes | Seconds |
|---|---|---|---|
| KXNBAGAME | 67 | 33,007 | 1.31 |
| KXNBASPREAD | 430 | 213,742 | 2.60 |
| KXNBATOTAL | 379 | 186,518 | 2.09 |
| KXNBATEAMTOTAL | 458 | 231,643 | 1.91 |
| KXNHLGAME | 101 | 49,381 | 1.31 |
| KXNHLSPREAD | 87 | 42,900 | 1.23 |
| KXNHLTOTAL | 185 | 90,414 | 1.29 |
| KXNHLTEAMTOTAL | 172 | 86,415 | 1.30 |

NBA per run about 1,334 rows, 665 KB, 8 s. NHL per run about 545 rows, 269 KB, 5 s. About 44 runs per day each.

## Disk
About 1.2 GB per month combined (NBA about 880 MB, NHL about 355 MB) against 9.0G free on /dev/vda1 (24G, 62% used). PRICE_ARCHIVE is 1.3G today. At that rate free space lasts well past the NBA/NHL season but is a watch item (not in this block's scope to rotate).

## Pacing
0.30 s floor enforced by the archiver (about 3.3 req/s per process, under the GG-1341 limit of about 4 req/s). Runs are staggered (MLB :00/:20/:40, NFL :05/:25/:45, NBA :08/:28/:48, NHL :11/:31/:51) and each lasts under 10 s, so processes do not overlap. One measurement run absorbed 2 429s on KXNBASPREAD; the last 500 log lines held 1.

## Readback (05:16Z)
`prices_2026-10-28.jsonl`, 1,612,405 bytes: KXNBAGAME 66, KXNBASPREAD 429, KXNBATEAMTOTAL 459, KXNBATOTAL 380, KXNHLGAME 98, KXNHLSPREAD 78, KXNHLTEAMTOTAL 160, KXNHLTOTAL 171. Log: "wrote 507 snapshots", 4 depth samples.

## Surface budget
Before: 83 live, 6 mirrored-but-not-installed, GREEN (a defect). After the fix (PR #361): the six are excluded from `live` and turn the budget RED until installed; after install, 83 live, 0 not installed, GREEN, healthcheck HEALTHY.

## Not archived (follow-ups)
Period/half series (KXNBA1H/1Q, KXNHL1P), KXNBAOT, KXNBAWINMARGIN, KXNBAMATCHUP, player props, parlay/multi-leg families.

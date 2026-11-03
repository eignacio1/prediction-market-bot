# Box task `frozen_resume_combine` — 20261103T063526Z_z_frozen_resume_combine

- request: `04_EXECUTION/BOX_TASKS/requests/20261103T063526Z_z_frozen_resume_combine.toml`
- note: B-002: classify the 13 cells (window, read-only)
- ran: 2026-11-03T07:13:17Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python 12_EXPLORATORY/frozen_evidence_check/resume.py combine`

```
## window: all archive files

91.2 split date 2026-09-13; ladder triggers k007/exact 105721/130947; missing units: none

| cell | reported n/net/lo | re-run n (games) | k007 net [lo,hi] | exact net [lo,hi] | class |
|---|---|---|---|---|---|
| 89.2 KXMLBHIT T0-2h 20-25c all yes | (1892, 0.027, 0.0065) | 2734 (516) | +0.0124 [-0.0053, +0.0289] | +0.0186 [+0.0009, +0.0351] | DIFFERS |
| 89.2 KXMLBHIT T0-2h 20-25c tight yes | (1151, 0.044, 0.017) | 1864 (488) | +0.0218 [+0.0011, +0.0422] | +0.0280 [+0.0072, +0.0483] | DIFFERS |
| 89.2 KXMLBF5TOTAL T6-24h 90-95c all yes | (143, 0.038, 0.022) | 132 (128) | +0.0381 [+0.0215, +0.0484] | +0.0397 [+0.0230, +0.0501] | DIFFERS |
| 89.2 KXMLBF5TOTAL T6-24h 90-95c wide yes | (111, 0.033, 0.011) | 101 (98) | +0.0428 [+0.0387, +0.0470] | +0.0443 [+0.0400, +0.0486] | DIFFERS |
| 89.2 KXMLBF5TOTAL T2-6h 90-95c tight yes | (85, 0.043, 0.017) | 89 (87) | +0.0454 [+0.0219, +0.0583] | +0.0473 [+0.0238, +0.0603] | DIFFERS |
| 89.2 KXNFLTOTAL D1 5-10c all no | (154, 0.038, 0.0065) | 148 (89) | +0.0370 [+0.0014, +0.0637] | +0.0370 [+0.0014, +0.0637] | DIFFERS |
| 89.2 KXMLBSPREAD T>24h 20-25c tight no | (186, 0.052, 0.0026) | 262 (206) | +0.0385 [-0.0061, +0.0766] | +0.0444 [-0.0003, +0.0825] | DIFFERS |
| 89.2 KXMLBTEAMTOTAL T6-24h 15-20c tight no | (49, 0.095, 0.0085) | 59 (50) | +0.0702 [-0.0065, +0.1385] | +0.0750 [-0.0017, +0.1433] | DIFFERS |
| 89.2 KXMLBF5 T2-6h 10-15c all no | (44, 0.078, 0.0087) | 75 (75) | +0.0428 [-0.0224, +0.0964] | +0.0468 [-0.0184, +0.1004] | DIFFERS |
| 89.2 KXMLBTOTAL T0-2h 85-90c wide yes | (52, 0.089, 0.047) | 72 (72) | +0.0383 [-0.0301, +0.0915] | +0.0419 [-0.0265, +0.0950] | DIFFERS |
| 89.2 KXMLBF7 T0-2h 40-45c wide yes | (121, 0.065, 0.0006) | 144 (105) | +0.0509 [-0.0119, +0.1080] | +0.0595 [-0.0033, +0.1166] | DIFFERS |
| 91.2 KXMLBTOTAL T0-2h net2-5c tight (HELD_OUT second half) | (117, 0.087, 0.0336) | 336 (103) | +0.0716 [+0.0131, +0.1309] | +0.0219 [-0.0258, +0.0694] | DIFFERS |
| 91.2 KXMLBTOTAL T0-2h net5c+ tight (HELD_OUT second half) | (30, 0.2166, 0.0951) | 89 (24) | +0.2324 [+0.0937, +0.3640] | +0.2569 [+0.1305, +0.3832] | DIFFERS |

## window: dates < 2026-10-28

91.2 split date 2026-09-12; ladder triggers k007/exact 105417/130633; missing units: none

| cell | reported n/net/lo | re-run n (games) | k007 net [lo,hi] | exact net [lo,hi] | class |
|---|---|---|---|---|---|
| 89.2 KXMLBHIT T0-2h 20-25c all yes | (1892, 0.027, 0.0065) | 2734 (516) | +0.0124 [-0.0053, +0.0289] | +0.0186 [+0.0009, +0.0351] | DIFFERS |
| 89.2 KXMLBHIT T0-2h 20-25c tight yes | (1151, 0.044, 0.017) | 1864 (488) | +0.0218 [+0.0011, +0.0422] | +0.0280 [+0.0072, +0.0483] | DIFFERS |
| 89.2 KXMLBF5TOTAL T6-24h 90-95c all yes | (143, 0.038, 0.022) | 132 (128) | +0.0381 [+0.0215, +0.0484] | +0.0397 [+0.0230, +0.0501] | DIFFERS |
| 89.2 KXMLBF5TOTAL T6-24h 90-95c wide yes | (111, 0.033, 0.011) | 101 (98) | +0.0428 [+0.0387, +0.0470] | +0.0443 [+0.0400, +0.0486] | DIFFERS |
| 89.2 KXMLBF5TOTAL T2-6h 90-95c tight yes | (85, 0.043, 0.017) | 89 (87) | +0.0454 [+0.0219, +0.0583] | +0.0473 [+0.0238, +0.0603] | DIFFERS |
| 89.2 KXNFLTOTAL D1 5-10c all no | (154, 0.038, 0.0065) | 147 (88) | +0.0368 [+0.0036, +0.0635] | +0.0368 [+0.0036, +0.0635] | DIFFERS |
| 89.2 KXMLBSPREAD T>24h 20-25c tight no | (186, 0.052, 0.0026) | 262 (206) | +0.0385 [-0.0061, +0.0766] | +0.0444 [-0.0003, +0.0825] | DIFFERS |
| 89.2 KXMLBTEAMTOTAL T6-24h 15-20c tight no | (49, 0.095, 0.0085) | 59 (50) | +0.0702 [-0.0065, +0.1385] | +0.0750 [-0.0017, +0.1433] | DIFFERS |
| 89.2 KXMLBF5 T2-6h 10-15c all no | (44, 0.078, 0.0087) | 75 (75) | +0.0428 [-0.0224, +0.0964] | +0.0468 [-0.0184, +0.1004] | DIFFERS |
| 89.2 KXMLBTOTAL T0-2h 85-90c wide yes | (52, 0.089, 0.047) | 72 (72) | +0.0383 [-0.0301, +0.0915] | +0.0419 [-0.0265, +0.0950] | DIFFERS |
| 89.2 KXMLBF7 T0-2h 40-45c wide yes | (121, 0.065, 0.0006) | 144 (105) | +0.0509 [-0.0119, +0.1080] | +0.0595 [-0.0033, +0.1166] | DIFFERS |
| 91.2 KXMLBTOTAL T0-2h net2-5c tight (HELD_OUT second half) | (117, 0.087, 0.0336) | 339 (106) | +0.0685 [+0.0055, +0.1248] | +0.0203 [-0.0306, +0.0676] | DIFFERS |
| 91.2 KXMLBTOTAL T0-2h net5c+ tight (HELD_OUT second half) | (30, 0.2166, 0.0951) | 98 (27) | +0.2174 [+0.0679, +0.3607] | +0.2405 [+0.1190, +0.3721] | DIFFERS |


```

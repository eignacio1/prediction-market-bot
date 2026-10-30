# Box task `frozen_inventory_read` — 20261030T141438Z_w95_2b_frozen_inventory_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261030T141438Z_w95_2b_frozen_inventory_read.toml`
- note: W95.2 Part A: archive inventory (retry)
- ran: 2026-10-30T14:16:41Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python 12_EXPLORATORY/frozen_evidence_check/repro.py inventory --archive exp_output/PRICE_ARCHIVE`

```
{
 "files": 91,
 "first": "2026-08-01",
 "last": "2026-10-30",
 "rows_by_series": {
  "KXMLBSPREAD": 153442,
  "KXMLBTOTAL": 256821,
  "KXMLBTEAMTOTAL": 338576,
  "KXMLBF5": 65793,
  "KXMLBF7": 69384,
  "KXMLBF5TOTAL": 153832,
  "KXMLBHIT": 532614,
  "KXNFLSPREAD": 311912,
  "KXNFLTOTAL": 230174,
  "KXNFLTEAMTOTAL": 260387
 },
 "two_sided_by_series": {
  "KXMLBSPREAD": 148162,
  "KXMLBTOTAL": 255259,
  "KXMLBTEAMTOTAL": 327390,
  "KXMLBF5": 63562,
  "KXMLBF7": 63325,
  "KXMLBF5TOTAL": 146374,
  "KXMLBHIT": 378807,
  "KXNFLSPREAD": 307390,
  "KXNFLTOTAL": 228684,
  "KXNFLTEAMTOTAL": 243360
 },
 "KXMLBHIT_two_sided_prestart": 199937
}

```

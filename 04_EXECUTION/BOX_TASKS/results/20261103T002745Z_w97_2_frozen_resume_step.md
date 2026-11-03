# Box task `frozen_resume_step` — 20261103T002745Z_w97_2_frozen_resume_step

- request: `04_EXECUTION/BOX_TASKS/requests/20261103T002745Z_w97_2_frozen_resume_step.toml`
- note: W97.2 Part A: resumable reproduction step 1 (box deployed 552bd996; t4-mlb restart not_needed)
- ran: 2026-11-03T00:43:06Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 124
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python 12_EXPLORATORY/frozen_evidence_check/resume.py step --budget 700`

```
[resume] unit KXMLBHIT full 91s
[resume] unit KXMLBF5TOTAL full 32s

[stderr]
[repro] alive 30s
[repro] alive 60s
[repro] alive 90s
[repro] alive 120s
[repro] alive 150s
[repro] alive 180s
[repro] alive 210s
[repro] alive 240s
[repro] alive 270s
[repro] alive 300s
[repro] alive 330s
[repro] alive 360s
[repro] alive 390s
[repro] alive 420s
[repro] alive 450s
[repro] alive 484s
[repro] alive 514s
[repro] alive 544s
[repro] alive 574s
[repro] alive 604s
[repro] alive 634s
[repro] alive 664s
[repro] alive 694s
[repro] alive 724s
[repro] alive 754s
[repro] alive 784s
[repro] alive 814s
[repro] alive 844s
[repro] alive 874s

```

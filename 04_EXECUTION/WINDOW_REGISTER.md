# Strategic window register

Operator, 2026-11-04 22:53 PT: "I want these windows to start getting numbered so I have a reference point on which window worked on
what". Every strategic window has a number, **SW-n**. The window states its number in its first message, in the RUNNING SITREP
header, in every queue commit it makes and in its handoff. The incoming window takes the next number and adds its row here
(`/strategic-handoff` does this). Numbering starts at the first window with a handoff on file; waves before Wave 10 predate the record.

| Window | Waves | Dates | Handoff (carry-forward) | Notes |
|---|---|---|---|---|
| SW-1 | 10 → 24 | → 2026-09-15 | `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-09-15.md` | |
| SW-2 | 25 → 30 | → 2026-09-22 | `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-09-22.md` | |
| SW-3 | 31 → 37 | 2026-09-22 → ~10-01 | none on file | no carry-forward found for these waves; may have been more than one window |
| SW-4 | 38 → 44 | → 2026-10-01 | `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-10-01.md` | |
| SW-5 | 45 → 51 | → 2026-10-03 | `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-10-03.md` | |
| SW-6 | 52 → 60 | → 2026-10-08 | `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-10-08.md` | |
| SW-7 | 61 → 80 | 2026-10-08 → 10-19 | `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-10-19.md` | |
| SW-8 | 81 → 100 | 2026-10-19 → 11-04 | `04_EXECUTION/STRATEGIC_WINDOW_CARRY_FORWARD.md` (11-04) | error log W25-W43 |
| **SW-9** | **101 →** | 2026-11-04 → | (at its handoff) | current; error log W44 → |

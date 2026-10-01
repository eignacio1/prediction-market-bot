# Operator Digest — 2026-10-01 (T-599 / EXP-031)

- I checked 14 Kalshi market families to see where prices are least efficient. The rule was fixed and pushed before any result was computed.
- Result: no family cleared the bar. Ten MLB families were no better than player hits (KXMLBHIT). Four NFL families had too little data to say anything.
- This does not argue for or against KXMLBHIT or any family. The window is only about two months, and the test uses the first price seen, which is unfair to families listed early.
- A test on the last pre-game price would be a new experiment and needs your decision first.
- Still open from earlier: the 0-player T1 run on 2026-09-28 has not been diagnosed. Bet count not re-checked this close-out.
- No model, order, sizing or pool was touched. Paper only.
# Operator Digest — 2026-10-01
- Built a tool that saves a dated snapshot of NFL lineup/venue data before each game; tested it twice live, no duplicates, nothing corrupted.
- Earlier worry that this data was already being lost was mostly wrong: the source keeps history, so weeks 1–3 can be rebuilt.
- It is instrumentation for next season, not new evidence for this one (about 8% of the sample the model test needs).
- The schedule to run it automatically is drafted but NOT switched on. Needs your yes; first game is Thursday night.
- Still zero real money at risk.

- T-600 (auto): T-600 Live Terminal landed (byte-faithful embed + 3 additive /api/data keys, tested); VPS restart skipped, unauthorized.

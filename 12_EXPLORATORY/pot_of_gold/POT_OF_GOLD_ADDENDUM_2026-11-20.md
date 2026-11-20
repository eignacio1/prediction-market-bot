# Pot-of-gold pre-registration — ADDENDUM 1 (written 2026-11-20 ~16:00Z, BEFORE any outcome in the new window is read; W122.2 / B-024)

The 2026-11-05 pre-registration binds unchanged: the 17 cells, route x family x bucket x time-to-start, book "all"; judged n 150 contracts
across >= 30 games AND >= 5 outcomes of the rarer kind; looks 2026-12-10 and 2027-01-14; PASS = Holm-adjusted game-clustered 90% lower
bound > 0. This addendum adds only what the 11-05 text did not cover.

1. **What the 17 are (read from `longshot_cells.toml`, not from memory):** 15 MLB + 2 NFL (KXNFLSPREAD D1 1-5c FADE, KXNFLTOTAL D1 95-99c TAKE).
   No NBA or NHL cell was among them. MLB is idle until 2027, so the 15 MLB cells gain no rows from the new window; only the 2 NFL cells can.
2. **This is a descriptive re-score, NOT a look.** Neither 12-10 nor 01-14 has arrived. A cell below judged n gets no score read, no PASS, no
   FAIL: it stays IN_SAMPLE ("CONTINUE"). Only a cell that reaches judged n in the window is read, with the 11-05 decision words.
3. **Window and data:** price archive through the last complete day before the run; settlements from Kalshi's public GET (same as
   `fetch_settlements.py`). Same method as `measure.py`: first two-sided pre-start snapshot per (ticker, tier); 70/30 split by game date,
   per sport; entry at the quote (YES at ask, NO at 1 - bid), so the spread is paid; exact fee (`quant/money.fee_rate`); game-clustered.
   Cost basis note: the spread is recorded in the archive on every row; the extra spread log on the box (since 11-18) is shadow-side and
   is not joined here.
4. **New families (props, NBA / NFL / NHL player markets since 2026-11-10) and NBA / NHL game families are MEASURED and listed, never
   promoted from this window.** A cell not among the 17 can only enter the router after its own dated pre-registration. They are named
   "candidate cells for a new pre-registration" in the result, with held-out numbers, and nothing routes from them.
5. **Router candidate (Part B):** key `pot_of_gold` in `router_candidates`, shadow only, using `longshot.decide` unchanged against a
   table generated from this re-score. Status gate unchanged (HELD_OUT / FORWARD_PASSED with net_lo > 0 only). Date-only sports get the
   D-tier of calib.tier computed from the event date and the row's own timestamp (no look-ahead).
6. **Modal outcome (stated in advance):** 0 of 17 earned; the 2 NFL cells below judged n; MLB 15 unchanged (IN_SAMPLE / no new data);
   props cells mostly below judged n. Any held-out positive cell outside the 17 is a lead for a new pre-registration, not a result.
7. **Words:** a cell that reaches judged n and loses is "hypothesis closed (EXP-POT-17, parked for R&D)"; nothing else closes.

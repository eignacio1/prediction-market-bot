# Operator Digest 2026-10-29

- The alarm saying the live MLB bot went quiet during the World Series game was false. The bot never stopped. The alarm just fires about 8 to 16 minutes before the bot's first line of the night, every night.
- The only fix is to give that one alarm a 30-minute grace period. I did not make it, because you said not to touch the alarm. It is waiting for your window to decide.
- Some past start-up delays were much longer (up to 27 hours). Nobody has checked whether those were real outages or just postponed games.
- New measurement of what a fill costs: orders that sit and wait lose about 11 cents per contract in hockey and 9 to 17 cents in baseball once filled. Taking the price on the screen does not have that problem. It only pays the normal spread, about 2 cents.
- So "take the quoted price" looks safe for the four frozen forward tests. The limits are that I could not measure delays of a few seconds, hockey bets pay less reliably, and I did not test bigger stakes.
- Still zero real money at risk. Only real demo fills count as execution evidence.

## W94.1 — NBA engine live arm (STANDARD)
- 56 games from the 2026-27 NBA season are now in the event store (last game 2026-10-27).
- EXP-044 is frozen: the NBA engine prices moneyline, spread, total and team totals one hour before tip, against the Kalshi quote. Verdict look 2027-04-20.
- EXP-044b is frozen: a v2 engine with an estimated score correlation and a calibration step. It beat v1 held-out on three of four markets.
- Altitude and travel factors did not help, so they were dropped. Availability, lineups and officials weren't built because their data isn't in the store (GG-1451). NBA applied factor classes stay at 4, not 7.
- Nothing is installed on the box. The box health read was RED at the start and I never saw GREEN (GG-1450).
- No orders, stakes or ledgers touched. No decision needed.

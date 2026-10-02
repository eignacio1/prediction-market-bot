# EXP-034 D1(b) — candle-vs-live correctness gate: tolerance (written BEFORE any comparison)

Written 2026-10-02 ~19:40Z, before the first live read was compared with any candle.

Sample: first 2 open tickers returned by `GET /markets?series_ticker=S&status=open&limit=100` at round 0, for
S in KXHIGHNY, KXHIGHCHI, KXHIGHMIA, KXCPI, KXPAYROLLS, KXGDP (12 tickers). Fixed after round 0; never swapped.
Rounds: >=6, spaced >=20 min (target 21 min). Each read: `GET /markets/{t}` -> yes_bid, yes_ask, retrieval UTC.
Candles: 1-minute, pulled AFTER the last round + 10 min settle.

Matching rule: a read at time t is matched to the 1-min candle with end_period_ts = ceil(t/60)*60. If that candle is
absent (candles are sparse; no row when nothing changed), the prevailing quote is the `close` of the nearest EARLIER
candle for that ticker; if none exists, the pair is UNMATCHED (reported, counted as a fail).

Per side (bid, ask), a pair PASSES iff  low-0.01 <= read <= high+0.01  against the matched candle (or, for the
absent-candle case, |read - prior close| <= 0.01).
Pair passes overall iff both sides pass.

GATE: >=95% of pairs pass overall AND no pair misses by >0.03 on either side. Empty-book placeholders are NOT
excluded (compared as reported). Failure => every candle-based number in EXP-034 is VOID: stop, report, hand back.
Tolerance is frozen by this commit; no edit after the comparison is run.

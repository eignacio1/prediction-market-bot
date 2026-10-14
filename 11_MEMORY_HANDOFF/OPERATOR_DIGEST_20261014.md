# Operator Digest — 2026-10-14

**Pillar moved: EXECUTION (orders that actually fill).** The test orders are being placed and cancelled correctly: 0 cancel failures, and the control arm is placing too. Nothing has settled yet, so we can't say whether the fills make or lose money.

Three safety guards are now in the code and tested. The bot refuses to send orders to the real-money Kalshi host. The forecast can no longer raise its own bet size. The shadow bets now stop when the kill switch is on. One piece is pending: the live T4 process runs on the old code until it is restarted between games.

Still zero real money at risk.

**One decision for you:** most skips are markets the demo site doesn't list, and they're about to trip the "pause the test" rule. Should those skips be left out of that rule? I recommend yes.

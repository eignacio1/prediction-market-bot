# Pot of gold: result (W105.6)
Data: 40,520 settled first-snapshots (5,325 MLB games, 371 NFL, 155 NHL, 155 NBA), 70/30 split by game date. Gaps below are settled-rate minus price, pooled; costs are 1-3c per contract (fee + half spread).
Routes defined 0 -> 3. Cells pre-registered: 17 (all IN_SAMPLE). Held-out and ready for the router: **0**.

**MLB.** No standard-board lottery-ticket overpay after costs. Longshots settle slightly *above* price (5-10c: +1.1c), favourites 85-95c settle about 1.2-1.4c above price. That is the favourite side underpriced by roughly one cent, smaller than the cost. Best candidate: KXMLBF5TOTAL 2-6h 90-95c TAKE_FAVOURITE (fit +3.7c, held-out +5.5c) but only 32 games and few losses, so IN_SAMPLE. 0 ready.

**NFL.** Pooled gaps are about -1c on longshots (settle below price, the classic direction) and mixed on favourites; costs eat it. KXNFLSPREAD 1-5c FADE looks good on 10 held-out games only. 0 ready.

**NHL.** Only 9 days of data; most buckets have under 30 contracts. Favourites at 85-95c settle several cents above price in tiny samples. UNTESTED in practice. 0 ready.

**NBA.** Also 9 days. Both longshots (-4c) and 85-95c favourites (-3.5c) settle below price, which is not the favourite-longshot shape, and the sample is thin. 0 ready.

**Answer:** on the data that exists, lottery-ticket buyers overpay by roughly 1c or less on average, and after cost nothing survives hold-out. The module exists and will route nothing until forward data promotes a cell. Multi-leg combos cannot be measured yet.

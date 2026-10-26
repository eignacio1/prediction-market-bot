"""W87.1 Part B: each re-pointed path is run old-vs-new on a frozen seeded snapshot and must be equal."""
from __future__ import annotations

import random

from prediction_market_bot.quant import money as Q


def _quotes(n=2000, seed=7):
    r = random.Random(seed)
    out = []
    for _ in range(n):
        b = round(r.uniform(0.01, 0.97), 2)
        a = round(min(0.99, b + r.choice([0.01, 0.02, 0.05])), 2)
        out.append((r.random(), b, a))
    return out


def test_fees_fee_k007_bit_equal_to_core():
    from prediction_market_bot.pregame_shadow import fees
    for q in [i / 1000 for i in range(0, 1001)]:
        assert fees.fee_k007(q) == 0.07 * q * (1.0 - q) == Q.fee_k007(q)

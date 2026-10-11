"""W68.2: NHL shadow eval + ADR-0072 demo flat stakes. Thin wrapper: the shadow row is written first by
nhl_shadow_eval and never altered; staking runs afterwards via the shared hook (demo-only guard inside).
Kept separate so nhl_shadow_eval.py stays free of any order-code import (tests/test_nhl_shadow_safety.py)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import nhl_shadow_eval as ev  # noqa: E402
from prediction_market_bot.c5_execution.shadow_flat_stake import make_on_row  # noqa: E402


def make_adapter():
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
    from prediction_market_bot.c5_execution.venue_adapter import KalshiVenueAdapter
    try:
        return KalshiVenueAdapter.from_env()
    except Exception:
        return KalshiVenueAdapter(KalshiMarketClient("public-read-only-no-auth"))


def main(argv=None) -> int:
    return ev.main(argv, on_row=make_on_row(make_adapter()))


if __name__ == "__main__":
    raise SystemExit(main())

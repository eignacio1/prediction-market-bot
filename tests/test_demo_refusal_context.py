"""W96.3 / GG-1481: balance + open exposure logged beside a refused demo order. Logging only; mocked, no network."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.c5_execution import demo_fill_policy as pol


@pytest.fixture(autouse=True)
def _reset():
    pol._REFUSAL_CACHE[0], pol._REFUSAL_CACHE[1] = None, 0.0
    pol._CASH_CACHE[0], pol._CASH_CACHE[1] = None, 0.0


def _client(bal=12.5, ok=True):
    c = MagicMock()
    c.get_balance.return_value = (ok, {"balance_usd": bal, "portfolio_value_usd": 3.0} if ok else {"error": "x"})
    return c


def test_logs_balance_and_open_exposure():
    ctx = pol.refusal_context(_client(), [{"size_usd": 0.5}, {"size_usd": 1.25}])
    assert ctx["demo_balance_usd"] == 12.5 and ctx["demo_portfolio_value_usd"] == 3.0
    assert ctx["open_exposure_usd"] == 1.75 and ctx["open_positions_n"] == 2


def test_burst_of_refusals_is_one_balance_get():
    c = _client()
    for _ in range(5):
        pol.refusal_context(c, [])
    assert c.get_balance.call_count == 1


def test_unreadable_balance_never_raises_and_says_so():
    ctx = pol.refusal_context(_client(ok=False), None)
    assert ctx["demo_balance_usd"] is None and ctx["open_exposure_usd"] == 0.0
    boom = MagicMock()
    boom.get_balance.side_effect = RuntimeError("down")
    ctx = pol.refusal_context(boom, [{"size_usd": "bad"}])
    assert ctx["demo_balance_usd"] is None and "down" in ctx["demo_balance_error"] and ctx["open_exposure_usd"] is None


def test_does_not_touch_the_cash_guard_cache():
    pol.refusal_context(_client(), [])
    assert pol._CASH_CACHE[0] is None  # the gate's view is unchanged by the logger

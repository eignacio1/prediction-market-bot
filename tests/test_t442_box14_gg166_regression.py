"""
T-442 Box 1.4 regression guard: open_position()'s generalized signature must
not disturb GG-166's fix.

GG-166 corrupted 55.63% of closed positions by stamping game_date from the
session wall-clock instead of the ticker-embedded date. The fix is three
call sites in run_t4_mlb_live.py that pass
_ticker_to_game_date(ticker, game_date) rather than the bare game_date
variable. Box 1.4 reorders/generalizes PaperTrader.open_position()'s
signature (player_name/player_id/kalshi_threshold become optional,
kwargs-only across the whole codebase) but must not touch these call sites'
values. This test pins the source-level invariant directly so a future
refactor that reverts any of the three back to the session value fails
loudly instead of silently reintroducing GG-166.
"""

import re
from pathlib import Path

_RUNNER_SRC = (
    Path(__file__).resolve().parent.parent
    / "src" / "prediction_market_bot" / "run_t4_mlb_live.py"
).read_text()


def test_two_cycle_log_sites_use_ticker_derived_date():
    """
    Both '"game_date":' dict-literal write sites in run_t4_mlb_live.py's
    cycle-log records must derive their value via
    _ticker_to_game_date(ticker, game_date), not the bare session-level
    game_date variable. GG-166/T-429.

    (This intentionally does not match plain `game_date=game_date`
    pass-through kwargs to inner functions like _run_cycle() — those forward
    the session value as an input parameter, they do not write it to a
    persisted record, so GG-166 does not apply to them.)
    """
    write_site_lines = [
        line for line in _RUNNER_SRC.splitlines()
        if re.search(r'"game_date":\s*\S', line)
    ]
    assert len(write_site_lines) == 2, (
        f"Expected exactly 2 cycle-log '\"game_date\":' write sites in "
        f"run_t4_mlb_live.py, found {len(write_site_lines)}: "
        f"{write_site_lines!r}. If this count changed intentionally, update "
        f"this test AND verify the new/changed site(s) still use "
        f"_ticker_to_game_date."
    )
    for line in write_site_lines:
        assert "_ticker_to_game_date(ticker" in line, (
            f"GG-166 regression: a cycle-log game_date write site in "
            f"run_t4_mlb_live.py does not derive from "
            f"_ticker_to_game_date(ticker, game_date) — this is the exact "
            f"defect that corrupted 55.63% of closed positions. "
            f"Offending line: {line!r}"
        )


def test_open_position_call_site_passes_ticker_derived_game_date():
    """
    The specific PaperTrader.open_position(...) call in run_t4_mlb_live.py
    must pass game_date=_ticker_to_game_date(ticker, game_date) as a keyword
    argument — this is the one write site that lands in the ledger PnL/kill
    switch reads (ADR-0052 §2.3), as opposed to the two cycle-log-only sites.
    """
    match = re.search(
        r"trader\.open_position\((.*?)\n\s*\)",
        _RUNNER_SRC,
        re.S,
    )
    assert match is not None, "Could not locate trader.open_position(...) call in run_t4_mlb_live.py"
    call_block = match.group(1)
    assert "game_date=_ticker_to_game_date(ticker, game_date)" in call_block, (
        "GG-166 regression: run_t4_mlb_live.py's trader.open_position(...) call "
        "no longer passes game_date=_ticker_to_game_date(ticker, game_date). "
        f"Call block was:\n{call_block}"
    )

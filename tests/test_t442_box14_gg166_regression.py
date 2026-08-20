"""
T-442 Box 1.4 regression guard: open_position()'s generalized signature must
not disturb GG-166's fix.

GG-166 corrupted 55.63% of closed positions by stamping game_date from the
session wall-clock instead of the ticker-embedded date. The fix is three
call sites in run_t4_mlb_live.py that derive game_date from a
_ticker_to_game_date(ticker) call rather than using the bare session-level
game_date variable. Box 1.4 reorders/generalizes PaperTrader.open_position()'s
signature (player_name/player_id/kalshi_threshold become optional,
kwargs-only across the whole codebase) but must not touch these call sites'
values. This test pins the source-level invariant directly so a future
refactor that reverts any of the three back to the session value fails
loudly instead of silently reintroducing GG-166.

T-472/GG-191 (2026-08-20): `_ticker_to_game_date` was changed from a
two-arg `(ticker, fallback)` function that silently substituted the
wall-clock `fallback` on any parse failure, to a one-arg `(ticker)`
function that returns None -- refusal, never a fallback -- on any parse
failure, with each call site checking for None and skipping the write. The
three call sites now assign the derived value to a local variable
(`_gg191_game_date` for the two cycle-log sites, `position_game_date` for
the open_position site) a few lines above the write, rather than inlining
the call at the write site itself. The assertions below were rewritten to
follow that indirection -- extract the variable name used at each write
site, then confirm that variable is itself assigned via
`_ticker_to_game_date(ticker)` somewhere in the file. This still pins the
same invariant (every game_date write site must trace to a
_ticker_to_game_date(ticker) call, never the bare session game_date), just
against the refusal-only implementation.
"""

import re
from pathlib import Path

_RUNNER_SRC = (
    Path(__file__).resolve().parent.parent
    / "src" / "prediction_market_bot" / "run_t4_mlb_live.py"
).read_text()


def _assert_traces_to_ticker_derivation(value_var: str, context: str) -> None:
    assert re.search(
        rf"\b{re.escape(value_var)}\s*=\s*_ticker_to_game_date\(ticker\)",
        _RUNNER_SRC,
    ), (
        f"GG-166/GG-191 regression: {context} uses {value_var!r}, which is "
        f"not assigned via _ticker_to_game_date(ticker) anywhere in "
        f"run_t4_mlb_live.py — this is the exact defect class that "
        f"corrupted 55.63% of closed positions."
    )


def test_two_cycle_log_sites_use_ticker_derived_date():
    """
    Both '"game_date":' dict-literal write sites in run_t4_mlb_live.py's
    cycle-log records must derive their value from a
    _ticker_to_game_date(ticker) call, not the bare session-level game_date
    variable. GG-166/T-429/GG-191.

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
        var_match = re.search(r'"game_date":\s*(\w+)', line)
        assert var_match is not None, (
            f"Could not extract a game_date value token from line: {line!r}"
        )
        _assert_traces_to_ticker_derivation(
            var_match.group(1), f"a cycle-log game_date write site ({line!r})"
        )


def test_open_position_call_site_passes_ticker_derived_game_date():
    """
    The specific PaperTrader.open_position(...) call in run_t4_mlb_live.py
    must pass a game_date= keyword argument that itself traces back to a
    _ticker_to_game_date(ticker) call — this is the one write site that
    lands in the ledger PnL/kill switch reads (ADR-0052 §2.3), as opposed to
    the two cycle-log-only sites.
    """
    match = re.search(
        r"trader\.open_position\((.*?)\n\s*\)",
        _RUNNER_SRC,
        re.S,
    )
    assert match is not None, "Could not locate trader.open_position(...) call in run_t4_mlb_live.py"
    call_block = match.group(1)
    var_match = re.search(r"game_date=(\w+)", call_block)
    assert var_match is not None, (
        "GG-166 regression: run_t4_mlb_live.py's trader.open_position(...) "
        f"call has no game_date=<var> kwarg. Call block was:\n{call_block}"
    )
    _assert_traces_to_ticker_derivation(
        var_match.group(1), "open_position's game_date= kwarg"
    )

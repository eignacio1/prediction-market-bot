"""GG-667/W72.1: one shared kill-switch check for order-placing paths outside C4.

C4/T4 runners halt on `logs/*kill_switch.flag` files (NFR-03: touch to halt, rm to resume) and
the cell-tier state in market_type_registry. The shadow stake path (shadow_flat_stake.maybe_place)
places demo orders without passing through C4, so it asks this helper before every order.
Read-only; fails closed (an unreadable logs dir counts as halted).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

_DEFAULT_LOGS_DIR = Path(__file__).resolve().parents[3] / "logs"


def halt_reason(market_type=None, band=None, logs_dir: Optional[Path] = None) -> Optional[str]:
    """Return why order placement must halt, or None when nothing is halted."""
    d = Path(logs_dir) if logs_dir is not None else _DEFAULT_LOGS_DIR
    try:
        flags = sorted(p.name for p in d.glob("*kill_switch*.flag")) if d.exists() else []
    except OSError as e:
        return f"kill_switch_state_unreadable:{type(e).__name__}"
    if flags:
        return f"kill_switch_flag:{flags[0]}"
    if market_type is not None and band is not None:
        from prediction_market_bot.c5_execution.market_type_registry import (
            CellKillSwitchStatus, resolve_kill_switch_state,
        )
        st = resolve_kill_switch_state(market_type, band)
        if st.status is CellKillSwitchStatus.HALTED:
            return f"cell_halted:{st.reason}"
    return None

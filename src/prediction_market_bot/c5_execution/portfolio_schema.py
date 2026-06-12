"""
Portfolio JSON Schema Owner — C5 Paper Trader (T-159 / LL-014)
==============================================================
Single source of truth for the portfolio state structure.

LL-014: stale-state bugs arose because multiple consumers read
portfolio fields by string key without any central definition.
Adding/renaming a field required hunting all consumers manually.
This module kills that class: all field names are constants here.
Any consumer that reads the portfolio must import from here.

Schema version: 1 (bump when fields are added/removed)
"""
from __future__ import annotations

from typing import Any

SCHEMA_VERSION: int = 1

# ---------------------------------------------------------------------------
# Top-level field name constants
# ---------------------------------------------------------------------------

F_BANKROLL          = "bankroll_usd"
F_INITIAL_BANKROLL  = "initial_bankroll_usd"
F_TOTAL_REALIZED_PNL = "total_realized_pnl"
F_CURRENT_DAILY_LOSS = "current_daily_loss"
F_DAILY_NET_PNL     = "daily_net_pnl"
F_DAILY_LOSS_DATE   = "daily_loss_date"
F_OPEN_POSITIONS    = "open_positions"
F_CLOSED_POSITIONS  = "closed_positions"
F_CREATED_AT        = "created_at"
F_LAST_UPDATED      = "last_updated"

# Position-level field name constants
P_POSITION_ID       = "position_id"
P_STATUS            = "status"
P_DIRECTION         = "direction"
P_SIZE_USD          = "size_usd"
P_MID_PRICE         = "mid_price_at_entry"
P_GAME_DATE         = "game_date"
P_POOL_ISOLATED     = "pool_isolated"
P_OUTCOME           = "outcome"
P_PNL               = "pnl"
P_EXIT_PNL          = "exit_pnl"
P_DUPLICATE_OF      = "duplicate_of"

# Valid status values
STATUS_OPEN         = "OPEN"
STATUS_CLOSED       = "CLOSED"
STATUS_EXITED       = "EXITED"

OPEN_STATUSES       = frozenset({STATUS_OPEN})
CLOSED_STATUSES     = frozenset({STATUS_CLOSED, STATUS_EXITED})

# ---------------------------------------------------------------------------
# Required top-level fields (must be present in any valid portfolio state)
# ---------------------------------------------------------------------------

REQUIRED_TOP_LEVEL_FIELDS: frozenset[str] = frozenset({
    F_BANKROLL,
    F_INITIAL_BANKROLL,
    F_TOTAL_REALIZED_PNL,
    F_CURRENT_DAILY_LOSS,
    F_DAILY_LOSS_DATE,
    F_OPEN_POSITIONS,
    F_CLOSED_POSITIONS,
})

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_portfolio_state(state: dict[str, Any]) -> list[str]:
    """Return a list of violation strings (empty = valid).

    Checks structural invariants only — not business logic like P&L correctness.
    Suitable for use in tests and session-start health checks.
    """
    errors: list[str] = []

    # Required fields present
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in state:
            errors.append(f"missing required field: {field!r}")

    if errors:
        return errors  # structural failures make subsequent checks meaningless

    # open_positions contains only OPEN status entries
    for i, pos in enumerate(state[F_OPEN_POSITIONS]):
        status = pos.get(P_STATUS)
        if status not in OPEN_STATUSES:
            errors.append(
                f"open_positions[{i}] has status={status!r}; expected OPEN"
            )

    # closed_positions contains only CLOSED or EXITED status entries
    for i, pos in enumerate(state[F_CLOSED_POSITIONS]):
        status = pos.get(P_STATUS)
        if status not in CLOSED_STATUSES:
            errors.append(
                f"closed_positions[{i}] has status={status!r}; expected CLOSED or EXITED"
            )

    # Numeric fields are non-negative where required
    if state[F_BANKROLL] < 0:
        errors.append(f"{F_BANKROLL} is negative: {state[F_BANKROLL]}")
    if state[F_INITIAL_BANKROLL] <= 0:
        errors.append(f"{F_INITIAL_BANKROLL} must be positive: {state[F_INITIAL_BANKROLL]}")
    if state[F_CURRENT_DAILY_LOSS] < 0:
        errors.append(f"{F_CURRENT_DAILY_LOSS} is negative: {state[F_CURRENT_DAILY_LOSS]}")

    # daily_loss_date is a non-empty string
    if not isinstance(state[F_DAILY_LOSS_DATE], str) or not state[F_DAILY_LOSS_DATE]:
        errors.append(f"{F_DAILY_LOSS_DATE} must be a non-empty string")

    return errors

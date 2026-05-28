# C4: Risk Engine
# Phase active: Phase 5+ (GATED — not active until ADR-0004 accepted + G5 signed)
# Applies hard limits, computes Fractional Kelly position sizing, triggers kill switch.
# f* = Kelly optimal fraction (see risk.py for formula)
# f_live = f* × kelly_fraction  (default 0.25; confirmed at G4)
# Position placed only if edge > MIN_EDGE_TO_APPROVE (2% default; confirmed at G4)
# Hard limits: stubs in risk.py; finalized in RISK_APPETITE_CONSTRAINTS.md at G4
# Gate: BOT_C4_ACTIVE=true required; NEVER set in ENV-01 or ENV-02
# Kill switch: daily_loss_limit or drawdown_limit breach → STATUS_KILL_SWITCH
# See: EXECUTION_ARCHITECTURE.md, RISK_APPETITE_CONSTRAINTS.md

from prediction_market_bot.c4_risk_engine.risk import RiskEngine

__all__ = ["RiskEngine"]

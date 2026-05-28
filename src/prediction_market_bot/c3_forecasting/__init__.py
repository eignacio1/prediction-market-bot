# C3: Forecasting Engine
# Phase active: Phase 3+
# Produces calibrated p_estimate and confidence_interval for each market event.
# Null model: mid_price = (bid + ask) / 2
# Edge: edge = p_estimate - market_implied_prob - vig
# Model class: LogisticRegression + Platt scaling (Phase 3 baseline; confirmed at ADR-0004)
# Calibration requirement: ECE < 0.05
# See: METHODOLOGY.md, ARCHITECTURE_OVERVIEW.md

from prediction_market_bot.c3_forecasting.forecaster import ModelForecaster

__all__ = ["ModelForecaster"]

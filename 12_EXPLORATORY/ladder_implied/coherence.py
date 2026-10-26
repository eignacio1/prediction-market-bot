"""W86.2 coherence checks (wrapper).

W87.1: the implementation moved to prediction_market_bot.quant.coherence (known-answer tests in
tests/test_w87_quant_absorb.py). This file is a thin wrapper kept so existing scripts and tests import unchanged.
"""
import prediction_market_bot.quant.coherence as _m

globals().update({k: v for k, v in vars(_m).items() if not k.startswith("__")})

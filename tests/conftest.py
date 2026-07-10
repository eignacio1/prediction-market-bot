"""Global pytest configuration — WINDOW B (B5), full-suite determinism.

Two concerns, both about reproducibility of test *results* across reruns and
across machines, not about import resolution (that's T-282/GG-104's
`pythonpath = ["src"]` fix in `pyproject.toml`):

1. Hypothesis profile — single source of truth. `test_t280_property_based_
   invariants.py` (B3) originally registered its own `derandomize=True`
   profile locally; centralizing it here means every current and future
   Hypothesis-based test in the suite gets deterministic example generation
   automatically, without each file needing to duplicate the registration.
2. Global `random` seed — an autouse, session-scoped fixture that seeds the
   stdlib `random` module before the suite runs. Tests that already build
   their own `random.Random(seed)` instance are unaffected (already
   deterministic); this only matters for code paths that call bare
   module-level `random.*` functions.
"""
from __future__ import annotations

import random

from hypothesis import settings

settings.register_profile("t280-deterministic", derandomize=True, max_examples=100)
settings.load_profile("t280-deterministic")

_GLOBAL_SEED = 20260709


def pytest_configure(config):  # noqa: ARG001 — pytest hook signature
    random.seed(_GLOBAL_SEED)

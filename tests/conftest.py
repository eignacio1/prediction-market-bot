"""Global pytest configuration — WINDOW B (B5), full-suite determinism.

Two concerns, both about reproducibility of test *results* across reruns and
across machines, not about import resolution (that's T-282/GG-109's
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

import os
import random

import pytest
from hypothesis import settings

settings.register_profile("t280-deterministic", derandomize=True, max_examples=100)
settings.load_profile("t280-deterministic")

_GLOBAL_SEED = 20260709


def pytest_configure(config):  # noqa: ARG001 — pytest hook signature
    random.seed(_GLOBAL_SEED)


# GG-428: live-network tests fail with a proxy 403 in egress-restricted sandboxes,
# turning a default `pytest -q` red for reasons unrelated to the code. Skip them
# unless explicitly opted in; CI (which has egress) sets the variable.
_NETWORK_ENV = "PMBOT_NETWORK_TESTS"


def pytest_collection_modifyitems(config, items):  # noqa: ARG001 — pytest hook signature
    if os.environ.get(_NETWORK_ENV) == "1":
        return
    skip = pytest.mark.skip(reason=f"live-network test; set {_NETWORK_ENV}=1 to run (GG-428)")
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip)


# GG-745/W75.4: C7 trip_kill_switch now writes the global flag file. Keep every test's flag
# directory private so a test trip can never halt other tests (or a real logs/ dir).
import pytest as _pytest_w754  # noqa: E402


@_pytest_w754.fixture(autouse=True)
def _isolated_kill_switch_dir(tmp_path_factory, monkeypatch):
    monkeypatch.setenv("PMBOT_KILL_SWITCH_DIR", str(tmp_path_factory.mktemp("kill_switch")))

"""
Phase MLB-G1 integration test fixtures.

All tests in this directory make REAL network calls. They are gated behind
pytest.mark.integration and never run in standard CI.

Run manually:
    pytest tests/integration/ -v -m integration

Requirements:
    - .env file loaded (VENUE_API_KEY, VENUE_PRIVATE_KEY_PATH set)
    - Network access to statsapi.mlb.com, site.api.espn.com, kalshi.com
    - exp_output/MLB/mlb_feature_matrix.csv present
"""
import os
import sys
from pathlib import Path

import pytest

# Ensure src/ is on path when running from project root
_PROJECT_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(_PROJECT_ROOT / "src"))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: tests making real network calls — run with -m integration",
    )


@pytest.fixture(scope="session")
def project_root() -> Path:
    return _PROJECT_ROOT


@pytest.fixture(scope="session")
def feature_csv_path(project_root) -> Path:
    p = project_root / "exp_output" / "MLB" / "mlb_feature_matrix.csv"
    if not p.exists():
        pytest.skip(f"Feature CSV not found: {p}. Run scripts/generate_mlb_features.py first.")
    return p


@pytest.fixture(scope="session")
def kalshi_client():
    """Real KalshiMarketClient from environment credentials."""
    from dotenv import load_dotenv
    load_dotenv(_PROJECT_ROOT / ".env")
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
    try:
        return KalshiMarketClient.from_env()
    except Exception as e:
        pytest.skip(f"Kalshi client not available: {e}")


@pytest.fixture(scope="session")
def kalshi_mlb_snapshot(kalshi_client):
    """Live KXMLBHIT snapshot — fetched once per session."""
    from prediction_market_bot.c5_execution.kalshi_client import SERIES_MLB_PLAYER_HITS
    ok, snap = kalshi_client.fetch_player_points_markets(series_ticker=SERIES_MLB_PLAYER_HITS)
    if not ok or snap is None:
        pytest.skip("Kalshi KXMLBHIT fetch failed — check credentials and network.")
    return snap


@pytest.fixture(scope="session")
def feature_df(feature_csv_path):
    """Latest-row-per-player DataFrame from feature CSV."""
    import pandas as pd
    df = pd.read_csv(feature_csv_path, low_memory=False)
    df["game_date_dt"] = pd.to_datetime(df["game_date"], errors="coerce")
    return df.sort_values("game_date_dt").groupby("player_id").last().reset_index()

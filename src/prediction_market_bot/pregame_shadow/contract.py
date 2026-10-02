from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol

@dataclass(frozen=True)
class PregameForecast:
    sport: str                     # "NFL" or "NHL"
    market_type: str               # MarketType member name, e.g. "NFL_MONEYLINE"
    event_ticker: str              # Kalshi event ticker
    market_ticker: str             # Kalshi market ticker; p_yes is for its YES side
    p_yes: float                   # calibrated probability, strictly inside (0, 1)
    as_of_utc: datetime            # information cutoff; nothing after it entered p_yes
    model_id: str                  # frozen model artifact id
    model_sha256: str              # sha256 of the frozen artifact file
    feature_row_sha256: str        # sha256 of the exact feature row used

class PregameForecaster(Protocol):
    sport: str
    def forecast(self, market_ticker: str,
                 as_of_utc: datetime) -> Optional[PregameForecast]: ...

"""W127.3 Part A (B-024): Kalshi RFQ client, DEMO ONLY.

Requests quotes on combo (MVE) markets so the combo arm's cost can be measured as what a maker quotes us. Plumbing: a small
fixed demo size, Kelly 0, hard caps written here. Every call refuses any host except the demo host, whatever BOT_ENV or
LIVE_CAPITAL_ADR say (a combo RFQ on production is real capital, Hard Rule 2). Credentials come from the environment only
(VENUE_API_KEY, VENUE_PRIVATE_KEY_PATH; NFR-05).

Endpoints (docs.kalshi.com, read 2026-11-25; demo support NOT confirmed by the docs, so every call returns the raw API answer):
  POST   /communications/rfqs                              create (market_ticker, contracts_fp, rest_remainder)
  GET    /communications/quotes?rfq_id=..&rfq_user_filter=self
  PUT    /communications/rfqs/{rfq}/quotes/{quote}/accept  {"accepted_side": "yes"|"no"}
  DELETE /communications/rfqs/{rfq}                        cancel
"""
from __future__ import annotations

import os
from typing import Any

import requests

from prediction_market_bot.c5_execution import kalshi_client as KC

DEMO_BASE = KC._KALSHI_DEMO_BASE_URL

# Hard caps. Not configurable by env or argument: raising one is a code change reviewed in a PR.
MAX_RFQS_PER_NIGHT = 12          # RFQs created per UTC day, counted across runs in the ledger file
MAX_RFQS_PER_RUN = 12
MAX_ACCEPTS_PER_RUN = 3          # demo accepts (a fill needs the maker to confirm)
CONTRACTS_FP = "1.00"            # fixed demo size: one contract
REQUEST_TIMEOUT_S = 15


class RfqRefused(Exception):
    pass


class DemoRfqClient:
    def __init__(self, key_id: str, private_key: Any, session: requests.Session | None = None) -> None:
        if not key_id or private_key is None:
            raise RfqRefused("demo credentials missing (VENUE_API_KEY / VENUE_PRIVATE_KEY_PATH)")
        self._key_id, self._pk = key_id, private_key
        self._s = session or requests.Session()
        self._s.headers.update({"Accept": "application/json", "Content-Type": "application/json",
                                "User-Agent": "prediction-market-bot/0.1.0"})
        self.sent = {"create": 0, "accept": 0}

    @classmethod
    def from_env(cls) -> "DemoRfqClient":
        key = os.environ.get("VENUE_API_KEY", "")
        path = os.environ.get("VENUE_PRIVATE_KEY_PATH", "")
        return cls(key, KC._load_private_key(path) if path else None)

    @staticmethod
    def _host_ok() -> None:
        if os.environ.get("BOT_ENV", "").lower() != "paper":
            raise RfqRefused("BOT_ENV must be 'paper' for RFQ calls")
        if KC._kalshi_base_url() != DEMO_BASE:
            raise RfqRefused("non-demo host refused")

    def _call(self, method: str, path: str, body: dict | None = None, params: dict | None = None) -> dict:
        """One signed request, no retry. Returns {ok, status, body} with the raw API answer (so NONE can be recorded verbatim)."""
        self._host_ok()
        headers = KC._auth_headers(self._key_id, self._pk, method, f"/trade-api/v2{path}")
        try:
            r = self._s.request(method, DEMO_BASE + path, json=body, params=params, headers=headers, timeout=REQUEST_TIMEOUT_S)
            try:
                data = r.json() if r.content else {}
            except ValueError:
                data = {"raw": r.text[:300]}
            return {"ok": r.status_code in (200, 201, 204), "status": r.status_code, "body": data}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "status": None, "body": {"error": type(e).__name__, "detail": str(e)[:200]}}

    def market(self, ticker: str) -> dict:
        return self._call("GET", f"/markets/{ticker}")

    def create_combo(self, collection: str, legs: list[dict]) -> dict:
        return self._call("POST", f"/multivariate_event_collections/{collection}",
                          {"selected_markets": legs, "with_market_payload": True})

    def create_rfq(self, market_ticker: str) -> dict:
        if self.sent["create"] >= MAX_RFQS_PER_RUN:
            raise RfqRefused("per-run RFQ cap reached")
        self.sent["create"] += 1
        return self._call("POST", "/communications/rfqs",
                          {"market_ticker": market_ticker, "contracts_fp": CONTRACTS_FP, "rest_remainder": False})

    def quotes(self, rfq_id: str) -> dict:
        return self._call("GET", "/communications/quotes", params={"rfq_id": rfq_id, "rfq_user_filter": "self"})

    def accept(self, rfq_id: str, quote_id: str, side: str) -> dict:
        if side not in ("yes", "no"):
            raise RfqRefused("side must be yes or no")
        if self.sent["accept"] >= MAX_ACCEPTS_PER_RUN:
            raise RfqRefused("per-run accept cap reached")
        self.sent["accept"] += 1
        return self._call("PUT", f"/communications/rfqs/{rfq_id}/quotes/{quote_id}/accept", {"accepted_side": side})

    def get_rfq(self, rfq_id: str) -> dict:
        return self._call("GET", f"/communications/rfqs/{rfq_id}")

    def cancel_rfq(self, rfq_id: str) -> dict:
        return self._call("DELETE", f"/communications/rfqs/{rfq_id}")

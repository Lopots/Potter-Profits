from __future__ import annotations

import json
from datetime import datetime
from datetime import timedelta
from typing import Any

import httpx

from app.core.config import settings


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_polymarket_probability(raw_market: dict[str, Any]) -> float:
    outcome_prices = raw_market.get("outcomePrices")
    if isinstance(outcome_prices, str):
        try:
            parsed = json.loads(outcome_prices)
        except json.JSONDecodeError:
            parsed = []
    elif isinstance(outcome_prices, list):
        parsed = outcome_prices
    else:
        parsed = []

    if parsed:
        return min(max(_safe_float(parsed[0], 0.5), 0.01), 0.99)

    return min(max(_safe_float(raw_market.get("lastTradePrice"), 0.5), 0.01), 0.99)


def fetch_kalshi_markets(limit: int | None = None, status: str = "open") -> list[dict[str, Any]]:
    response = httpx.get(
        f"{settings.kalshi_api_url}/trade-api/v2/markets",
        params={"limit": limit or settings.market_fetch_limit, "status": status},
        timeout=20.0,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("markets", [])


def fetch_kalshi_markets_by_statuses(statuses: list[str], limit_per_status: int | None = None) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for status in statuses:
        try:
            markets = fetch_kalshi_markets(limit=limit_per_status, status=status)
        except httpx.HTTPError:
            continue
        for market in markets:
            ticker = str(market.get("ticker") or "")
            if ticker:
                deduped[ticker] = market
    return list(deduped.values())


def fetch_kalshi_market_candlesticks(
    market_tickers: list[str],
    start_ts: int,
    end_ts: int,
    period_interval: int | None = None,
) -> list[dict[str, Any]]:
    if not market_tickers:
        return []

    response = httpx.get(
        f"{settings.kalshi_api_url}/trade-api/v2/markets/candlesticks",
        params={
            "market_tickers": ",".join(market_tickers[:100]),
            "start_ts": start_ts,
            "end_ts": end_ts,
            "period_interval": period_interval or settings.historical_candle_interval_minutes,
            "include_latest_before_start": "true",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("markets", [])


def fetch_polymarket_markets(limit: int | None = None) -> list[dict[str, Any]]:
    response = httpx.get(
        "https://gamma-api.polymarket.com/markets",
        params={"active": "true", "closed": "false", "limit": limit or settings.market_fetch_limit},
        timeout=20.0,
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, list) else []


def normalize_kalshi_market(raw_market: dict[str, Any]) -> dict[str, Any]:
    probability = _safe_float(raw_market.get("last_price_dollars"), 0.5)
    yes_bid = _safe_float(raw_market.get("yes_bid_dollars"), probability)
    yes_ask = _safe_float(raw_market.get("yes_ask_dollars"), probability)
    midpoint = probability
    if yes_bid > 0 and yes_ask > 0:
        midpoint = (yes_bid + yes_ask) / 2

    probability = min(max(midpoint or probability, 0.01), 0.99)
    volume_24h = _safe_float(raw_market.get("volume_24h_fp"))
    liquidity = _safe_float(raw_market.get("liquidity_dollars"))

    return {
        "external_id": f"kalshi:{raw_market.get('ticker')}",
        "venue": "Kalshi",
        "question": raw_market.get("title") or raw_market.get("subtitle") or raw_market.get("ticker"),
        "category": "Kalshi",
        "status": raw_market.get("status", "open"),
        "market_prob": probability,
        "volume_24h": volume_24h,
        "liquidity": liquidity,
        "metadata_json": {
            "source": "kalshi",
            "ticker": raw_market.get("ticker"),
            "event_ticker": raw_market.get("event_ticker"),
            "subtitle": raw_market.get("subtitle"),
            "yes_bid_dollars": yes_bid,
            "yes_ask_dollars": yes_ask,
            "last_price_dollars": _safe_float(raw_market.get("last_price_dollars"), probability),
            "trend_score": round(probability - 0.5, 4),
            "volume_score": round(min(volume_24h / 100000.0, 1.0), 4),
            "sentiment_score": 0.0,
            "raw": raw_market,
        },
    }


def normalize_polymarket_market(raw_market: dict[str, Any]) -> dict[str, Any]:
    probability = _parse_polymarket_probability(raw_market)
    volume = _safe_float(raw_market.get("volume"))
    liquidity = _safe_float(raw_market.get("liquidity"))

    return {
        "external_id": f"polymarket:{raw_market.get('id')}",
        "venue": "Polymarket",
        "question": raw_market.get("question") or raw_market.get("slug") or raw_market.get("id"),
        "category": raw_market.get("category") or "Polymarket",
        "status": "active" if raw_market.get("active", True) else "closed",
        "market_prob": probability,
        "volume_24h": volume,
        "liquidity": liquidity,
        "metadata_json": {
            "source": "polymarket",
            "market_slug": raw_market.get("slug"),
            "condition_id": raw_market.get("conditionId"),
            "outcomes": raw_market.get("outcomes"),
            "outcome_prices": raw_market.get("outcomePrices"),
            "trend_score": round(probability - 0.5, 4),
            "volume_score": round(min(volume / 100000.0, 1.0), 4),
            "sentiment_score": 0.0,
            "raw": raw_market,
        },
    }


def fetch_live_markets() -> dict[str, list[dict[str, Any]]]:
    enabled_sources = {source.strip().lower() for source in settings.enabled_market_sources.split(",") if source.strip()}
    results: dict[str, list[dict[str, Any]]] = {}

    if "kalshi" in enabled_sources:
        results["kalshi"] = [normalize_kalshi_market(market) for market in fetch_kalshi_markets()]

    if "polymarket" in enabled_sources:
        results["polymarket"] = [normalize_polymarket_market(market) for market in fetch_polymarket_markets()]

    return results


def build_kalshi_backfill_window(days: int | None = None) -> tuple[int, int]:
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=days or settings.historical_backfill_days)
    return int(start_dt.timestamp()), int(end_dt.timestamp())


def get_market_client_status() -> dict[str, dict[str, str | bool]]:
    return {
        "polymarket": {
            "configured": True,
            "base_url": settings.polymarket_api_url,
            "notes": "Public market discovery is available from the Gamma API without authentication.",
        },
        "kalshi": {
            "configured": True,
            "base_url": settings.kalshi_api_url,
            "notes": "Public market data endpoints are available without authentication. Trading still requires auth.",
        },
    }

from __future__ import annotations

import json
from datetime import datetime
from datetime import timedelta
from datetime import timezone
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


def _infer_primary_category(text: str) -> str:
    normalized = text.lower()
    if any(token in normalized for token in ["nba", "mlb", "nfl", "nhl", "wnba", "soccer", "baseball", "basketball", "football", "tennis", "golf"]):
        return "Sports"
    if any(token in normalized for token in ["president", "senate", "house", "governor", "election", "democrat", "republican", "trump", "biden"]):
        return "Politics"
    if any(token in normalized for token in ["cpi", "fed", "rate", "inflation", "recession", "gdp", "jobs", "unemployment", "treasury"]):
        return "Macro"
    return "Current Events"


def _infer_subcategory(text: str) -> str | None:
    normalized = text.lower()
    if "nba" in normalized or any(team in normalized for team in ["lakers", "celtics", "knicks", "bulls", "warriors", "bucks", "suns", "nuggets"]):
        return "NBA"
    if "mlb" in normalized or any(team in normalized for team in ["cubs", "yankees", "dodgers", "mets", "astros", "braves", "red sox", "padres"]):
        return "MLB"
    if "nfl" in normalized or any(team in normalized for team in ["chiefs", "eagles", "cowboys", "ravens", "bills", "49ers", "packers"]):
        return "NFL"
    if "nhl" in normalized or any(team in normalized for team in ["rangers", "bruins", "oilers", "panthers", "maple leafs"]):
        return "NHL"
    if "wnba" in normalized:
        return "WNBA"
    if any(token in normalized for token in ["president", "senate", "house", "governor", "election"]):
        return "Elections"
    if any(token in normalized for token in ["fed", "cpi", "inflation", "rates"]):
        return "Rates & Inflation"
    return None


def _extract_group_label(raw_market: dict[str, Any]) -> str | None:
    subtitle = str(raw_market.get("subtitle") or "").strip()
    if subtitle:
        return subtitle

    event_ticker = str(raw_market.get("event_ticker") or "")
    if "-" in event_ticker:
        return event_ticker.split("-", 1)[0]

    return None


def _extract_game_label(raw_market: dict[str, Any], title: str, subtitle: str | None) -> str | None:
    for candidate in [subtitle, str(raw_market.get("event_title") or "").strip(), str(raw_market.get("series_title") or "").strip()]:
        if candidate and any(token in candidate.lower() for token in [" vs ", " @ ", " at ", " v ", "game", "match", "final", "innings"]):
            return candidate

    event_ticker = str(raw_market.get("event_ticker") or "").strip()
    if event_ticker and "-" in event_ticker:
        return event_ticker.replace("-", " ")

    if any(token in title.lower() for token in [" vs ", " @ ", " at "]):
        return title

    return None


def _extract_market_type(title: str, subtitle: str | None) -> str:
    combined = " ".join(filter(None, [title, subtitle or ""])).lower()

    if any(token in combined for token in ["points", "rebounds", "assists", "hits", "strikeouts", "home runs", "passing", "rushing", "receiving", "1+", "2+", "3+", "10+", "15+", "20+", "25+", "30+"]):
        return "Player Prop"
    if any(token in combined for token in ["over", "under", "wins by", "spread", "run line", "goal line", "totals", "scored"]):
        return "Game Line"
    if any(token in combined for token in ["win", "beat", "moneyline", "to win"]):
        return "Moneyline"

    return "Market"


def _extract_subject_label(title: str) -> str | None:
    normalized = title.strip()
    if ":" in normalized:
        subject = normalized.split(":", 1)[0].replace("yes ", "").replace("no ", "").strip()
        if subject:
            return subject

    lowered = normalized.lower()
    if lowered.startswith("yes "):
        return normalized[4:].strip()
    if lowered.startswith("no "):
        return normalized[3:].strip()

    return None


def _parse_market_datetime(raw_market: dict[str, Any]) -> datetime | None:
    candidate_keys = [
        "close_time",
        "expiration_time",
        "expiration_date",
        "settlement_time",
        "settlement_date",
        "event_date",
        "end_date",
    ]

    for key in candidate_keys:
        raw_value = raw_market.get(key)
        if not raw_value:
            continue
        value = str(raw_value).strip()
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    return None


def _clean_market_title(raw_market: dict[str, Any]) -> tuple[str, str | None]:
    title = str(raw_market.get("title") or raw_market.get("subtitle") or raw_market.get("ticker") or "").strip()
    subtitle = str(raw_market.get("subtitle") or "").strip() or None

    if " | " in title:
        parts = [segment.strip() for segment in title.split("|") if segment.strip()]
        if parts:
            return parts[0], " | ".join(parts[1:]) if len(parts) > 1 else subtitle

    return title, subtitle


def _is_sports_market(raw_market: dict[str, Any]) -> bool:
    title, subtitle = _clean_market_title(raw_market)
    combined_text = " ".join(
        filter(
            None,
            [
                title,
                subtitle or "",
                str(raw_market.get("event_ticker") or ""),
                str(raw_market.get("series_ticker") or ""),
            ],
        )
    )
    return _infer_primary_category(combined_text) == "Sports"


def _is_bundle_market(raw_market: dict[str, Any]) -> bool:
    title, subtitle = _clean_market_title(raw_market)
    combined_text = " ".join(filter(None, [title, subtitle or ""])).lower()
    yes_count = combined_text.count("yes ")
    no_count = combined_text.count("no ")
    segment_count = combined_text.count("|") + combined_text.count(", yes ") + combined_text.count(", no ")
    ticker = str(raw_market.get("ticker") or "").lower()
    event_ticker = str(raw_market.get("event_ticker") or "").lower()

    if "multigame" in ticker or "multigame" in event_ticker:
        return True
    if yes_count >= 4 or no_count >= 4:
        return True
    if segment_count >= 3:
        return True
    return False


def _is_short_dated_market(raw_market: dict[str, Any]) -> bool:
    closes_at = _parse_market_datetime(raw_market)
    if closes_at is None:
        return False
    hours_until_close = (closes_at - datetime.now(timezone.utc)).total_seconds() / 3600
    return 0 <= hours_until_close <= 96


def _sport_priority(raw_market: dict[str, Any]) -> tuple[int, float, float]:
    short_term_bonus = 2 if _is_short_dated_market(raw_market) else 0
    bundle_penalty = -3 if _is_bundle_market(raw_market) else 0
    liquidity = _safe_float(raw_market.get("liquidity_dollars"))
    volume = _safe_float(raw_market.get("volume_24h_fp"))
    return (
        short_term_bonus + bundle_penalty,
        liquidity,
        volume,
    )

def fetch_kalshi_markets_page(limit: int | None = None, status: str = "open", cursor: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
    params: dict[str, Any] = {"limit": limit or settings.market_fetch_limit, "status": status}
    if cursor:
        params["cursor"] = cursor

    response = httpx.get(
        f"{settings.kalshi_api_url}/trade-api/v2/markets",
        params=params,
        timeout=20.0,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("markets", []), payload.get("cursor") or payload.get("next_cursor")


def fetch_kalshi_markets(limit: int | None = None, status: str = "open") -> list[dict[str, Any]]:
    markets, _cursor = fetch_kalshi_markets_page(limit=limit, status=status)
    return markets


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


def fetch_kalshi_sports_markets(total_limit: int | None = None, statuses: list[str] | None = None) -> list[dict[str, Any]]:
    target = total_limit or max(settings.market_fetch_limit, 300)
    statuses = statuses or ["open"]
    deduped: dict[str, dict[str, Any]] = {}

    for status in statuses:
        cursor: str | None = None
        pages_seen = 0

        while len(deduped) < target and pages_seen < 12:
            markets, next_cursor = fetch_kalshi_markets_page(limit=min(target, 200), status=status, cursor=cursor)
            if not markets:
                break

            for market in markets:
                ticker = str(market.get("ticker") or "")
                if not ticker or not _is_sports_market(market) or _is_bundle_market(market):
                    continue
                deduped[ticker] = market

            pages_seen += 1
            if not next_cursor or next_cursor == cursor:
                break
            cursor = str(next_cursor)

    shortlisted = sorted(deduped.values(), key=_sport_priority, reverse=True)
    return shortlisted[:target]


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
    no_probability = round(1 - probability, 4)
    volume_24h = _safe_float(raw_market.get("volume_24h_fp"))
    liquidity = _safe_float(raw_market.get("liquidity_dollars"))
    title, subtitle = _clean_market_title(raw_market)
    combined_text = " ".join(filter(None, [title, subtitle or "", str(raw_market.get("event_ticker") or "")]))
    category = _infer_primary_category(combined_text)
    subcategory = _infer_subcategory(combined_text)
    group_label = _extract_group_label(raw_market)
    game_label = _extract_game_label(raw_market, title, subtitle)
    market_type = _extract_market_type(title, subtitle)
    subject_label = _extract_subject_label(title)

    return {
        "external_id": f"kalshi:{raw_market.get('ticker')}",
        "venue": "Kalshi",
        "question": title,
        "category": category,
        "status": raw_market.get("status", "open"),
        "market_prob": probability,
        "volume_24h": volume_24h,
        "liquidity": liquidity,
        "metadata_json": {
            "source": "kalshi",
            "ticker": raw_market.get("ticker"),
            "event_ticker": raw_market.get("event_ticker"),
            "subtitle": subtitle,
            "subcategory": subcategory,
            "group_label": group_label,
            "game_label": game_label,
            "market_type": market_type,
            "subject_label": subject_label,
            "yes_prob": probability,
            "no_prob": no_probability,
            "yes_label": "Yes",
            "no_label": "No",
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
        results["kalshi"] = [normalize_kalshi_market(market) for market in fetch_kalshi_sports_markets()]

    if "polymarket" in enabled_sources:
        results["polymarket"] = [normalize_polymarket_market(market) for market in fetch_polymarket_markets()]

    return results


def build_kalshi_backfill_window(days: int | None = None) -> tuple[int, int]:
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=days or settings.historical_backfill_days)
    return int(start_dt.timestamp()), int(end_dt.timestamp())


def get_market_client_status() -> dict[str, dict[str, str | bool]]:
    enabled_sources = {source.strip().lower() for source in settings.enabled_market_sources.split(",") if source.strip()}
    status = {
        "kalshi": {
            "configured": "kalshi" in enabled_sources,
            "base_url": settings.kalshi_api_url,
            "notes": "Public market data endpoints are available without authentication. Trading still requires auth.",
        },
    }

    if "polymarket" in enabled_sources:
        status["polymarket"] = {
            "configured": True,
            "base_url": settings.polymarket_api_url,
            "notes": "Public market discovery is available from the Gamma API without authentication.",
        }

    return status

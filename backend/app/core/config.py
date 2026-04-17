from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from pydantic import BaseModel, Field


def _load_loose_env_file(path: str = ".env") -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    current_key: str | None = None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if "=" in line:
            key, value = line.split("=", 1)
            current_key = key.strip()
            values[current_key] = value.strip()
        elif current_key is not None:
            # Allow multiline values such as PEM blocks or accidentally wrapped keys.
            values[current_key] = f"{values[current_key]}\n{line}"

    return values


def _normalize_database_url(url: str) -> str:
    if not url:
        return "sqlite:///./potter.db"

    normalized = url.strip()
    if normalized.startswith("postgresql://"):
        normalized = normalized.replace("postgresql://", "postgresql+psycopg://", 1)

    # Convert patterns like :[password]@ into a URL-encoded password.
    match = re.search(r":\[(.*?)\]@", normalized)
    if match:
        encoded_password = quote(match.group(1), safe="")
        normalized = normalized.replace(match.group(0), f":{encoded_password}@", 1)

    return normalized


def _read_private_key(path_value: str | None, inline_value: str | None) -> str:
    if path_value:
        key_path = Path(path_value)
        if key_path.exists():
            return key_path.read_text(encoding="utf-8").strip()
    return (inline_value or "").strip()


class Settings(BaseModel):
    app_env: str = "development"
    app_name: str = "Potter Profits API"
    debug: bool = True
    frontend_origin: str = "http://localhost:3000"

    database_url: str = "sqlite:///./potter.db"
    local_database_url: str = "sqlite:///./potter_local.db"
    remote_database_url: str = ""
    enable_remote_sync: bool = True
    sync_interval_seconds: int = Field(default=900, ge=60)

    default_market_source: str = "kalshi"
    default_news_source: str = "newsapi"
    enabled_market_sources: str = "kalshi"
    market_fetch_limit: int = Field(default=400, ge=1, le=1000)
    news_fetch_limit: int = Field(default=3, ge=1, le=50)

    polymarket_api_url: str = "https://clob.polymarket.com"
    polymarket_api_key: str = ""

    kalshi_api_url: str = "https://api.elections.kalshi.com"
    kalshi_api_key: str = ""
    kalshi_api_secret: str = ""
    kalshi_private_key_path: str = ""
    kalshi_private_key: str = ""
    kalshi_paper_trading: bool = True
    live_trading_enabled: bool = False
    max_paper_trade_size: float = Field(default=250.0, ge=0)
    max_live_trade_size: float = Field(default=25.0, ge=0)
    daily_loss_limit: float = Field(default=100.0, ge=0)

    newsapi_api_url: str = "https://newsapi.org/v2"
    newsapi_api_key: str = ""

    gnews_api_url: str = "https://gnews.io/api/v4"
    gnews_api_key: str = ""

    reddit_client_id: str = ""
    reddit_client_secret: str = ""

    openai_api_key: str = ""

    enable_scheduler: bool = False
    market_poll_seconds: int = Field(default=300, ge=30)
    news_poll_seconds: int = Field(default=900, ge=60)
    model_poll_seconds: int = Field(default=600, ge=60)
    enable_historical_backfill: bool = True
    historical_backfill_days: int = Field(default=30, ge=1, le=3650)
    historical_backfill_market_limit: int = Field(default=25, ge=1, le=100)
    historical_backfill_interval_seconds: int = Field(default=86400, ge=300)
    historical_candle_interval_minutes: int = Field(default=1440, ge=1)
    enable_model_training: bool = True
    model_train_interval_seconds: int = Field(default=21600, ge=300)
    model_min_training_samples: int = Field(default=50, ge=10)


def _build_settings() -> Settings:
    file_values = _load_loose_env_file(".env")
    merged = {**file_values, **os.environ}

    resolved = {
        "app_env": merged.get("APP_ENV", "development"),
        "app_name": merged.get("APP_NAME", "Potter Profits API"),
        "debug": str(merged.get("DEBUG", "true")).strip().lower() in {"1", "true", "yes", "on"},
        "frontend_origin": merged.get("FRONTEND_ORIGIN", "http://localhost:3000"),
        "database_url": _normalize_database_url(merged.get("DATABASE_URL", "sqlite:///./potter.db")),
        "local_database_url": _normalize_database_url(merged.get("LOCAL_DATABASE_URL", "sqlite:///./potter_local.db")),
        "remote_database_url": _normalize_database_url(merged.get("REMOTE_DATABASE_URL", merged.get("DATABASE_URL", ""))),
        "enable_remote_sync": str(merged.get("ENABLE_REMOTE_SYNC", "true")).strip().lower() in {"1", "true", "yes", "on"},
        "sync_interval_seconds": int(merged.get("SYNC_INTERVAL_SECONDS", 900)),
        "default_market_source": merged.get("DEFAULT_MARKET_SOURCE", "kalshi"),
        "default_news_source": merged.get("DEFAULT_NEWS_SOURCE", "newsapi"),
        "enabled_market_sources": merged.get("ENABLED_MARKET_SOURCES", "kalshi"),
        "market_fetch_limit": int(merged.get("MARKET_FETCH_LIMIT", 400)),
        "news_fetch_limit": int(merged.get("NEWS_FETCH_LIMIT", 3)),
        "polymarket_api_url": merged.get("POLYMARKET_API_URL", "https://clob.polymarket.com"),
        "polymarket_api_key": merged.get("POLYMARKET_API_KEY", ""),
        "kalshi_api_url": merged.get("KALSHI_API_URL", "https://api.elections.kalshi.com"),
        "kalshi_api_key": merged.get("KALSHI_API_KEY", ""),
        "kalshi_api_secret": merged.get("KALSHI_API_SECRET", ""),
        "kalshi_private_key_path": merged.get("KALSHI_PRIVATE_KEY_PATH", ""),
        "kalshi_private_key": _read_private_key(
            merged.get("KALSHI_PRIVATE_KEY_PATH", ""),
            merged.get("KALSHI_PRIVATE_KEY", ""),
        ),
        "kalshi_paper_trading": str(merged.get("KALSHI_PAPER_TRADING", "true")).strip().lower() in {"1", "true", "yes", "on"},
        "live_trading_enabled": str(merged.get("LIVE_TRADING_ENABLED", "false")).strip().lower() in {"1", "true", "yes", "on"},
        "max_paper_trade_size": float(merged.get("MAX_PAPER_TRADE_SIZE", 250)),
        "max_live_trade_size": float(merged.get("MAX_LIVE_TRADE_SIZE", 25)),
        "daily_loss_limit": float(merged.get("DAILY_LOSS_LIMIT", 100)),
        "newsapi_api_url": merged.get("NEWSAPI_API_URL", "https://newsapi.org/v2"),
        "newsapi_api_key": merged.get("NEWSAPI_API_KEY", ""),
        "gnews_api_url": merged.get("GNEWS_API_URL", "https://gnews.io/api/v4"),
        "gnews_api_key": merged.get("GNEWS_API_KEY", ""),
        "reddit_client_id": merged.get("REDDIT_CLIENT_ID", ""),
        "reddit_client_secret": merged.get("REDDIT_CLIENT_SECRET", ""),
        "openai_api_key": merged.get("OPENAI_API_KEY", ""),
        "enable_scheduler": str(merged.get("ENABLE_SCHEDULER", "false")).strip().lower() in {"1", "true", "yes", "on"},
        "market_poll_seconds": int(merged.get("MARKET_POLL_SECONDS", 300)),
        "news_poll_seconds": int(merged.get("NEWS_POLL_SECONDS", 1800)),
        "model_poll_seconds": int(merged.get("MODEL_POLL_SECONDS", 600)),
        "enable_historical_backfill": str(merged.get("ENABLE_HISTORICAL_BACKFILL", "true")).strip().lower() in {"1", "true", "yes", "on"},
        "historical_backfill_days": int(merged.get("HISTORICAL_BACKFILL_DAYS", 30)),
        "historical_backfill_market_limit": int(merged.get("HISTORICAL_BACKFILL_MARKET_LIMIT", 25)),
        "historical_backfill_interval_seconds": int(merged.get("HISTORICAL_BACKFILL_INTERVAL_SECONDS", 86400)),
        "historical_candle_interval_minutes": int(merged.get("HISTORICAL_CANDLE_INTERVAL_MINUTES", 1440)),
        "enable_model_training": str(merged.get("ENABLE_MODEL_TRAINING", "true")).strip().lower() in {"1", "true", "yes", "on"},
        "model_train_interval_seconds": int(merged.get("MODEL_TRAIN_INTERVAL_SECONDS", 21600)),
        "model_min_training_samples": int(merged.get("MODEL_MIN_TRAINING_SAMPLES", 50)),
    }

    return Settings(**resolved)


@lru_cache
def get_settings() -> Settings:
    return _build_settings()


settings = get_settings()

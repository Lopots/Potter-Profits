from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Market(Base):
    __tablename__ = "markets"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    venue: Mapped[str] = mapped_column(String(80), index=True)
    question: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    current_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    liquidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    market_external_id: Mapped[str] = mapped_column(String(255), index=True)
    venue: Mapped[str] = mapped_column(String(80), index=True)
    probability: Mapped[float] = mapped_column(Float)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    liquidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(80), index=True)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MarketNewsLink(Base):
    __tablename__ = "market_news_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    market_external_id: Mapped[str] = mapped_column(String(255), index=True)
    news_external_id: Mapped[str] = mapped_column(String(255), index=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    match_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    market_external_id: Mapped[str] = mapped_column(String(255), index=True)
    deterministic_edge: Mapped[float] = mapped_column(Float)
    ml_adjustment: Mapped[float] = mapped_column(Float)
    ai_adjustment: Mapped[float] = mapped_column(Float)
    final_probability: Mapped[float] = mapped_column(Float)
    final_score: Mapped[float] = mapped_column(Float)
    action: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[int] = mapped_column(Integer)
    pricing_summary: Mapped[str] = mapped_column(Text)
    ml_summary: Mapped[str] = mapped_column(Text)
    ai_summary: Mapped[str] = mapped_column(Text)
    raw_features: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class TradeAction(Base):
    __tablename__ = "trade_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    market_external_id: Mapped[str] = mapped_column(String(255), index=True)
    venue: Mapped[str] = mapped_column(String(80))
    side: Mapped[str] = mapped_column(String(16))
    stake: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    rationale: Mapped[str] = mapped_column(Text)
    is_paper: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    market_external_id: Mapped[str] = mapped_column(String(255), index=True)
    venue: Mapped[str] = mapped_column(String(80))
    side: Mapped[str] = mapped_column(String(16))
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    average_entry_price: Mapped[float] = mapped_column(Float, default=0.0)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    message: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(80), index=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    feature_count: Mapped[int] = mapped_column(Integer, default=0)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    metrics_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ModelArtifact(Base):
    __tablename__ = "model_artifacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(80), index=True)
    version: Mapped[str] = mapped_column(String(40), index=True)
    feature_names: Mapped[list] = mapped_column(JSON, default=list)
    coefficients: Mapped[list] = mapped_column(JSON, default=list)
    intercept: Mapped[float] = mapped_column(Float, default=0.0)
    metrics_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

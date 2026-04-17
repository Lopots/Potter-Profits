from typing import Literal

from pydantic import BaseModel, Field


ActionType = Literal["BUY", "SELL", "HOLD"]
TradeStatus = Literal["queued", "simulated", "blocked"]


class Market(BaseModel):
    id: str
    venue: str
    question: str
    category: str
    market_prob: float = Field(ge=0, le=1)
    potter_prob: float = Field(ge=0, le=1)
    sentiment_score: float = Field(ge=-1, le=1)
    trend_score: float = Field(ge=-1, le=1)
    volume_score: float = Field(ge=-1, le=1)
    confidence: int = Field(ge=0, le=100)
    edge: float
    action: ActionType
    volume_24h: int
    liquidity: int
    deterministic_edge: float
    ml_confidence_adjustment: float
    ai_news_adjustment: float
    final_score: float
    pricing_summary: str
    ml_summary: str
    ai_summary: str


class MarketSnapshot(BaseModel):
    total_markets: int
    buy_signals: int
    sell_signals: int
    average_edge: float
    strongest_edge: float


class PotterThought(BaseModel):
    timestamp: str
    title: str
    detail: str
    tone: Literal["info", "success", "warning"]


class RiskGuardrail(BaseModel):
    name: str
    status: Literal["active", "watch", "disabled"]
    detail: str


class PotterState(BaseModel):
    mode: Literal["paper", "live-disabled"]
    autonomy_level: Literal["assistive", "paper-auto", "live-auto-locked"]
    mission: str
    reasoning_summary: str
    next_action: str
    guardrails: list[RiskGuardrail]
    thoughts: list[PotterThought]


class ModelLayer(BaseModel):
    name: str
    role: str
    weight: str
    purpose: str
    examples: list[str]


class Trade(BaseModel):
    id: str
    timestamp: str
    market_id: str
    market_question: str
    venue: str
    side: ActionType
    stake: float
    edge_at_entry: float
    confidence: int
    status: TradeStatus
    rationale: str


class DashboardResponse(BaseModel):
    snapshot: MarketSnapshot
    model_layers: list[ModelLayer]
    markets: list[Market]
    potter: PotterState
    trades: list[Trade]


class SourceStatus(BaseModel):
    configured: bool
    base_url: str
    notes: str


class ExecutionStatus(BaseModel):
    paper_trading_enabled: bool
    live_trading_enabled: bool
    execution_venue: str
    max_paper_trade_size: float
    max_live_trade_size: float
    daily_loss_limit: float
    live_trading_lock_reason: str | None


class AuditEvent(BaseModel):
    event_type: str
    message: str
    created_at: str


class PipelineStatusResponse(BaseModel):
    database_url: str
    remote_database_url: str
    market_sources: dict[str, SourceStatus]
    news_sources: dict[str, SourceStatus]
    execution: ExecutionStatus
    openai_configured: bool
    scheduler_enabled: bool
    remote_sync_enabled: bool
    historical_backfill_enabled: bool
    model_training_enabled: bool
    market_poll_seconds: int
    news_poll_seconds: int
    model_poll_seconds: int
    sync_interval_seconds: int
    historical_backfill_interval_seconds: int
    model_train_interval_seconds: int
    latest_market_capture: str | None
    latest_news_capture: str | None
    latest_model_run: str | None
    latest_training_run: str | None
    latest_remote_sync: str | None
    latest_remote_sync_status: str | None
    market_count: int
    news_count: int
    model_run_count: int
    training_run_count: int
    recent_audit_events: list[AuditEvent]


class PipelineRunResponse(BaseModel):
    job: str
    status: str
    timestamp: str
    source: str | None = None
    layers: list[str] | None = None
    records_written: int | None = None

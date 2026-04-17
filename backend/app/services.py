from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from .data import load_dashboard
from .execution import get_execution_status
from .models import Market as MarketRecord
from .models import MarketPrice
from .models import ModelArtifact
from .models import ModelRun as ModelRunRecord
from .models import TradeAction
from .pipeline import backfill_historical_market_data, get_pipeline_status, ingest_market_data, ingest_news_data, run_model_pipeline, sync_local_to_remote, train_probability_model
from .schemas import (
    DashboardResponse,
    Market,
    MarketSnapshot,
    PipelineRunResponse,
    PipelineStatusResponse,
    PotterState,
    PotterThought,
    RiskGuardrail,
    Trade,
)


def get_dashboard_data(db: Session | None = None) -> DashboardResponse:
    fallback = load_dashboard()
    if db is None:
        return fallback

    market_rows = db.scalars(select(MarketRecord).where(MarketRecord.status == "active").order_by(MarketRecord.created_at)).all()
    if not market_rows:
        return fallback
    live_market_rows = [market for market in market_rows if not (market.metadata_json or {}).get("seeded")]
    if live_market_rows:
        market_rows = live_market_rows

    latest_model_runs: dict[str, ModelRunRecord] = {}
    for model_run in db.scalars(select(ModelRunRecord).order_by(desc(ModelRunRecord.created_at))).all():
        latest_model_runs.setdefault(model_run.market_external_id, model_run)

    price_snapshots: dict[str, list[MarketPrice]] = {}
    for price_row in db.scalars(select(MarketPrice).order_by(desc(MarketPrice.captured_at))).all():
        bucket = price_snapshots.setdefault(price_row.market_external_id, [])
        if len(bucket) < 2:
            bucket.append(price_row)

    def _split_question(question: str) -> tuple[str, str | None, list[str]]:
        cleaned = " ".join(question.replace("  ", " ").split())
        normalized = cleaned.replace(",yes", ", yes").replace(",no", ", no").replace(";yes", "; yes").replace(";no", "; no")
        if len(normalized) > 92 and "," in normalized:
            segments = [segment.strip() for segment in normalized.split(",") if segment.strip()]
        elif len(normalized) > 92 and ";" in normalized:
            segments = [segment.strip() for segment in normalized.split(";") if segment.strip()]
        else:
            segments = [normalized]

        display_title = segments[0]
        subtitle = " | ".join(segments[1:3]) if len(segments) > 1 else None
        return display_title, subtitle, segments[:6]

    dashboard_markets: list[Market] = []
    for market_row in market_rows:
        model_run = latest_model_runs.get(market_row.external_id)
        metadata = market_row.metadata_json or {}
        market_prob = float(market_row.current_probability or 0.5)
        potter_prob = float(model_run.final_probability) if model_run else float(metadata.get("potter_probability", market_prob))
        recent_prices = price_snapshots.get(market_row.external_id, [])
        latest_price = recent_prices[0] if recent_prices else None
        previous_price = recent_prices[1] if len(recent_prices) > 1 else None
        display_title, subtitle, question_segments = _split_question(market_row.question)

        dashboard_markets.append(
            Market(
                id=market_row.external_id,
                venue=market_row.venue,
                question=market_row.question,
                display_title=display_title,
                subtitle=subtitle,
                question_segments=question_segments,
                category=market_row.category,
                market_prob=market_prob,
                previous_market_prob=float(previous_price.probability) if previous_price else None,
                potter_prob=potter_prob,
                sentiment_score=float(metadata.get("sentiment_score", 0.0)),
                trend_score=float(metadata.get("trend_score", 0.0)),
                volume_score=float(metadata.get("volume_score", 0.0)),
                confidence=int(model_run.confidence if model_run else 55),
                edge=round(potter_prob - market_prob, 4),
                action=model_run.action if model_run else "HOLD",
                volume_24h=int(market_row.volume_24h or 0),
                liquidity=int(market_row.liquidity or 0),
                deterministic_edge=float(model_run.deterministic_edge if model_run else 0.0),
                ml_confidence_adjustment=float(model_run.ml_adjustment if model_run else 0.0),
                ai_news_adjustment=float(model_run.ai_adjustment if model_run else 0.0),
                final_score=float(model_run.final_score if model_run else 0.0),
                pricing_summary=model_run.pricing_summary if model_run else "No model run has been stored yet.",
                ml_summary=model_run.ml_summary if model_run else "ML validation has not been run yet.",
                ai_summary=model_run.ai_summary if model_run else "AI/news context has not been run yet.",
                latest_pull_at=latest_price.captured_at.isoformat() if latest_price else None,
                previous_pull_at=previous_price.captured_at.isoformat() if previous_price else None,
                latest_model_at=model_run.created_at.isoformat() if model_run else None,
                price_change=round(market_prob - float(previous_price.probability), 4) if previous_price else 0.0,
            )
        )

    snapshot = MarketSnapshot(
        total_markets=len(dashboard_markets),
        buy_signals=len([market for market in dashboard_markets if market.action == "BUY"]),
        sell_signals=len([market for market in dashboard_markets if market.action == "SELL"]),
        average_edge=round(sum(m.edge for m in dashboard_markets) / len(dashboard_markets), 3),
        strongest_edge=max(abs(m.edge) for m in dashboard_markets),
    )

    trade_rows = db.scalars(select(TradeAction).order_by(desc(TradeAction.created_at)).limit(12)).all()
    trades = [
        Trade(
            id=f"trade-{trade_row.id}",
            timestamp=trade_row.created_at.strftime("%Y-%m-%d %H:%M UTC"),
            market_id=trade_row.market_external_id,
            market_question=next(
                (market.question for market in dashboard_markets if market.id == trade_row.market_external_id),
                trade_row.market_external_id,
            ),
            venue=trade_row.venue,
            side=trade_row.side,
            stake=trade_row.stake,
            edge_at_entry=next(
                (market.final_score for market in dashboard_markets if market.id == trade_row.market_external_id),
                0.0,
            ),
            confidence=next(
                (market.confidence for market in dashboard_markets if market.id == trade_row.market_external_id),
                55,
            ),
            status=trade_row.status,
            rationale=trade_row.rationale,
        )
        for trade_row in trade_rows
    ]

    execution = get_execution_status()
    potter = PotterState(
        mode="paper" if execution["paper_trading_enabled"] else "live-disabled",
        autonomy_level="paper-auto" if execution["paper_trading_enabled"] else "live-auto-locked",
        mission="Monitor active markets, score mispricing with math first, validate edges with ML, and use AI as a supporting context layer.",
        reasoning_summary=(
            "Potter is now reading stored market snapshots, linked news context, and the latest model runs from the database."
        ),
        next_action=(
            next(
                (
                    f"Review {market.question} because the latest stored model score is {market.final_score:+.1%}."
                    for market in dashboard_markets
                    if market.action != "HOLD"
                ),
                "Run the model pipeline after ingesting more market and news data.",
            )
        ),
        guardrails=[
            RiskGuardrail(
                name="Live Capital Lock",
                status="active" if not execution["live_trading_enabled"] else "watch",
                detail=execution["live_trading_lock_reason"] or "Live trading is enabled.",
            ),
            RiskGuardrail(
                name="Paper Trade Sizing",
                status="active",
                detail=f"Paper trades are capped at ${execution['max_paper_trade_size']:.0f}.",
            ),
            RiskGuardrail(
                name="Daily Loss Limit",
                status="watch",
                detail=f"Configured daily loss limit is ${execution['daily_loss_limit']:.0f}.",
            ),
        ],
        thoughts=[
            PotterThought(
                timestamp="Stored",
                title="Market snapshots loaded",
                detail=f"Loaded {len(dashboard_markets)} active markets from the database.",
                tone="info",
            ),
            PotterThought(
                timestamp="Stored",
                title="Model runs available",
                detail=f"Found {len(latest_model_runs)} latest model outputs to compare against live venue pricing.",
                tone="success" if latest_model_runs else "warning",
            ),
            PotterThought(
                timestamp="Stored",
                title="Training artifact status",
                detail=(
                    "A trained ML artifact is available and contributes to the probability adjustment."
                    if db.scalar(select(ModelArtifact).order_by(desc(ModelArtifact.created_at)).limit(1))
                    else "No trained ML artifact is stored yet, so Potter is using rule-based ML adjustments."
                ),
                tone="success" if db.scalar(select(ModelArtifact).order_by(desc(ModelArtifact.created_at)).limit(1)) else "warning",
            ),
            PotterThought(
                timestamp="Stored",
                title="Execution remains guarded",
                detail=execution["live_trading_lock_reason"] or "Paper mode stays active until you deliberately unlock live trading.",
                tone="warning" if not execution["live_trading_enabled"] else "info",
            ),
        ],
    )

    return DashboardResponse(
        snapshot=snapshot,
        model_layers=fallback.model_layers,
        markets=dashboard_markets,
        potter=potter,
        trades=trades,
    )


def get_system_status(db: Session) -> PipelineStatusResponse:
    return PipelineStatusResponse(**get_pipeline_status(db))


def run_market_ingestion(db: Session) -> PipelineRunResponse:
    return PipelineRunResponse(**ingest_market_data(db))


def run_news_ingestion_job(db: Session) -> PipelineRunResponse:
    return PipelineRunResponse(**ingest_news_data(db))


def run_model_pipeline_job(db: Session) -> PipelineRunResponse:
    return PipelineRunResponse(**run_model_pipeline(db))


def run_historical_backfill_job(db: Session) -> PipelineRunResponse:
    return PipelineRunResponse(**backfill_historical_market_data(db))


def run_model_training_job(db: Session) -> PipelineRunResponse:
    return PipelineRunResponse(**train_probability_model(db))


def run_remote_sync_job(db: Session) -> PipelineRunResponse:
    return PipelineRunResponse(**sync_local_to_remote(db))

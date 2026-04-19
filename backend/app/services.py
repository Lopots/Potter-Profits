import re
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from .core.config import settings
from .data import build_empty_dashboard, build_model_layers, load_dashboard
from .execution import get_execution_status
from .models import Market as MarketRecord
from .models import MarketPrice
from .models import ModelArtifact
from .models import ModelRun as ModelRunRecord
from .models import NewsItem
from .models import AuditLog
from .models import TradeAction
from .pipeline import backfill_historical_market_data, get_pipeline_status, ingest_market_data, ingest_news_data, run_model_pipeline, sync_local_to_remote, train_probability_model
from .schemas import (
    RawAuditLogRow,
    DashboardResponse,
    Market,
    MarketSnapshot,
    PerformancePoint,
    PipelineRunResponse,
    PipelineStatusResponse,
    PortfolioSummary,
    PotterState,
    PotterThought,
    PotterChatResponse,
    RawDataResponse,
    RawMarketPriceRow,
    RawMarketRow,
    RawModelRunRow,
    RawNewsItemRow,
    RiskGuardrail,
    Trade,
    RawTradeActionRow,
)


def _utc_iso(value):
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _price_at_or_before(price_rows: list[MarketPrice], timestamp, fallback: float) -> float:
    for row in reversed(price_rows):
        if row.captured_at <= timestamp:
            return float(row.probability)
    return fallback


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9\s]+", " ", value.lower()).strip()


def _build_market_blurb(market: Market) -> str:
    yes_prob = market.yes_prob if market.yes_prob is not None else market.market_prob
    no_prob = market.no_prob if market.no_prob is not None else 1 - market.market_prob
    action_side = market.yes_label if market.edge >= 0 else market.no_label
    return (
        f"{market.display_title}: {market.yes_label} is {yes_prob:.1%}, {market.no_label} is {no_prob:.1%}, "
        f"Potter's true yes estimate is {market.potter_prob:.1%}, mispricing is {market.mispricing:+.1%}, "
        f"fee-adjusted EV is {market.fee_adjusted_ev:+.1%} on Yes and {market.fee_adjusted_ev_no:+.1%} on No, "
        f"and the current action is {market.action} leaning toward {action_side}. "
        f"Math says: {market.pricing_summary} ML says: {market.ml_summary} AI/news says: {market.ai_summary}"
    )


def _market_match_score(message: str, market: Market) -> int:
    query_tokens = {token for token in _normalize_text(message).split() if len(token) > 2}
    market_tokens = {
        token
        for token in _normalize_text(
            " ".join(
                filter(
                    None,
                    [
                        market.display_title,
                        market.question,
                        market.subtitle,
                        market.group_label,
                        market.category,
                        market.subcategory,
                    ],
                )
            )
        ).split()
        if len(token) > 2
    }
    return len(query_tokens & market_tokens)


def get_dashboard_data(db: Session | None = None) -> DashboardResponse:
    if db is None:
        return build_empty_dashboard()

    market_rows = db.scalars(
        select(MarketRecord)
        .where(MarketRecord.status.in_(["active", "open"]), MarketRecord.category == "Sports")
        .order_by(MarketRecord.created_at)
    ).all()
    if not market_rows:
        return build_empty_dashboard()
    live_market_rows = [market for market in market_rows if not (market.metadata_json or {}).get("seeded")]
    if live_market_rows:
        market_rows = live_market_rows

    latest_model_runs: dict[str, ModelRunRecord] = {}
    for model_run in db.scalars(select(ModelRunRecord).order_by(desc(ModelRunRecord.created_at))).all():
        latest_model_runs.setdefault(model_run.market_external_id, model_run)

    price_snapshots: dict[str, list[MarketPrice]] = {}
    price_history: dict[str, list[MarketPrice]] = {}
    all_price_rows = db.scalars(select(MarketPrice).order_by(MarketPrice.captured_at)).all()
    for price_row in all_price_rows:
        price_history.setdefault(price_row.market_external_id, []).append(price_row)
    for market_external_id, rows in price_history.items():
        price_snapshots[market_external_id] = list(reversed(rows[-2:]))

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
        fee_rate = float(
            model_run.raw_features.get("fee_rate", settings.prediction_market_fee_rate)
            if model_run and model_run.raw_features
            else settings.prediction_market_fee_rate
        )
        mispricing = float(
            model_run.raw_features.get("mispricing", potter_prob - market_prob)
            if model_run and model_run.raw_features
            else potter_prob - market_prob
        )
        expected_value = float(
            model_run.raw_features.get("expected_value_yes", potter_prob - market_prob)
            if model_run and model_run.raw_features
            else potter_prob - market_prob
        )
        expected_value_no = float(
            model_run.raw_features.get("expected_value_no", (1 - potter_prob) - (1 - market_prob))
            if model_run and model_run.raw_features
            else (1 - potter_prob) - (1 - market_prob)
        )
        fee_adjusted_ev = float(
            model_run.raw_features.get("fee_adjusted_ev_yes", expected_value - fee_rate)
            if model_run and model_run.raw_features
            else expected_value - fee_rate
        )
        fee_adjusted_ev_no = float(
            model_run.raw_features.get("fee_adjusted_ev_no", expected_value_no - fee_rate)
            if model_run and model_run.raw_features
            else expected_value_no - fee_rate
        )
        trade_score = float(
            model_run.raw_features.get("trade_score", 0.0)
            if model_run and model_run.raw_features
            else 0.0
        )
        yes_prob = float(metadata.get("yes_prob", market_prob))
        no_prob = float(metadata.get("no_prob", 1 - market_prob))
        recent_prices = price_snapshots.get(market_row.external_id, [])
        latest_price = recent_prices[0] if recent_prices else None
        previous_price = recent_prices[1] if len(recent_prices) > 1 else None
        display_title, subtitle, question_segments = _split_question(market_row.question)
        subtitle = metadata.get("subtitle") or subtitle

        dashboard_markets.append(
            Market(
                id=market_row.external_id,
                venue=market_row.venue,
                question=market_row.question,
                display_title=display_title,
                subtitle=subtitle,
                question_segments=question_segments,
                category=market_row.category,
                subcategory=metadata.get("subcategory"),
                group_label=metadata.get("group_label"),
                game_label=metadata.get("game_label"),
                market_type=metadata.get("market_type"),
                subject_label=metadata.get("subject_label"),
                market_prob=market_prob,
                previous_market_prob=float(previous_price.probability) if previous_price else None,
                potter_prob=potter_prob,
                yes_prob=yes_prob,
                no_prob=no_prob,
                yes_label=str(metadata.get("yes_label", "Yes")),
                no_label=str(metadata.get("no_label", "No")),
                sentiment_score=float(metadata.get("sentiment_score", 0.0)),
                trend_score=float(metadata.get("trend_score", 0.0)),
                volume_score=float(metadata.get("volume_score", 0.0)),
                confidence=int(model_run.confidence if model_run else 55),
                edge=round(mispricing, 4),
                mispricing=round(mispricing, 4),
                expected_value=round(expected_value, 4),
                expected_value_no=round(expected_value_no, 4),
                fee_adjusted_ev=round(fee_adjusted_ev, 4),
                fee_adjusted_ev_no=round(fee_adjusted_ev_no, 4),
                trade_score=round(trade_score, 4),
                fee_rate=round(fee_rate, 4),
                action_threshold=round(
                    float(model_run.raw_features.get("action_edge_threshold", 0.10))
                    if model_run and model_run.raw_features
                    else 0.10,
                    4,
                ),
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
                latest_pull_at=_utc_iso(latest_price.captured_at) if latest_price else None,
                previous_pull_at=_utc_iso(previous_price.captured_at) if previous_price else None,
                latest_model_at=_utc_iso(model_run.created_at) if model_run else None,
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

    trade_action_rows = db.scalars(select(TradeAction).order_by(TradeAction.created_at)).all()
    eastern = ZoneInfo("America/New_York")
    starting_bankroll = 10000.0
    bank_balance = starting_bankroll
    realized_pnl = 0.0
    open_positions: dict[str, dict[str, float | str | datetime]] = {}
    performance_points: list[PerformancePoint] = []
    trades: list[Trade] = []
    current_probabilities = {market.id: market.market_prob for market in dashboard_markets}

    for trade_row in trade_action_rows:
        if trade_row.status != "simulated" or trade_row.side == "HOLD":
            continue

        market_id = trade_row.market_external_id
        market_question = next(
            (market.question for market in dashboard_markets if market.id == market_id),
            market_id,
        )
        confidence = next(
            (market.confidence for market in dashboard_markets if market.id == market_id),
            55,
        )
        edge_at_entry = next(
            (market.final_score for market in dashboard_markets if market.id == market_id),
            0.0,
        )
        current_probability = current_probabilities.get(market_id, 0.5)
        entry_probability = _price_at_or_before(price_history.get(market_id, []), trade_row.created_at, current_probability)

        if trade_row.side == "BUY":
            if market_id in open_positions:
                continue
            bank_balance -= trade_row.stake
            open_positions[market_id] = {
                "entry_probability": entry_probability,
                "stake": trade_row.stake,
                "opened_at": trade_row.created_at,
                "venue": trade_row.venue,
                "market_question": market_question,
                "edge_at_entry": edge_at_entry,
                "confidence": confidence,
                "rationale": trade_row.rationale,
            }
        elif trade_row.side == "SELL":
            position = open_positions.pop(market_id, None)
            if position is None:
                continue
            exit_probability = entry_probability
            stake = float(position["stake"])
            realized_trade_pnl = (exit_probability - float(position["entry_probability"])) * stake
            bank_balance += stake + realized_trade_pnl
            realized_pnl += realized_trade_pnl
            trades.append(
                Trade(
                    id=f"trade-{trade_row.id}",
                    timestamp=trade_row.created_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(eastern).strftime("%Y-%m-%d %I:%M %p ET"),
                    market_id=market_id,
                    market_question=str(position["market_question"]),
                    venue=str(position["venue"]),
                    side="SELL",
                    stake=stake,
                    edge_at_entry=float(position["edge_at_entry"]),
                    confidence=int(position["confidence"]),
                    status="closed",
                    rationale=trade_row.rationale,
                    entry_probability=float(position["entry_probability"]),
                    exit_probability=exit_probability,
                    profit_loss=realized_trade_pnl,
                )
            )

        active_capital = sum(float(position["stake"]) for position in open_positions.values())
        unrealized_pnl = sum(
            (current_probabilities.get(position_market_id, 0.5) - float(position["entry_probability"])) * float(position["stake"])
            for position_market_id, position in open_positions.items()
        )
        performance_points.append(
            PerformancePoint(
                timestamp=_utc_iso(trade_row.created_at),
                equity=round(bank_balance + active_capital + unrealized_pnl, 2),
                bank_balance=round(bank_balance, 2),
                active_capital=round(active_capital, 2),
            )
        )

    active_capital = sum(float(position["stake"]) for position in open_positions.values())
    unrealized_pnl = sum(
        (current_probabilities.get(position_market_id, 0.5) - float(position["entry_probability"])) * float(position["stake"])
        for position_market_id, position in open_positions.items()
    )
    total_equity = bank_balance + active_capital + unrealized_pnl
    fallback_timestamp = (
        _utc_iso(latest_model_run.created_at)
        if latest_model_run
        else _utc_iso(max((market.latest_pull_at for market in dashboard_markets if market.latest_pull_at), default=None))
    )
    if not performance_points:
        performance_points.append(
            PerformancePoint(
                timestamp=fallback_timestamp or "Not yet",
                equity=round(total_equity, 2),
                bank_balance=round(bank_balance, 2),
                active_capital=round(active_capital, 2),
            )
        )

    portfolio = PortfolioSummary(
        starting_bankroll=starting_bankroll,
        bank_balance=round(bank_balance, 2),
        active_capital=round(active_capital, 2),
        realized_pnl=round(realized_pnl, 2),
        unrealized_pnl=round(unrealized_pnl, 2),
        total_equity=round(total_equity, 2),
        completed_trades=len(trades),
        open_positions=len(open_positions),
        performance_points=performance_points[-30:],
    )

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
        model_layers=build_model_layers(),
        markets=dashboard_markets,
        potter=potter,
        trades=trades,
        portfolio=portfolio,
    )


def get_system_status(db: Session) -> PipelineStatusResponse:
    return PipelineStatusResponse(**get_pipeline_status(db))


def get_raw_data(db: Session) -> RawDataResponse:
    sports_market_ids = set(
        db.scalars(
            select(MarketRecord.external_id).where(
                MarketRecord.venue == "Kalshi",
                MarketRecord.category == "Sports",
            )
        ).all()
    )

    market_rows = db.scalars(
        select(MarketRecord)
        .where(MarketRecord.external_id.in_(sports_market_ids))
        .order_by(desc(MarketRecord.updated_at))
        .limit(100)
    ).all()
    price_rows = db.scalars(
        select(MarketPrice)
        .where(MarketPrice.market_external_id.in_(sports_market_ids))
        .order_by(desc(MarketPrice.captured_at))
        .limit(150)
    ).all()
    news_rows = db.scalars(select(NewsItem).order_by(desc(NewsItem.created_at)).limit(100)).all()
    model_rows = db.scalars(
        select(ModelRunRecord)
        .where(ModelRunRecord.market_external_id.in_(sports_market_ids))
        .order_by(desc(ModelRunRecord.created_at))
        .limit(150)
    ).all()
    trade_rows = db.scalars(
        select(TradeAction)
        .where(TradeAction.market_external_id.in_(sports_market_ids))
        .order_by(desc(TradeAction.created_at))
        .limit(150)
    ).all()
    audit_rows = db.scalars(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(150)).all()

    return RawDataResponse(
        markets=[
            RawMarketRow(
                external_id=row.external_id,
                venue=row.venue,
                question=row.question,
                category=row.category,
                status=row.status,
                current_probability=row.current_probability,
                volume_24h=row.volume_24h,
                liquidity=row.liquidity,
                created_at=_utc_iso(row.created_at),
                updated_at=_utc_iso(row.updated_at),
            )
            for row in market_rows
        ],
        market_prices=[
            RawMarketPriceRow(
                market_external_id=row.market_external_id,
                venue=row.venue,
                probability=row.probability,
                price=row.price,
                volume_24h=row.volume_24h,
                liquidity=row.liquidity,
                captured_at=_utc_iso(row.captured_at),
            )
            for row in price_rows
        ],
        news_items=[
            RawNewsItemRow(
                source=row.source,
                external_id=row.external_id,
                title=row.title,
                url=row.url,
                summary=row.summary,
                published_at=_utc_iso(row.published_at) if row.published_at else None,
                created_at=_utc_iso(row.created_at),
            )
            for row in news_rows
        ],
        model_runs=[
            RawModelRunRow(
                market_external_id=row.market_external_id,
                deterministic_edge=row.deterministic_edge,
                ml_adjustment=row.ml_adjustment,
                ai_adjustment=row.ai_adjustment,
                final_probability=row.final_probability,
                final_score=row.final_score,
                mispricing=float((row.raw_features or {}).get("mispricing", row.final_probability - ((row.raw_features or {}).get("market_probability", row.final_probability)))),
                expected_value=float((row.raw_features or {}).get("expected_value_yes", 0.0)),
                expected_value_no=float((row.raw_features or {}).get("expected_value_no", 0.0)),
                fee_adjusted_ev=float((row.raw_features or {}).get("fee_adjusted_ev_yes", 0.0)),
                fee_adjusted_ev_no=float((row.raw_features or {}).get("fee_adjusted_ev_no", 0.0)),
                trade_score=float((row.raw_features or {}).get("trade_score", 0.0)),
                action=row.action,
                confidence=row.confidence,
                created_at=_utc_iso(row.created_at),
            )
            for row in model_rows
        ],
        trade_actions=[
            RawTradeActionRow(
                market_external_id=row.market_external_id,
                venue=row.venue,
                side=row.side,
                stake=row.stake,
                status=row.status,
                rationale=row.rationale,
                is_paper=row.is_paper,
                created_at=_utc_iso(row.created_at),
            )
            for row in trade_rows
        ],
        audit_logs=[
            RawAuditLogRow(
                event_type=row.event_type,
                message=row.message,
                created_at=_utc_iso(row.created_at),
            )
            for row in audit_rows
        ],
    )


def answer_potter_chat(db: Session, message: str) -> PotterChatResponse:
    dashboard = get_dashboard_data(db)
    system_status = get_system_status(db)
    normalized_message = _normalize_text(message)
    completed_trades = [trade for trade in dashboard.trades if trade.status == "closed"]
    portfolio = dashboard.portfolio
    ranked_markets = sorted(
        dashboard.markets,
        key=lambda market: (_market_match_score(normalized_message, market), abs(market.edge)),
        reverse=True,
    )
    matched_markets = [market for market in ranked_markets if _market_match_score(normalized_message, market) > 0][:3]

    suggested_prompts = [
        "How does your process work?",
        "What is my paper portfolio doing right now?",
        "What market has the strongest edge right now?",
        "Why do you like this market?",
    ]

    if any(keyword in normalized_message for keyword in ["how", "process", "work", "ingestion", "pipeline", "model"]):
        answer = (
            f"I ingest market prices every {system_status.market_poll_seconds // 60} minutes, news every "
            f"{system_status.news_poll_seconds // 60} minutes, and score the board every "
            f"{system_status.model_poll_seconds // 60} minutes. I start with venue pricing, adjust with the "
            f"ML layer when historical evidence is available, then use the AI/news layer as supporting context. "
            f"My latest market pull was {system_status.latest_market_capture or 'not yet'}, and my latest model run "
            f"was {system_status.latest_model_run or 'not yet'}."
        )
        return PotterChatResponse(answer=answer, suggested_prompts=suggested_prompts)

    if any(keyword in normalized_message for keyword in ["portfolio", "profit", "loss", "bank", "equity", "performance", "pnl"]):
        answer = (
            f"Your paper bank balance is ${portfolio.bank_balance:,.0f}, active capital is ${portfolio.active_capital:,.0f}, "
            f"realized P/L is ${portfolio.realized_pnl:,.0f}, unrealized P/L is ${portfolio.unrealized_pnl:,.0f}, "
            f"and total equity is ${portfolio.total_equity:,.0f}. I currently count {portfolio.completed_trades} "
            f"completed trades and {portfolio.open_positions} open positions."
        )
        return PotterChatResponse(answer=answer, suggested_prompts=suggested_prompts)

    if any(keyword in normalized_message for keyword in ["top", "best", "strongest", "edge", "opportunity"]):
        top_markets = sorted(dashboard.markets, key=lambda market: abs(market.edge), reverse=True)[:3]
        if not top_markets:
            answer = "I do not have any live markets loaded yet, so I cannot rank opportunities right now."
            return PotterChatResponse(answer=answer, suggested_prompts=suggested_prompts)
        lines = [f"My strongest edges right now are {', '.join(market.display_title for market in top_markets)}."]
        lines.extend(_build_market_blurb(market) for market in top_markets[:2])
        return PotterChatResponse(
            answer=" ".join(lines),
            suggested_prompts=suggested_prompts,
            matched_market_ids=[market.id for market in top_markets],
        )

    if matched_markets:
        answer = " ".join(_build_market_blurb(market) for market in matched_markets)
        return PotterChatResponse(
            answer=answer,
            suggested_prompts=suggested_prompts,
            matched_market_ids=[market.id for market in matched_markets],
        )

    if completed_trades:
        latest_trade = completed_trades[-1]
        answer = (
            f"My latest completed trade was {latest_trade.market_question} on {latest_trade.venue}. "
            f"It closed with {latest_trade.profit_loss:+.0f} dollars of P/L. "
            f"If you ask about a specific market, I can explain the probability, edge, and model breakdown."
        )
    else:
        answer = (
            "I am online and watching the board. Ask me how the process works, what my portfolio is doing, "
            "or about a specific market and I will explain the current probability and why I lean the way I do."
        )

    return PotterChatResponse(answer=answer, suggested_prompts=suggested_prompts)


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

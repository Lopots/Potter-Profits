from __future__ import annotations

from datetime import datetime
from datetime import timezone

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.clients.market_data import (
    build_kalshi_backfill_window,
    fetch_kalshi_market_candlesticks,
    fetch_kalshi_markets_by_statuses,
    fetch_live_markets,
    get_market_client_status,
    normalize_kalshi_market,
)
from app.clients.news_data import fetch_newsapi_articles, get_news_client_status, normalize_newsapi_article
from app.core.config import settings
from app.data import load_dashboard
from app.db.base import Base
from app.db.session import get_remote_db
from app.execution import get_execution_status
from app.models import AuditLog, Market, MarketNewsLink, MarketPrice, ModelArtifact, ModelRun, NewsItem, PortfolioPosition, TradeAction, TrainingRun


def _upsert_market(db: Session, market_payload: dict[str, object]) -> None:
    external_id = str(market_payload["external_id"])
    market_row = db.scalar(select(Market).where(Market.external_id == external_id))
    if market_row is None:
        market_row = Market(
            external_id=external_id,
            venue=str(market_payload["venue"]),
            question=str(market_payload["question"]),
            category=str(market_payload["category"]),
            status="active",
        )
        db.add(market_row)

    market_row.venue = str(market_payload["venue"])
    market_row.question = str(market_payload["question"])
    market_row.category = str(market_payload["category"])
    market_row.status = str(market_payload.get("status", "active"))
    market_row.current_probability = float(market_payload.get("market_prob", 0.5))
    market_row.volume_24h = float(market_payload.get("volume_24h", 0.0))
    market_row.liquidity = float(market_payload.get("liquidity", 0.0))
    market_row.metadata_json = dict(market_payload.get("metadata_json", {}))


def _latest_news_score_by_market(db: Session) -> dict[str, float]:
    links = db.scalars(select(MarketNewsLink)).all()
    news_map = {item.external_id: item for item in db.scalars(select(NewsItem)).all()}
    scores: dict[str, float] = {}

    for link in links:
        news_item = news_map.get(link.news_external_id)
        if news_item is None:
            continue

        text = f"{news_item.title} {news_item.summary or ''}".lower()
        if any(token in text for token in ["rises", "strengthen", "accumulation", "bullish", "support"]):
            direction = 1.0
        elif any(token in text for token in ["weigh", "sticky", "cautious", "injury", "concern"]):
            direction = -1.0
        else:
            direction = 0.0

        scores[link.market_external_id] = max(min(link.relevance_score * direction * 0.12, 0.08), -0.08)

    return scores


def _insert_market_price_if_missing(
    db: Session,
    market_external_id: str,
    venue: str,
    probability: float,
    price: float | None,
    volume_24h: float | None,
    liquidity: float | None,
    captured_at: datetime,
) -> bool:
    existing = db.scalar(
        select(MarketPrice).where(
            MarketPrice.market_external_id == market_external_id,
            MarketPrice.captured_at == captured_at,
        )
    )
    if existing is not None:
        return False

    db.add(
        MarketPrice(
            market_external_id=market_external_id,
            venue=venue,
            probability=probability,
            price=price,
            volume_24h=volume_24h,
            liquidity=liquidity,
            captured_at=captured_at,
        )
    )
    return True


def _preferred_kalshi_backfill_markets(db: Session) -> list[Market]:
    candidates = db.scalars(
        select(Market)
        .where(Market.venue == "Kalshi")
        .order_by(Market.volume_24h.desc().nullslast(), Market.updated_at.desc())
    ).all()

    preferred = [
        market
        for market in candidates
        if not str((market.metadata_json or {}).get("ticker", "")).startswith("KXMVE")
    ]
    selected = preferred or candidates
    return selected[: settings.historical_backfill_market_limit]


def _hydrate_additional_backfill_markets(db: Session) -> list[Market]:
    desired = max(settings.historical_backfill_market_limit * 4, 50)
    raw_markets = fetch_kalshi_markets_by_statuses(["open", "settled"], limit_per_status=desired)
    for raw_market in raw_markets:
        _upsert_market(db, normalize_kalshi_market(raw_market))
    db.commit()
    return _preferred_kalshi_backfill_markets(db)


def _load_latest_training_artifact(db: Session) -> ModelArtifact | None:
    return db.scalar(
        select(ModelArtifact)
        .where(ModelArtifact.model_name == "market_direction_lr")
        .order_by(desc(ModelArtifact.created_at))
        .limit(1)
    )


def _sigmoid(value: float) -> float:
    import math
    return 1 / (1 + math.exp(-value))


def _mask_database_url(url: str) -> str:
    if not url:
        return ""
    if "@" not in url or "://" not in url:
        return url
    prefix, suffix = url.split("://", 1)
    auth, host = suffix.split("@", 1)
    if ":" in auth:
        user, _password = auth.split(":", 1)
        return f"{prefix}://{user}:***@{host}"
    return f"{prefix}://***@{host}"


def _build_training_dataset(db: Session) -> tuple[list[list[float]], list[int], list[str]]:
    feature_names = [
        "probability",
        "delta_from_prev",
        "volume_scaled",
        "liquidity_scaled",
        "distance_from_mid",
        "news_score",
    ]

    news_scores = _latest_news_score_by_market(db)
    X: list[list[float]] = []
    y: list[int] = []

    market_ids = db.scalars(select(Market.external_id)).all()
    for market_id in market_ids:
        prices = db.scalars(
            select(MarketPrice)
            .where(MarketPrice.market_external_id == market_id)
            .order_by(MarketPrice.captured_at)
        ).all()
        if len(prices) < 3:
            continue

        market_news_score = news_scores.get(market_id, 0.0)
        for index in range(1, len(prices) - 1):
            prev_row = prices[index - 1]
            current_row = prices[index]
            next_row = prices[index + 1]

            current_prob = float(current_row.probability)
            prev_prob = float(prev_row.probability)
            next_prob = float(next_row.probability)
            delta = current_prob - prev_prob
            label = 1 if next_prob > current_prob else 0

            X.append(
                [
                    current_prob,
                    delta,
                    min(float(current_row.volume_24h or 0.0) / 100000.0, 5.0),
                    min(float(current_row.liquidity or 0.0) / 100000.0, 5.0),
                    abs(current_prob - 0.5),
                    market_news_score,
                ]
            )
            y.append(label)

    return X, y, feature_names


def _copy_market(remote_db: Session, market: Market) -> None:
    remote_row = remote_db.scalar(select(Market).where(Market.external_id == market.external_id))
    if remote_row is None:
        remote_row = Market(external_id=market.external_id, venue=market.venue, question=market.question, category=market.category)
        remote_db.add(remote_row)

    remote_row.venue = market.venue
    remote_row.question = market.question
    remote_row.category = market.category
    remote_row.status = market.status
    remote_row.current_probability = market.current_probability
    remote_row.volume_24h = market.volume_24h
    remote_row.liquidity = market.liquidity
    remote_row.metadata_json = dict(market.metadata_json or {})
    remote_row.created_at = market.created_at
    remote_row.updated_at = market.updated_at


def _copy_market_price(remote_db: Session, row: MarketPrice) -> None:
    remote_row = remote_db.scalar(
        select(MarketPrice).where(
            MarketPrice.market_external_id == row.market_external_id,
            MarketPrice.captured_at == row.captured_at,
        )
    )
    if remote_row is None:
        remote_row = MarketPrice(market_external_id=row.market_external_id, venue=row.venue, probability=row.probability)
        remote_db.add(remote_row)

    remote_row.venue = row.venue
    remote_row.probability = row.probability
    remote_row.price = row.price
    remote_row.volume_24h = row.volume_24h
    remote_row.liquidity = row.liquidity
    remote_row.captured_at = row.captured_at


def _copy_news_item(remote_db: Session, row: NewsItem) -> None:
    remote_row = remote_db.scalar(select(NewsItem).where(NewsItem.external_id == row.external_id))
    if remote_row is None:
        remote_row = NewsItem(source=row.source, external_id=row.external_id, title=row.title, url=row.url)
        remote_db.add(remote_row)

    remote_row.source = row.source
    remote_row.title = row.title
    remote_row.url = row.url
    remote_row.summary = row.summary
    remote_row.published_at = row.published_at
    remote_row.raw_payload = dict(row.raw_payload or {})
    remote_row.created_at = row.created_at


def _copy_market_news_link(remote_db: Session, row: MarketNewsLink) -> None:
    remote_row = remote_db.scalar(
        select(MarketNewsLink).where(
            MarketNewsLink.market_external_id == row.market_external_id,
            MarketNewsLink.news_external_id == row.news_external_id,
        )
    )
    if remote_row is None:
        remote_row = MarketNewsLink(market_external_id=row.market_external_id, news_external_id=row.news_external_id)
        remote_db.add(remote_row)

    remote_row.relevance_score = row.relevance_score
    remote_row.match_reason = row.match_reason
    remote_row.created_at = row.created_at


def _copy_model_run(remote_db: Session, row: ModelRun) -> None:
    remote_row = remote_db.scalar(
        select(ModelRun).where(
            ModelRun.market_external_id == row.market_external_id,
            ModelRun.created_at == row.created_at,
        )
    )
    if remote_row is None:
        remote_row = ModelRun(
            market_external_id=row.market_external_id,
            deterministic_edge=row.deterministic_edge,
            ml_adjustment=row.ml_adjustment,
            ai_adjustment=row.ai_adjustment,
            final_probability=row.final_probability,
            final_score=row.final_score,
            action=row.action,
            confidence=row.confidence,
            pricing_summary=row.pricing_summary,
            ml_summary=row.ml_summary,
            ai_summary=row.ai_summary,
        )
        remote_db.add(remote_row)

    remote_row.deterministic_edge = row.deterministic_edge
    remote_row.ml_adjustment = row.ml_adjustment
    remote_row.ai_adjustment = row.ai_adjustment
    remote_row.final_probability = row.final_probability
    remote_row.final_score = row.final_score
    remote_row.action = row.action
    remote_row.confidence = row.confidence
    remote_row.pricing_summary = row.pricing_summary
    remote_row.ml_summary = row.ml_summary
    remote_row.ai_summary = row.ai_summary
    remote_row.raw_features = dict(row.raw_features or {})
    remote_row.created_at = row.created_at


def _copy_trade_action(remote_db: Session, row: TradeAction) -> None:
    remote_row = remote_db.scalar(
        select(TradeAction).where(
            TradeAction.market_external_id == row.market_external_id,
            TradeAction.created_at == row.created_at,
            TradeAction.side == row.side,
        )
    )
    if remote_row is None:
        remote_row = TradeAction(market_external_id=row.market_external_id, venue=row.venue, side=row.side, rationale=row.rationale)
        remote_db.add(remote_row)

    remote_row.venue = row.venue
    remote_row.side = row.side
    remote_row.stake = row.stake
    remote_row.status = row.status
    remote_row.rationale = row.rationale
    remote_row.is_paper = row.is_paper
    remote_row.created_at = row.created_at


def _copy_portfolio_position(remote_db: Session, row: PortfolioPosition) -> None:
    remote_row = remote_db.scalar(
        select(PortfolioPosition).where(
            PortfolioPosition.market_external_id == row.market_external_id,
            PortfolioPosition.venue == row.venue,
            PortfolioPosition.side == row.side,
        )
    )
    if remote_row is None:
        remote_row = PortfolioPosition(market_external_id=row.market_external_id, venue=row.venue, side=row.side)
        remote_db.add(remote_row)

    remote_row.quantity = row.quantity
    remote_row.average_entry_price = row.average_entry_price
    remote_row.unrealized_pnl = row.unrealized_pnl
    remote_row.updated_at = row.updated_at


def _copy_audit_log(remote_db: Session, row: AuditLog) -> None:
    remote_row = remote_db.scalar(
        select(AuditLog).where(
            AuditLog.event_type == row.event_type,
            AuditLog.message == row.message,
            AuditLog.created_at == row.created_at,
        )
    )
    if remote_row is None:
        remote_row = AuditLog(event_type=row.event_type, message=row.message, payload=dict(row.payload or {}), created_at=row.created_at)
        remote_db.add(remote_row)
        return

    remote_row.payload = dict(row.payload or {})


def _copy_training_run(remote_db: Session, row: TrainingRun) -> None:
    remote_row = remote_db.scalar(
        select(TrainingRun).where(
            TrainingRun.model_name == row.model_name,
            TrainingRun.created_at == row.created_at,
        )
    )
    if remote_row is None:
        remote_row = TrainingRun(model_name=row.model_name, created_at=row.created_at)
        remote_db.add(remote_row)

    remote_row.sample_count = row.sample_count
    remote_row.feature_count = row.feature_count
    remote_row.accuracy = row.accuracy
    remote_row.status = row.status
    remote_row.metrics_json = dict(row.metrics_json or {})


def _copy_model_artifact(remote_db: Session, row: ModelArtifact) -> None:
    remote_row = remote_db.scalar(
        select(ModelArtifact).where(
            ModelArtifact.model_name == row.model_name,
            ModelArtifact.version == row.version,
        )
    )
    if remote_row is None:
        remote_row = ModelArtifact(model_name=row.model_name, version=row.version)
        remote_db.add(remote_row)

    remote_row.feature_names = list(row.feature_names or [])
    remote_row.coefficients = list(row.coefficients or [])
    remote_row.intercept = row.intercept
    remote_row.metrics_json = dict(row.metrics_json or {})
    remote_row.created_at = row.created_at


def sync_local_to_remote(db: Session) -> dict[str, object]:
    if not settings.enable_remote_sync:
        return {
            "job": "remote_sync",
            "status": "disabled",
            "timestamp": datetime.utcnow().isoformat(),
            "records_written": 0,
        }

    with get_remote_db() as remote_db:
        if remote_db is None:
            db.add(
                AuditLog(
                    event_type="remote_sync_skipped",
                    message="Remote sync skipped because no remote database is configured.",
                    payload={},
                )
            )
            db.commit()
            return {
                "job": "remote_sync",
                "status": "not_configured",
                "timestamp": datetime.utcnow().isoformat(),
                "records_written": 0,
            }

        try:
            Base.metadata.create_all(bind=remote_db.get_bind())
            counts: dict[str, int] = {}

            local_markets = db.scalars(select(Market)).all()
            for row in local_markets:
                _copy_market(remote_db, row)
            counts["markets"] = len(local_markets)

            local_prices = db.scalars(select(MarketPrice)).all()
            for row in local_prices:
                _copy_market_price(remote_db, row)
            counts["market_prices"] = len(local_prices)

            local_news = db.scalars(select(NewsItem)).all()
            for row in local_news:
                _copy_news_item(remote_db, row)
            counts["news_items"] = len(local_news)

            local_links = db.scalars(select(MarketNewsLink)).all()
            for row in local_links:
                _copy_market_news_link(remote_db, row)
            counts["market_news_links"] = len(local_links)

            local_model_runs = db.scalars(select(ModelRun)).all()
            for row in local_model_runs:
                _copy_model_run(remote_db, row)
            counts["model_runs"] = len(local_model_runs)

            local_trade_actions = db.scalars(select(TradeAction)).all()
            for row in local_trade_actions:
                _copy_trade_action(remote_db, row)
            counts["trade_actions"] = len(local_trade_actions)

            local_positions = db.scalars(select(PortfolioPosition)).all()
            for row in local_positions:
                _copy_portfolio_position(remote_db, row)
            counts["portfolio_positions"] = len(local_positions)

            local_training_runs = db.scalars(select(TrainingRun)).all()
            for row in local_training_runs:
                _copy_training_run(remote_db, row)
            counts["training_runs"] = len(local_training_runs)

            local_artifacts = db.scalars(select(ModelArtifact)).all()
            for row in local_artifacts:
                _copy_model_artifact(remote_db, row)
            counts["model_artifacts"] = len(local_artifacts)

            local_audits = db.scalars(select(AuditLog)).all()
            for row in local_audits:
                _copy_audit_log(remote_db, row)
            counts["audit_logs"] = len(local_audits)

            remote_db.commit()
            records_written = sum(counts.values())
            db.add(
                AuditLog(
                    event_type="remote_sync",
                    message="Local collector data synced to remote database.",
                    payload={"counts": counts, "remote_database_url": settings.remote_database_url},
                )
            )
            db.commit()
            return {
                "job": "remote_sync",
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
                "records_written": records_written,
            }
        except Exception as exc:
            remote_db.rollback()
            db.add(
                AuditLog(
                    event_type="remote_sync_error",
                    message="Remote sync failed.",
                    payload={"error": str(exc), "remote_database_url": settings.remote_database_url},
                )
            )
            db.commit()
            return {
                "job": "remote_sync",
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat(),
                "records_written": 0,
            }


def ingest_market_data(db: Session) -> dict[str, object]:
    source = settings.default_market_source
    provider_counts: dict[str, int] = {}
    records_written = 0

    try:
        live_markets = fetch_live_markets()
    except Exception as exc:
        db.add(
            AuditLog(
                event_type="market_ingestion_error",
                message=f"Market ingestion failed for source '{source}'.",
                payload={"source": source, "error": str(exc)},
            )
        )
        db.commit()
        raise

    for provider, provider_markets in live_markets.items():
        provider_counts[provider] = len(provider_markets)
        for market_payload in provider_markets:
            _upsert_market(db, market_payload)
            db.add(
                MarketPrice(
                    market_external_id=str(market_payload["external_id"]),
                    venue=str(market_payload["venue"]),
                    probability=float(market_payload.get("market_prob", 0.5)),
                    price=float(market_payload.get("market_prob", 0.5)),
                    volume_24h=float(market_payload.get("volume_24h", 0.0)),
                    liquidity=float(market_payload.get("liquidity", 0.0)),
                )
            )
            records_written += 1

    db.add(
        AuditLog(
            event_type="market_ingestion",
            message=f"Market ingestion stored live market snapshots for source '{source}'.",
            payload={
                "source": source,
                "configured_sources": get_market_client_status(),
                "records_written": records_written,
                "provider_counts": provider_counts,
            },
        )
    )
    db.commit()
    return {
        "job": "market_ingestion",
        "source": source,
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "records_written": records_written,
    }


def ingest_news_data(db: Session) -> dict[str, object]:
    source = settings.default_news_source
    active_markets = db.scalars(select(Market).where(Market.status.in_(["active", "open"])).limit(settings.news_fetch_limit)).all()
    if not active_markets:
        ingest_market_data(db)
        active_markets = db.scalars(select(Market).where(Market.status.in_(["active", "open"])).limit(settings.news_fetch_limit)).all()

    queries = [market.question for market in active_markets]
    try:
        fetched_articles = fetch_newsapi_articles(queries)
    except Exception as exc:
        db.add(
            AuditLog(
                event_type="news_ingestion_error",
                message=f"News ingestion failed for source '{source}'.",
                payload={"source": source, "error": str(exc)},
            )
        )
        db.commit()
        raise

    records_written = 0
    for article in fetched_articles:
        normalized = normalize_newsapi_article(article)
        news_row = db.scalar(select(NewsItem).where(NewsItem.external_id == normalized["external_id"]))
        if news_row is None:
            news_row = NewsItem(
                source=str(normalized["source"]),
                external_id=str(normalized["external_id"]),
                title=str(normalized["title"]),
                url=str(normalized["url"]),
            )
            db.add(news_row)
            records_written += 1

        news_row.summary = str(normalized["summary"])
        news_row.raw_payload = dict(normalized["raw_payload"])
        published_at = normalized.get("published_at")
        if isinstance(published_at, str) and published_at:
            news_row.published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)

        article_text = f"{news_row.title} {news_row.summary or ''}".lower()
        for market in active_markets:
            query_terms = {term.lower() for term in market.question.replace("?", "").split() if len(term) > 3}
            if not query_terms:
                continue
            overlap = sum(1 for term in query_terms if term in article_text)
            if overlap == 0:
                continue

            relevance_score = min(0.95, 0.35 + 0.12 * overlap)
            link_row = db.scalar(
                select(MarketNewsLink).where(
                    MarketNewsLink.market_external_id == market.external_id,
                    MarketNewsLink.news_external_id == news_row.external_id,
                )
            )
            if link_row is None:
                db.add(
                    MarketNewsLink(
                        market_external_id=market.external_id,
                        news_external_id=news_row.external_id,
                        relevance_score=relevance_score,
                        match_reason="keyword overlap from live article query",
                    )
                )

    db.add(
        AuditLog(
            event_type="news_ingestion",
            message=f"News ingestion stored live articles for source '{source}'.",
            payload={
                "source": source,
                "configured_sources": get_news_client_status(),
                "records_written": records_written,
                "queries": queries,
            },
        )
    )
    db.commit()
    return {
        "job": "news_ingestion",
        "source": source,
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "records_written": records_written,
    }


def run_model_pipeline(db: Session) -> dict[str, object]:
    markets = db.scalars(select(Market).where(Market.status == "active")).all()
    news_scores = _latest_news_score_by_market(db)
    training_artifact = _load_latest_training_artifact(db)
    records_written = 0

    for market in markets:
        feature_blob = market.metadata_json or {}
        market_prob = market.current_probability or 0.5
        trend_score = float(feature_blob.get("trend_score", 0.0))
        volume_score = float(feature_blob.get("volume_score", 0.0))
        seeded_sentiment = float(feature_blob.get("sentiment_score", 0.0))
        ai_adjustment = round(news_scores.get(market.external_id, seeded_sentiment * 0.03), 4)

        deterministic_edge = round(((trend_score * 0.09) + (volume_score * 0.06) + (seeded_sentiment * 0.04)), 4)
        ml_adjustment = round(((abs(trend_score) * 0.03) + (abs(volume_score) * 0.02)) * (1 if deterministic_edge >= 0 else -1), 4)

        if training_artifact is not None and training_artifact.coefficients:
            feature_vector = [
                market_prob,
                trend_score,
                min(float(market.volume_24h or 0.0) / 100000.0, 5.0),
                min(float(market.liquidity or 0.0) / 100000.0, 5.0),
                abs(market_prob - 0.5),
                ai_adjustment,
            ]
            linear_score = float(training_artifact.intercept)
            for coefficient, value in zip(training_artifact.coefficients, feature_vector):
                linear_score += float(coefficient) * float(value)
            learned_prob = _sigmoid(linear_score)
            ml_adjustment = round((learned_prob - market_prob) * 0.35, 4)

        final_score = round(deterministic_edge + ml_adjustment + ai_adjustment, 4)
        final_probability = min(max(round(market_prob + final_score, 4), 0.01), 0.99)

        if final_score >= 0.1:
            action = "BUY"
        elif final_score <= -0.1:
            action = "SELL"
        else:
            action = "HOLD"

        confidence = min(
            95,
            max(52, int(55 + abs(final_score) * 160 + abs(trend_score) * 10 + abs(volume_score) * 8)),
        )

        model_run = ModelRun(
            market_external_id=market.external_id,
            deterministic_edge=deterministic_edge,
            ml_adjustment=ml_adjustment,
            ai_adjustment=ai_adjustment,
            final_probability=final_probability,
            final_score=final_score,
            action=action,
            confidence=confidence,
            pricing_summary=f"Stored market pricing for {market.question} implies a base edge of {deterministic_edge:+.1%}.",
            ml_summary=f"Trend and volume regime checks adjusted confidence by {ml_adjustment:+.1%}.",
            ai_summary=f"News-linked context contributed an AI adjustment of {ai_adjustment:+.1%}.",
            raw_features={
                "market_probability": market_prob,
                "trend_score": trend_score,
                "volume_score": volume_score,
                "seeded_sentiment": seeded_sentiment,
            },
        )
        db.add(model_run)

        db.add(
            TradeAction(
                market_external_id=market.external_id,
                venue=market.venue,
                side=action,
                stake=settings.max_paper_trade_size if action != "HOLD" else 0.0,
                status="simulated" if action != "HOLD" else "blocked",
                rationale=f"Model pipeline generated {action} from final score {final_score:+.1%}.",
                is_paper=True,
            )
        )
        records_written += 1

    db.add(
        AuditLog(
            event_type="model_pipeline",
            message="Model pipeline stored model runs and simulated trade actions.",
            payload={
                "layers": ["deterministic_pricing", "ml_confidence", "ai_context"],
                "records_written": records_written,
            },
        )
    )
    db.commit()
    return {
        "job": "model_pipeline",
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "layers": ["deterministic_pricing", "ml_confidence", "ai_context"],
        "records_written": records_written,
    }


def backfill_historical_market_data(db: Session) -> dict[str, object]:
    kalshi_markets = _preferred_kalshi_backfill_markets(db)

    if not kalshi_markets:
        ingest_market_data(db)
        kalshi_markets = _preferred_kalshi_backfill_markets(db)
    if len(kalshi_markets) < max(5, settings.historical_backfill_market_limit // 2):
        try:
            kalshi_markets = _hydrate_additional_backfill_markets(db)
        except Exception:
            kalshi_markets = _preferred_kalshi_backfill_markets(db)

    ticker_map = {
        str((market.metadata_json or {}).get("ticker")): market
        for market in kalshi_markets
        if (market.metadata_json or {}).get("ticker")
    }
    market_tickers = [ticker for ticker in ticker_map.keys() if ticker]
    start_ts, end_ts = build_kalshi_backfill_window()

    interval_candidates: list[int] = []
    for interval in [settings.historical_candle_interval_minutes, 240, 60]:
        if interval not in interval_candidates:
            interval_candidates.append(interval)

    candle_sets: list[dict[str, object]] = []
    last_error: Exception | None = None
    for interval in interval_candidates:
        try:
            candle_sets = fetch_kalshi_market_candlesticks(
                market_tickers=market_tickers,
                start_ts=start_ts,
                end_ts=end_ts,
                period_interval=interval,
            )
        except Exception as exc:
            last_error = exc
            continue
        if candle_sets:
            break

    if not candle_sets and last_error is not None:
        db.add(
            AuditLog(
                event_type="historical_backfill_error",
                message="Historical backfill failed.",
                payload={"error": str(last_error), "market_count": len(market_tickers)},
            )
        )
        db.commit()
        raise last_error

    records_written = 0
    for market_blob in candle_sets:
        ticker = market_blob.get("market_ticker") or market_blob.get("ticker")
        market = ticker_map.get(str(ticker))
        if market is None:
            continue

        for candle in market_blob.get("candlesticks", []):
            end_period_ts = candle.get("end_period_ts")
            if end_period_ts is None:
                continue

            price_blob = candle.get("price", {})
            close_price = float(price_blob.get("close_dollars") or price_blob.get("mean_dollars") or price_blob.get("close") or 0.0)
            if close_price <= 0:
                continue

            volume = float(candle.get("volume_fp") or candle.get("volume") or 0.0)
            open_interest = float(candle.get("open_interest_fp") or 0.0)
            captured_at = datetime.fromtimestamp(int(end_period_ts), tz=timezone.utc).replace(tzinfo=None)

            inserted = _insert_market_price_if_missing(
                db=db,
                market_external_id=market.external_id,
                venue=market.venue,
                probability=min(max(close_price, 0.01), 0.99),
                price=close_price,
                volume_24h=volume,
                liquidity=open_interest,
                captured_at=captured_at,
            )
            if inserted:
                records_written += 1

    db.add(
        AuditLog(
            event_type="historical_backfill",
            message="Historical Kalshi candlesticks backfill completed.",
            payload={
                "records_written": records_written,
                "market_count": len(market_tickers),
                "days": settings.historical_backfill_days,
                "interval_candidates": interval_candidates,
            },
        )
    )
    db.commit()
    return {
        "job": "historical_backfill",
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "records_written": records_written,
    }


def train_probability_model(db: Session) -> dict[str, object]:
    X, y, feature_names = _build_training_dataset(db)
    sample_count = len(X)

    if sample_count < settings.model_min_training_samples:
        training_run = TrainingRun(
            model_name="market_direction_lr",
            sample_count=sample_count,
            feature_count=len(feature_names),
            accuracy=None,
            status="insufficient_data",
            metrics_json={"required_minimum": settings.model_min_training_samples},
        )
        db.add(training_run)
        db.add(
            AuditLog(
                event_type="model_training",
                message="Model training skipped due to insufficient data.",
                payload={"sample_count": sample_count, "required_minimum": settings.model_min_training_samples},
            )
        )
        db.commit()
        return {
            "job": "model_training",
            "status": "insufficient_data",
            "timestamp": datetime.utcnow().isoformat(),
            "records_written": sample_count,
        }

    model = LogisticRegression(max_iter=1000)
    model.fit(X, y)
    predictions = model.predict(X)
    accuracy = float(accuracy_score(y, predictions))

    version = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    training_run = TrainingRun(
        model_name="market_direction_lr",
        sample_count=sample_count,
        feature_count=len(feature_names),
        accuracy=accuracy,
        status="completed",
        metrics_json={"accuracy": accuracy},
    )
    artifact = ModelArtifact(
        model_name="market_direction_lr",
        version=version,
        feature_names=feature_names,
        coefficients=[float(value) for value in model.coef_[0].tolist()],
        intercept=float(model.intercept_[0]),
        metrics_json={"accuracy": accuracy, "sample_count": sample_count},
    )
    db.add(training_run)
    db.add(artifact)
    db.add(
        AuditLog(
            event_type="model_training",
            message="Model training completed and stored a new artifact.",
            payload={"sample_count": sample_count, "accuracy": accuracy, "version": version},
        )
    )
    db.commit()
    return {
        "job": "model_training",
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "records_written": sample_count,
    }


def get_pipeline_status(db: Session) -> dict[str, object]:
    latest_audits = db.scalars(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(10)).all()
    latest_market_ingestion = db.scalar(
        select(AuditLog).where(AuditLog.event_type == "market_ingestion").order_by(desc(AuditLog.created_at)).limit(1)
    )
    latest_news_ingestion = db.scalar(
        select(AuditLog).where(AuditLog.event_type == "news_ingestion").order_by(desc(AuditLog.created_at)).limit(1)
    )
    latest_remote_sync = db.scalar(
        select(AuditLog)
        .where(AuditLog.event_type.in_(["remote_sync", "remote_sync_error", "remote_sync_skipped"]))
        .order_by(desc(AuditLog.created_at))
        .limit(1)
    )
    latest_market_price = db.scalar(select(MarketPrice).order_by(desc(MarketPrice.captured_at)).limit(1))
    latest_news_item = db.scalar(select(NewsItem).order_by(desc(NewsItem.created_at)).limit(1))
    latest_model_run = db.scalar(select(ModelRun).order_by(desc(ModelRun.created_at)).limit(1))
    latest_training_run = db.scalar(select(TrainingRun).order_by(desc(TrainingRun.created_at)).limit(1))
    market_count = len(db.scalars(select(Market.external_id)).all())
    news_count = len(db.scalars(select(NewsItem.external_id)).all())
    model_run_count = len(db.scalars(select(ModelRun.id)).all())
    training_run_count = len(db.scalars(select(TrainingRun.id)).all())

    return {
        "database_url": _mask_database_url(settings.local_database_url),
        "remote_database_url": _mask_database_url(settings.remote_database_url),
        "market_sources": get_market_client_status(),
        "news_sources": get_news_client_status(),
        "execution": get_execution_status(),
        "openai_configured": bool(settings.openai_api_key),
        "scheduler_enabled": settings.enable_scheduler,
        "remote_sync_enabled": settings.enable_remote_sync,
        "historical_backfill_enabled": settings.enable_historical_backfill,
        "model_training_enabled": settings.enable_model_training,
        "market_poll_seconds": settings.market_poll_seconds,
        "news_poll_seconds": settings.news_poll_seconds,
        "model_poll_seconds": settings.model_poll_seconds,
        "sync_interval_seconds": settings.sync_interval_seconds,
        "historical_backfill_interval_seconds": settings.historical_backfill_interval_seconds,
        "model_train_interval_seconds": settings.model_train_interval_seconds,
        "latest_market_capture": latest_market_price.captured_at.isoformat() if latest_market_price else None,
        "latest_news_capture": latest_news_item.created_at.isoformat() if latest_news_item else None,
        "latest_model_run": latest_model_run.created_at.isoformat() if latest_model_run else None,
        "latest_training_run": latest_training_run.created_at.isoformat() if latest_training_run else None,
        "latest_remote_sync": latest_remote_sync.created_at.isoformat() if latest_remote_sync else None,
        "latest_remote_sync_status": latest_remote_sync.event_type if latest_remote_sync else None,
        "latest_market_ingestion": latest_market_ingestion.created_at.isoformat() if latest_market_ingestion else None,
        "latest_news_ingestion": latest_news_ingestion.created_at.isoformat() if latest_news_ingestion else None,
        "latest_market_ingestion_status": latest_market_ingestion.event_type if latest_market_ingestion else None,
        "latest_news_ingestion_status": latest_news_ingestion.event_type if latest_news_ingestion else None,
        "market_count": market_count,
        "news_count": news_count,
        "model_run_count": model_run_count,
        "training_run_count": training_run_count,
        "recent_audit_events": [
            {
                "event_type": audit.event_type,
                "message": audit.message,
                "created_at": audit.created_at.isoformat(),
            }
            for audit in latest_audits
        ],
    }

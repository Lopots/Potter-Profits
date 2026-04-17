from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.db.session import SessionLocal
from app.pipeline import backfill_historical_market_data, ingest_market_data, ingest_news_data, run_model_pipeline, sync_local_to_remote, train_probability_model


def _run_job(job_func) -> None:
    db = SessionLocal()
    try:
        job_func(db)
    finally:
        db.close()


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: _run_job(ingest_market_data), "interval", seconds=settings.market_poll_seconds)
    scheduler.add_job(lambda: _run_job(ingest_news_data), "interval", seconds=settings.news_poll_seconds)
    scheduler.add_job(lambda: _run_job(run_model_pipeline), "interval", seconds=settings.model_poll_seconds)
    if settings.enable_remote_sync:
        scheduler.add_job(lambda: _run_job(sync_local_to_remote), "interval", seconds=settings.sync_interval_seconds)
    if settings.enable_historical_backfill:
        scheduler.add_job(
            lambda: _run_job(backfill_historical_market_data),
            "interval",
            seconds=settings.historical_backfill_interval_seconds,
        )
    if settings.enable_model_training:
        scheduler.add_job(
            lambda: _run_job(train_probability_model),
            "interval",
            seconds=settings.model_train_interval_seconds,
        )
    return scheduler

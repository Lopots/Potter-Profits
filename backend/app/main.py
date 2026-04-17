from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db, init_db
from app.scheduler import create_scheduler
from app.schemas import PotterChatRequest
from app.services import (
    answer_potter_chat,
    get_dashboard_data,
    get_raw_data,
    get_system_status,
    run_historical_backfill_job,
    run_market_ingestion,
    run_model_pipeline_job,
    run_remote_sync_job,
    run_model_training_job,
    run_news_ingestion_job,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    scheduler = None
    if settings.enable_scheduler:
        scheduler = create_scheduler()
        scheduler.start()

    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Prediction market intelligence and paper trading API for Potter.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return get_dashboard_data(db)


@app.get("/api/system/status")
def system_status(db: Session = Depends(get_db)):
    return get_system_status(db)


@app.get("/api/data")
def raw_data(db: Session = Depends(get_db)):
    return get_raw_data(db)


@app.post("/api/chat")
def potter_chat(payload: PotterChatRequest, db: Session = Depends(get_db)):
    return answer_potter_chat(db, payload.message)


@app.post("/api/pipeline/market-ingestion")
def market_ingestion(db: Session = Depends(get_db)):
    return run_market_ingestion(db)


@app.post("/api/pipeline/news-ingestion")
def news_ingestion(db: Session = Depends(get_db)):
    return run_news_ingestion_job(db)


@app.post("/api/pipeline/model-run")
def model_run(db: Session = Depends(get_db)):
    return run_model_pipeline_job(db)


@app.post("/api/pipeline/historical-backfill")
def historical_backfill(db: Session = Depends(get_db)):
    return run_historical_backfill_job(db)


@app.post("/api/pipeline/train-model")
def train_model(db: Session = Depends(get_db)):
    return run_model_training_job(db)


@app.post("/api/pipeline/remote-sync")
def remote_sync(db: Session = Depends(get_db)):
    return run_remote_sync_job(db)

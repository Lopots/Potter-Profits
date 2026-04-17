# Potter Profits

Potter Profits is a prediction market intelligence app with a visible AI agent named Potter. This scaffold now includes:

- A `FastAPI` backend for dashboard data, database persistence, and pipeline endpoints
- A `Next.js` frontend with a black and blue dashboard inspired by exchange-style products
- A transparent Potter activity feed so users can inspect reasoning, actions, and trade history
- A backend scaffold for SQLAlchemy models, Alembic migrations, scheduler hooks, and API-key driven data ingestion

## Project Structure

```text
potter-profits/
|- backend/
|  |- alembic/
|  |- app/
|  |  |- clients/
|  |  |- core/
|  |  |- db/
|  |  |- data.py
|  |  |- main.py
|  |  |- models.py
|  |  |- pipeline.py
|  |  |- scheduler.py
|  |  |- schemas.py
|  |  `- services.py
|  |- .env.example
|  |- alembic.ini
|  `- requirements.txt
|- frontend/
|  |- app/
|  |- components/
|  |- lib/
|  |- package.json
|  `- ...
`- .vscode/
```

## Run The Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

The backend now supports a local-first collector model:

- `LOCAL_DATABASE_URL` is the always-on local collector database
- `DATABASE_URL` / `REMOTE_DATABASE_URL` is the optional Supabase sync target

That means Potter can keep collecting locally even when Supabase is unreachable, then sync later.

## Run The Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the backend at `http://localhost:8000`.

## Run With A Task

If you use VS Code, you can run:

- `Potter: Run App` to start both backend and frontend
- `Potter: Backend Dev Server` to start only the API
- `Potter: Frontend Dev Server` to start only the UI

Open the command palette and run `Tasks: Run Task`, then choose the task you want.

## Deploy On One Ubuntu Server

The repo now includes a plain-Python same-server deployment scaffold in [deploy/ubuntu-deploy.md](/abs/path/c:/Users/NickLoppatto/Potter%20Profits/deploy/ubuntu-deploy.md:1) with:

- `systemd` service for the FastAPI backend
- `systemd` service for the Next.js frontend
- `nginx` reverse proxy config
- frontend production env example

For this setup:

- backend runs on `127.0.0.1:8000`
- frontend runs on `127.0.0.1:3000`
- nginx serves both through one public server IP

Important:

- use your server's public IPv4 address in the browser
- do not use the private address like `10.116.0.2` for public access

## What You Need To Fill In

Once you have the credentials, put them in `backend/.env`:

- `DATABASE_URL`
- `KALSHI_API_KEY`
- `KALSHI_API_SECRET` or `KALSHI_PRIVATE_KEY_PATH` later when you add authenticated Kalshi trading
- `NEWSAPI_API_KEY` or `GNEWS_API_KEY`
- `OPENAI_API_KEY`
- `POLYMARKET_API_KEY` later when you are ready to add Polymarket

You can leave unused providers blank.

## Backend Scaffold Included

The backend now has:

- SQLAlchemy models for `markets`, `market_prices`, `news_items`, `market_news_links`, `model_runs`, `trade_actions`, `portfolio_positions`, and `audit_logs`
- Alembic scaffolding for migrations
- Source configuration checks for market and news providers
- Pipeline endpoints for market ingestion, news ingestion, and model execution
- Optional APScheduler background jobs controlled by `.env`

Useful endpoints:

- `GET /health`
- `GET /api/dashboard`
- `GET /api/system/status`
- `POST /api/pipeline/market-ingestion`
- `POST /api/pipeline/news-ingestion`
- `POST /api/pipeline/model-run`
- `POST /api/pipeline/historical-backfill`
- `POST /api/pipeline/train-model`
- `POST /api/pipeline/remote-sync`

## Migrations

After you switch `DATABASE_URL` to PostgreSQL, generate and run your first migration:

```bash
cd backend
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

## Current Recommended `.env` Direction

For your current setup, these are the important values:

```env
LOCAL_DATABASE_URL=sqlite:///./potter_local.db
DATABASE_URL=postgresql+psycopg://postgres.YOUR_PROJECT_REF:YOUR_PASSWORD@aws-1-us-east-1.pooler.supabase.com:5432/postgres
REMOTE_DATABASE_URL=
ENABLE_REMOTE_SYNC=true
SYNC_INTERVAL_SECONDS=900
DEFAULT_MARKET_SOURCE=kalshi
DEFAULT_NEWS_SOURCE=newsapi
KALSHI_API_KEY=
KALSHI_API_SECRET=
KALSHI_PRIVATE_KEY_PATH=
NEWSAPI_API_KEY=
OPENAI_API_KEY=
LIVE_TRADING_ENABLED=false
KALSHI_PAPER_TRADING=true
```

That keeps Potter collecting into a local DB first, while syncing to Supabase in the background whenever the network allows it. Polymarket stays optional until you finish those credentials.

For now, you do not need a Kalshi private key for public market ingestion, news ingestion, or paper-trading logic. Keep live trading disabled until that path is implemented and tested.

## Automatic Polling

The backend can poll automatically while the API process is running. Use these settings in `backend/.env`:

```env
ENABLE_SCHEDULER=true
MARKET_POLL_SECONDS=300
NEWS_POLL_SECONDS=1800
MODEL_POLL_SECONDS=600
ENABLE_REMOTE_SYNC=true
SYNC_INTERVAL_SECONDS=900
ENABLE_HISTORICAL_BACKFILL=true
HISTORICAL_BACKFILL_DAYS=30
HISTORICAL_BACKFILL_MARKET_LIMIT=25
HISTORICAL_BACKFILL_INTERVAL_SECONDS=86400
HISTORICAL_CANDLE_INTERVAL_MINUTES=1440
ENABLE_MODEL_TRAINING=true
MODEL_TRAIN_INTERVAL_SECONDS=21600
MODEL_MIN_TRAINING_SAMPLES=50
```

That gives you:

- live market snapshots every 5 minutes
- news refresh every 30 minutes
- model reruns every 10 minutes
- Supabase sync attempts every 15 minutes
- Kalshi historical backfill once per day
- ML retraining every 6 hours once enough samples exist

For a cheaper default, the backend also reduces each news cycle to fewer market queries so you stay much lower on NewsAPI usage while you’re still iterating.

## Suggested Next Integrations

1. Replace the scaffolded ingestion jobs with real Polymarket and Kalshi fetchers.
2. Add a real headline/news collector tied to active markets.
3. Store model runs from deterministic pricing, ML confidence, and AI context scoring.
4. Add paper portfolio updates and eventually guarded broker execution.

## Safety Note

Automatic live betting and trading should stay disabled until you add:

- Position sizing limits
- Venue-specific compliance checks
- Kill switches
- Human approval rules
- Full audit logging

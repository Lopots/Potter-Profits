import { SystemStatus } from "./types";

export const mockSystemStatus: SystemStatus = {
  database_url: "sqlite:///./potter.db",
  market_sources: {
    kalshi: {
      configured: true,
      base_url: "https://api.elections.kalshi.com",
      notes: "Public market data endpoints are available without authentication. Trading still requires auth.",
    },
    polymarket: {
      configured: true,
      base_url: "https://clob.polymarket.com",
      notes: "Public market discovery is available from the Gamma API without authentication.",
    },
  },
  news_sources: {
    newsapi: {
      configured: true,
      base_url: "https://newsapi.org/v2",
      notes: "Recommended first news source for headline ingestion.",
    },
  },
  execution: {
    paper_trading_enabled: true,
    live_trading_enabled: false,
    execution_venue: "kalshi",
    max_paper_trade_size: 250,
    max_live_trade_size: 25,
    daily_loss_limit: 100,
    live_trading_lock_reason: "Live trading is locked. Enable it only after paper results, audit logs, and venue execution checks are verified.",
  },
  openai_configured: true,
  scheduler_enabled: true,
  historical_backfill_enabled: true,
  model_training_enabled: true,
  market_poll_seconds: 300,
  news_poll_seconds: 1800,
  model_poll_seconds: 600,
  historical_backfill_interval_seconds: 86400,
  model_train_interval_seconds: 21600,
  latest_market_capture: "2026-04-16T23:18:59.260744",
  latest_news_capture: "2026-04-16T23:19:01.235327",
  latest_model_run: "2026-04-16T23:19:01.752252",
  latest_training_run: "2026-04-16T23:49:18.531682",
  market_count: 200,
  news_count: 6,
  model_run_count: 200,
  training_run_count: 1,
  recent_audit_events: [
    {
      event_type: "model_training",
      message: "Model training skipped due to insufficient data.",
      created_at: "2026-04-16T23:49:18.531682",
    },
    {
      event_type: "model_pipeline",
      message: "Model pipeline stored model runs and simulated trade actions.",
      created_at: "2026-04-16T23:19:01.752252",
    },
  ],
};

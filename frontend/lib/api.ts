import { DashboardPageData, DashboardResponse, DataPageData, RawDataResponse, SystemStatus } from "./types";

const API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

const emptyRawData: RawDataResponse = {
  markets: [],
  market_prices: [],
  news_items: [],
  model_runs: [],
  trade_actions: [],
  audit_logs: [],
};

const emptyDashboardData: DashboardResponse = {
  snapshot: {
    total_markets: 0,
    buy_signals: 0,
    sell_signals: 0,
    average_edge: 0,
    strongest_edge: 0,
  },
  model_layers: [],
  markets: [],
  potter: {
    mode: "paper",
    autonomy_level: "paper-auto",
    mission: "Monitor active markets and wait for live data.",
    reasoning_summary: "No live dashboard payload is available right now, so Potter is showing a blank state instead of sample data.",
    next_action: "Restore the live dashboard feed and rerun ingestion.",
    guardrails: [],
    thoughts: [],
  },
  trades: [],
  portfolio: {
    starting_bankroll: 10000,
    bank_balance: 10000,
    active_capital: 0,
    realized_pnl: 0,
    unrealized_pnl: 0,
    total_equity: 10000,
    completed_trades: 0,
    open_positions: 0,
    performance_points: [],
  },
};

const emptySystemStatus: SystemStatus = {
  database_url: "",
  remote_database_url: "",
  market_sources: {},
  news_sources: {},
  execution: {
    paper_trading_enabled: true,
    live_trading_enabled: false,
    execution_venue: "kalshi",
    max_paper_trade_size: 0,
    max_live_trade_size: 0,
    daily_loss_limit: 0,
    live_trading_lock_reason: "Live system status is unavailable.",
  },
  openai_configured: false,
  scheduler_enabled: false,
  remote_sync_enabled: false,
  historical_backfill_enabled: false,
  model_training_enabled: false,
  market_poll_seconds: 0,
  news_poll_seconds: 0,
  model_poll_seconds: 0,
  sync_interval_seconds: 0,
  historical_backfill_interval_seconds: 0,
  model_train_interval_seconds: 0,
  latest_market_capture: null,
  latest_news_capture: null,
  latest_model_run: null,
  latest_training_run: null,
  latest_remote_sync: null,
  latest_remote_sync_status: null,
  latest_market_ingestion: null,
  latest_news_ingestion: null,
  latest_market_ingestion_status: null,
  latest_news_ingestion_status: null,
  market_count: 0,
  news_count: 0,
  model_run_count: 0,
  training_run_count: 0,
  recent_audit_events: [],
};

export async function getDashboardData(): Promise<DashboardResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/dashboard`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error("Failed to load Potter dashboard");
    }

    return response.json() as Promise<DashboardResponse>;
  } catch {
    return emptyDashboardData;
  }
}

export async function getSystemStatus(): Promise<SystemStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/system/status`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error("Failed to load system status");
    }

    return response.json() as Promise<SystemStatus>;
  } catch {
    return emptySystemStatus;
  }
}

export async function getRawData(): Promise<RawDataResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/data`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error("Failed to load raw Potter data");
    }

    return response.json() as Promise<RawDataResponse>;
  } catch {
    return emptyRawData;
  }
}

export async function getDashboardPageData(): Promise<DashboardPageData> {
  const [dashboard, systemStatus] = await Promise.all([getDashboardData(), getSystemStatus()]);
  return { dashboard, systemStatus };
}

export async function getDataPageData(): Promise<DataPageData> {
  const [rawData, systemStatus] = await Promise.all([getRawData(), getSystemStatus()]);
  return { rawData, systemStatus };
}

export type ActionType = "BUY" | "SELL" | "HOLD";
export type TradeStatus = "queued" | "simulated" | "blocked";

export interface Market {
  id: string;
  venue: string;
  question: string;
  category: string;
  market_prob: number;
  potter_prob: number;
  sentiment_score: number;
  trend_score: number;
  volume_score: number;
  confidence: number;
  edge: number;
  action: ActionType;
  volume_24h: number;
  liquidity: number;
  deterministic_edge: number;
  ml_confidence_adjustment: number;
  ai_news_adjustment: number;
  final_score: number;
  pricing_summary: string;
  ml_summary: string;
  ai_summary: string;
}

export interface MarketSnapshot {
  total_markets: number;
  buy_signals: number;
  sell_signals: number;
  average_edge: number;
  strongest_edge: number;
}

export interface PotterThought {
  timestamp: string;
  title: string;
  detail: string;
  tone: "info" | "success" | "warning";
}

export interface RiskGuardrail {
  name: string;
  status: "active" | "watch" | "disabled";
  detail: string;
}

export interface PotterState {
  mode: "paper" | "live-disabled";
  autonomy_level: "assistive" | "paper-auto" | "live-auto-locked";
  mission: string;
  reasoning_summary: string;
  next_action: string;
  guardrails: RiskGuardrail[];
  thoughts: PotterThought[];
}

export interface ModelLayer {
  name: string;
  role: string;
  weight: string;
  purpose: string;
  examples: string[];
}

export interface Trade {
  id: string;
  timestamp: string;
  market_id: string;
  market_question: string;
  venue: string;
  side: ActionType;
  stake: number;
  edge_at_entry: number;
  confidence: number;
  status: TradeStatus;
  rationale: string;
}

export interface DashboardResponse {
  snapshot: MarketSnapshot;
  model_layers: ModelLayer[];
  markets: Market[];
  potter: PotterState;
  trades: Trade[];
}

export interface SourceStatus {
  configured: boolean;
  base_url: string;
  notes: string;
}

export interface ExecutionStatus {
  paper_trading_enabled: boolean;
  live_trading_enabled: boolean;
  execution_venue: string;
  max_paper_trade_size: number;
  max_live_trade_size: number;
  daily_loss_limit: number;
  live_trading_lock_reason: string | null;
}

export interface AuditEvent {
  event_type: string;
  message: string;
  created_at: string;
}

export interface SystemStatus {
  database_url: string;
  market_sources: Record<string, SourceStatus>;
  news_sources: Record<string, SourceStatus>;
  execution: ExecutionStatus;
  openai_configured: boolean;
  scheduler_enabled: boolean;
  historical_backfill_enabled: boolean;
  model_training_enabled: boolean;
  market_poll_seconds: number;
  news_poll_seconds: number;
  model_poll_seconds: number;
  historical_backfill_interval_seconds: number;
  model_train_interval_seconds: number;
  latest_market_capture: string | null;
  latest_news_capture: string | null;
  latest_model_run: string | null;
  latest_training_run: string | null;
  market_count: number;
  news_count: number;
  model_run_count: number;
  training_run_count: number;
  recent_audit_events: AuditEvent[];
}

export interface DashboardPageData {
  dashboard: DashboardResponse;
  systemStatus: SystemStatus;
}

import { SystemStatus } from "@/lib/types";
import { formatEasternTimestamp } from "@/lib/time";

function formatInterval(seconds: number) {
  if (seconds >= 3600) {
    return `${Math.round(seconds / 3600)}h`;
  }
  if (seconds >= 60) {
    return `${Math.round(seconds / 60)}m`;
  }
  return `${seconds}s`;
}

function boolLabel(value: boolean) {
  return value ? "Enabled" : "Disabled";
}

export function SystemPanel({ systemStatus }: { systemStatus: SystemStatus }) {
  return (
    <div id="system" className="panel system-panel">
      <div className="section-header">
        <div>
          <span className="eyebrow">Data Operations</span>
          <h2>What is being ingested, when it last ran, and why the board looks this way</h2>
        </div>
        <p>
          This panel keeps the ingestion state readable: scheduler cadence, market/news pull times, sync timing,
          stored history depth, and whether Potter is operating from fresh rows or older local history.
        </p>
      </div>

      <div className="system-grid system-grid-wide">
        <article className="system-card">
          <span className="eyebrow">Scheduler</span>
          <strong>{systemStatus.scheduler_enabled ? "Running" : "Stopped"}</strong>
          <p>Automatic market, news, model, training, and sync jobs only fire while the backend service stays alive.</p>
        </article>
        <article className="system-card">
          <span className="eyebrow">Ingestion</span>
          <strong>Markets {formatInterval(systemStatus.market_poll_seconds)} | News {formatInterval(systemStatus.news_poll_seconds)}</strong>
          <p>Market pulls and headline pulls run on separate cadences so Potter can stay current without overspending on news APIs.</p>
        </article>
        <article className="system-card">
          <span className="eyebrow">Models</span>
          <strong>Scoring {formatInterval(systemStatus.model_poll_seconds)} | Train {formatInterval(systemStatus.model_train_interval_seconds)}</strong>
          <p>The scoring layer refreshes often, while the ML training layer waits for enough historical rows before retraining.</p>
        </article>
        <article className="system-card">
          <span className="eyebrow">Storage</span>
          <strong>Local first | Sync {formatInterval(systemStatus.sync_interval_seconds)}</strong>
          <p>Potter writes locally first, then attempts to sync into Supabase on the remote sync cadence.</p>
        </article>
      </div>

      <div className="explanation-grid explanation-grid-wide">
        <article className="explanation-card">
          <span className="eyebrow">Freshness</span>
          <p>Latest market capture: {formatEasternTimestamp(systemStatus.latest_market_capture)}</p>
          <p>Latest market ingestion: {formatEasternTimestamp(systemStatus.latest_market_ingestion)}</p>
          <p>Latest news capture: {formatEasternTimestamp(systemStatus.latest_news_capture)}</p>
          <p>Latest news ingestion: {formatEasternTimestamp(systemStatus.latest_news_ingestion)}</p>
        </article>

        <article className="explanation-card">
          <span className="eyebrow">Model Timing</span>
          <p>Latest model run: {formatEasternTimestamp(systemStatus.latest_model_run)}</p>
          <p>Latest training run: {formatEasternTimestamp(systemStatus.latest_training_run)}</p>
          <p>Training enabled: {boolLabel(systemStatus.model_training_enabled)}</p>
          <p>Historical backfill: {boolLabel(systemStatus.historical_backfill_enabled)}</p>
        </article>

        <article className="explanation-card">
          <span className="eyebrow">Stored Counts</span>
          <p>Markets: {systemStatus.market_count}</p>
          <p>News: {systemStatus.news_count}</p>
          <p>Model runs: {systemStatus.model_run_count}</p>
          <p>Training runs: {systemStatus.training_run_count}</p>
        </article>

        <article className="explanation-card">
          <span className="eyebrow">Execution Controls</span>
          <p>Paper trading: {boolLabel(systemStatus.execution.paper_trading_enabled)}</p>
          <p>Live trading: {systemStatus.execution.live_trading_enabled ? "Unlocked" : "Locked"}</p>
          <p>Paper max size: ${systemStatus.execution.max_paper_trade_size}</p>
          <p>Daily loss limit: ${systemStatus.execution.daily_loss_limit}</p>
        </article>

        <article className="explanation-card">
          <span className="eyebrow">Source Coverage</span>
          <p>Kalshi: {boolLabel(systemStatus.market_sources.kalshi?.configured ?? false)}</p>
          <p>NewsAPI: {boolLabel(systemStatus.news_sources.newsapi?.configured ?? false)}</p>
          <p>OpenAI: {boolLabel(systemStatus.openai_configured)}</p>
        </article>

        <article className="explanation-card">
          <span className="eyebrow">Sync Status</span>
          <p>Remote sync enabled: {boolLabel(systemStatus.remote_sync_enabled)}</p>
          <p>Latest remote sync: {formatEasternTimestamp(systemStatus.latest_remote_sync)}</p>
          <p>Latest sync status: {systemStatus.latest_remote_sync_status ?? "Not yet"}</p>
          <p>Remote DB target configured: {systemStatus.remote_database_url ? "Yes" : "No"}</p>
        </article>
      </div>

      <div className="audit-section">
        <span className="eyebrow">Recent Pipeline Events</span>
        <div className="audit-list">
          {systemStatus.recent_audit_events.slice(0, 9).map((event) => (
            <article key={`${event.event_type}-${event.created_at}`} className="audit-card">
              <strong>{event.event_type}</strong>
              <span>{formatEasternTimestamp(event.created_at)}</span>
              <p>{event.message}</p>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}

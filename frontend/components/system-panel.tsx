import { SystemStatus } from "@/lib/types";

function formatInterval(seconds: number) {
  if (seconds >= 3600) {
    return `${Math.round(seconds / 3600)}h`;
  }
  if (seconds >= 60) {
    return `${Math.round(seconds / 60)}m`;
  }
  return `${seconds}s`;
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return "Not yet";
  }
  return new Date(value).toLocaleString();
}

export function SystemPanel({ systemStatus }: { systemStatus: SystemStatus }) {
  return (
    <div className="panel system-panel">
      <div className="section-header">
        <div>
          <span className="eyebrow">System Status</span>
          <h2>Why the dashboard looks the way it does</h2>
        </div>
        <p>
          This panel explains what Potter is refreshing, how often it retrains, and whether the current
          numbers are being driven by live data, stored history, or fallback logic.
        </p>
      </div>

      <div className="system-grid">
        <article className="system-card">
          <span className="eyebrow">Scheduler</span>
          <strong>{systemStatus.scheduler_enabled ? "Active" : "Inactive"}</strong>
          <p>
            Potter only pulls automatically while the backend process is running and the scheduler is enabled.
          </p>
        </article>
        <article className="system-card">
          <span className="eyebrow">Polling Cadence</span>
          <strong>
            Markets {formatInterval(systemStatus.market_poll_seconds)} • News {formatInterval(systemStatus.news_poll_seconds)}
          </strong>
          <p>Model runs every {formatInterval(systemStatus.model_poll_seconds)} based on the latest stored market and news rows.</p>
        </article>
        <article className="system-card">
          <span className="eyebrow">Training</span>
          <strong>
            {systemStatus.model_training_enabled ? `Every ${formatInterval(systemStatus.model_train_interval_seconds)}` : "Disabled"}
          </strong>
          <p>
            The ML layer retrains from stored history. If there is not enough data yet, Potter falls back to the lighter rule-based ML adjustment.
          </p>
        </article>
        <article className="system-card">
          <span className="eyebrow">Backfill</span>
          <strong>
            {systemStatus.historical_backfill_enabled
              ? `Every ${formatInterval(systemStatus.historical_backfill_interval_seconds)}`
              : "Disabled"}
          </strong>
          <p>Historical Kalshi candles are used to build time-series context so the model can learn from more than one fresh snapshot.</p>
        </article>
      </div>

      <div className="explanation-grid">
        <article className="explanation-card">
          <span className="eyebrow">Data Freshness</span>
          <p>Latest market capture: {formatTimestamp(systemStatus.latest_market_capture)}</p>
          <p>Latest news capture: {formatTimestamp(systemStatus.latest_news_capture)}</p>
          <p>Latest model run: {formatTimestamp(systemStatus.latest_model_run)}</p>
          <p>Latest training run: {formatTimestamp(systemStatus.latest_training_run)}</p>
        </article>

        <article className="explanation-card">
          <span className="eyebrow">Stored History</span>
          <p>{systemStatus.market_count} markets stored</p>
          <p>{systemStatus.news_count} news items stored</p>
          <p>{systemStatus.model_run_count} model runs stored</p>
          <p>{systemStatus.training_run_count} training runs stored</p>
        </article>

        <article className="explanation-card">
          <span className="eyebrow">Execution Logic</span>
          <p>Paper trading: {systemStatus.execution.paper_trading_enabled ? "Enabled" : "Disabled"}</p>
          <p>Live trading: {systemStatus.execution.live_trading_enabled ? "Enabled" : "Locked"}</p>
          <p>Venue: {systemStatus.execution.execution_venue}</p>
          <p>Paper max size: ${systemStatus.execution.max_paper_trade_size}</p>
        </article>
      </div>

      <div className="audit-section">
        <span className="eyebrow">Recent Pipeline Events</span>
        <div className="audit-list">
          {systemStatus.recent_audit_events.slice(0, 6).map((event) => (
            <article key={`${event.event_type}-${event.created_at}`} className="audit-card">
              <strong>{event.event_type}</strong>
              <span>{formatTimestamp(event.created_at)}</span>
              <p>{event.message}</p>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}

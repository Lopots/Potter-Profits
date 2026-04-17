import { DashboardPageData } from "@/lib/types";
import { formatEasternTimestamp, normalizeApiTimestamp } from "@/lib/time";
import { AppHeader } from "./app-header";

function formatPercent(value: number | null | undefined) {
  if (value == null) {
    return "n/a";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function formatSignedPercent(value: number) {
  return `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}%`;
}

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function IngestionShell({ data }: { data: DashboardPageData }) {
  const { dashboard, systemStatus } = data;
  const { markets, potter } = dashboard;

  const freshestMarkets = [...markets]
    .sort((a, b) => {
      const aTime = normalizeApiTimestamp(a.latest_pull_at) ? new Date(normalizeApiTimestamp(a.latest_pull_at)!).getTime() : 0;
      const bTime = normalizeApiTimestamp(b.latest_pull_at) ? new Date(normalizeApiTimestamp(b.latest_pull_at)!).getTime() : 0;
      return bTime - aTime;
    })
    .slice(0, 25);

  return (
    <main className="page-shell">
      <AppHeader
        activePage="ingestion"
        latestMarketCapture={systemStatus.latest_market_capture}
        latestModelRun={systemStatus.latest_model_run}
        modeLabel={potter.mode === "paper" ? "Paper trading active" : "Live locked"}
      />

      <section className="stats-grid">
        <div className="panel stat-card">
          <span className="eyebrow">Latest Market Ingestion</span>
          <strong>{formatEasternTimestamp(systemStatus.latest_market_ingestion)}</strong>
          <p>Last successful market ingestion event stored in the audit trail.</p>
        </div>
        <div className="panel stat-card">
          <span className="eyebrow">Latest News Ingestion</span>
          <strong>{formatEasternTimestamp(systemStatus.latest_news_ingestion)}</strong>
          <p>Last successful news ingestion event stored in the audit trail.</p>
        </div>
        <div className="panel stat-card">
          <span className="eyebrow">Local Market Rows</span>
          <strong>{systemStatus.market_count}</strong>
          <p>Total stored market rows currently available in the local collector database.</p>
        </div>
        <div className="panel stat-card">
          <span className="eyebrow">Local Model Runs</span>
          <strong>{systemStatus.model_run_count}</strong>
          <p>Total stored model outputs currently available for Potter to reference.</p>
        </div>
      </section>

      <section className="panel stack-section">
        <div className="section-header">
          <div>
            <span className="eyebrow">Ingestion Board</span>
            <h2>Recent markets with previous pull vs current pull</h2>
          </div>
          <p>
            This view is for raw monitoring. It shows when each market was last pulled, what the previous price was,
            what it is now, and how Potter’s model reacted.
          </p>
        </div>
        <div className="table-wrap">
          <table className="dense-table">
            <thead>
              <tr>
                <th>Market</th>
                <th>Venue</th>
                <th>Latest Pull</th>
                <th>Previous Pull</th>
                <th>Previous Price</th>
                <th>Current Price</th>
                <th>Change</th>
                <th>Potter Prob</th>
                <th>Edge</th>
                <th>Liquidity</th>
              </tr>
            </thead>
            <tbody>
              {freshestMarkets.map((market) => (
                <tr key={`ingestion-${market.id}`}>
                  <td>
                    <div className="market-cell">
                      <strong>{market.display_title}</strong>
                      {market.subtitle ? <span>{market.subtitle}</span> : null}
                    </div>
                  </td>
                  <td>{market.venue}</td>
                  <td>{formatEasternTimestamp(market.latest_pull_at)}</td>
                  <td>{formatEasternTimestamp(market.previous_pull_at)}</td>
                  <td>{formatPercent(market.previous_market_prob)}</td>
                  <td>{formatPercent(market.market_prob)}</td>
                  <td className={market.price_change >= 0 ? "positive" : "negative"}>{formatSignedPercent(market.price_change)}</td>
                  <td>{formatPercent(market.potter_prob)}</td>
                  <td className={market.edge >= 0 ? "positive" : "negative"}>{formatSignedPercent(market.edge)}</td>
                  <td>{formatMoney(market.liquidity)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="content-grid">
        <div className="panel">
          <div className="section-header">
            <div>
              <span className="eyebrow">Pipeline Events</span>
              <h2>Recent audit log</h2>
            </div>
            <p>Use this to see exactly which job ran and when it updated local state.</p>
          </div>
          <div className="audit-list audit-list-single">
            {systemStatus.recent_audit_events.map((event) => (
              <article key={`${event.event_type}-${event.created_at}`} className="audit-card">
                <strong>{event.event_type}</strong>
                <span>{formatEasternTimestamp(event.created_at)}</span>
                <p>{event.message}</p>
              </article>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="section-header">
            <div>
              <span className="eyebrow">Model Context</span>
              <h2>Why rows move after ingestion</h2>
            </div>
            <p>The ingestion jobs update raw prices first, then Potter recalculates model outputs from the stored history.</p>
          </div>
          <div className="explanation-grid explanation-grid-single">
            <article className="explanation-card">
              <span className="eyebrow">Cadence</span>
              <p>Markets every {Math.round(systemStatus.market_poll_seconds / 60)}m</p>
              <p>News every {Math.round(systemStatus.news_poll_seconds / 60)}m</p>
              <p>Model every {Math.round(systemStatus.model_poll_seconds / 60)}m</p>
            </article>
            <article className="explanation-card">
              <span className="eyebrow">Training</span>
              <p>Training enabled: {systemStatus.model_training_enabled ? "Yes" : "No"}</p>
              <p>Training interval: {Math.round(systemStatus.model_train_interval_seconds / 3600)}h</p>
              <p>Stored training runs: {systemStatus.training_run_count}</p>
            </article>
            <article className="explanation-card">
              <span className="eyebrow">Sync</span>
              <p>Remote sync enabled: {systemStatus.remote_sync_enabled ? "Yes" : "No"}</p>
              <p>Latest sync: {formatEasternTimestamp(systemStatus.latest_remote_sync)}</p>
              <p>Latest sync status: {systemStatus.latest_remote_sync_status ?? "Not yet"}</p>
            </article>
          </div>
        </div>
      </section>
    </main>
  );
}

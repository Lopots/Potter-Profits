import { DataPageData } from "@/lib/types";
import { formatEasternTimestamp } from "@/lib/time";
import { AppHeader } from "./app-header";

function formatPercent(value: number | null | undefined) {
  if (value == null) {
    return "n/a";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function formatSignedPercent(value: number | null | undefined) {
  if (value == null) {
    return "n/a";
  }
  return `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}%`;
}

function formatNumber(value: number | null | undefined) {
  if (value == null) {
    return "n/a";
  }
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

function formatMoney(value: number | null | undefined) {
  if (value == null) {
    return "n/a";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function DataShell({ data }: { data: DataPageData }) {
  const { rawData, systemStatus } = data;
  const rawDataAvailable =
    rawData.markets.length > 0 ||
    rawData.market_prices.length > 0 ||
    rawData.news_items.length > 0 ||
    rawData.model_runs.length > 0 ||
    rawData.trade_actions.length > 0 ||
    rawData.audit_logs.length > 0;

  return (
    <main className="page-shell">
      <AppHeader
        activePage="data"
        latestMarketCapture={systemStatus.latest_market_capture}
        latestModelRun={systemStatus.latest_model_run}
        modeLabel={systemStatus.execution.paper_trading_enabled ? "Paper trading active" : "Live locked"}
      />

      <section className="panel section-intro">
        <span className="eyebrow">Raw Data</span>
        <h2>Stored rows queried directly from Potter&apos;s local database</h2>
        <p>
          This page shows the actual rows coming back from the database so you can verify ingestion, model output,
          and audit activity without leaving the UI.
        </p>
        <div className="mini-summary">
          <span className="mini-pill">{rawData.markets.length} market rows shown</span>
          <span className="mini-pill">{rawData.market_prices.length} price rows shown</span>
          <span className="mini-pill">{rawData.model_runs.length} model rows shown</span>
          <span className="mini-pill">{rawData.audit_logs.length} audit rows shown</span>
        </div>
        {!rawDataAvailable ? (
          <div className="mini-summary">
            <span className="mini-pill">Raw data endpoint unavailable on current backend</span>
            <span className="mini-pill">Deploy latest backend to enable /api/data</span>
          </div>
        ) : null}
      </section>

      <section className="stats-grid">
        <div className="panel stat-card">
          <span className="eyebrow">Latest Stored Price Row</span>
          <strong>{rawData.market_prices[0] ? formatEasternTimestamp(rawData.market_prices[0].captured_at) : "Not yet"}</strong>
          <p>Most recent stored market price snapshot returned by the raw data query.</p>
        </div>
        <div className="panel stat-card">
          <span className="eyebrow">Latest Stored News Row</span>
          <strong>{rawData.news_items[0] ? formatEasternTimestamp(rawData.news_items[0].created_at) : "Not yet"}</strong>
          <p>Most recent stored news row returned by the raw data query.</p>
        </div>
        <div className="panel stat-card">
          <span className="eyebrow">Latest Stored Model Row</span>
          <strong>{rawData.model_runs[0] ? formatEasternTimestamp(rawData.model_runs[0].created_at) : "Not yet"}</strong>
          <p>Most recent model output currently stored in the database.</p>
        </div>
        <div className="panel stat-card">
          <span className="eyebrow">Latest Audit Row</span>
          <strong>{rawData.audit_logs[0] ? formatEasternTimestamp(rawData.audit_logs[0].created_at) : "Not yet"}</strong>
          <p>Most recent audit event written by the pipeline.</p>
        </div>
      </section>

      <section className="panel stack-section">
        <div className="section-header">
          <div>
            <span className="eyebrow">Markets Table</span>
            <h2>Raw markets</h2>
          </div>
          <p>Latest stored market records with venue, status, probability, and timestamps.</p>
        </div>
        <div className="table-wrap">
          <table className="dense-table">
            <thead>
              <tr>
                <th>Market</th>
                <th>Venue</th>
                <th>Status</th>
                <th>Prob</th>
                <th>Volume</th>
                <th>Liquidity</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {rawData.markets.map((row) => (
                <tr key={`raw-market-${row.external_id}`}>
                  <td>
                    <div className="market-cell">
                      <strong>{row.question}</strong>
                      <span>{row.category}</span>
                      <span>{row.external_id}</span>
                    </div>
                  </td>
                  <td>{row.venue}</td>
                  <td>{row.status}</td>
                  <td>{formatPercent(row.current_probability)}</td>
                  <td>{formatNumber(row.volume_24h)}</td>
                  <td>{formatMoney(row.liquidity)}</td>
                  <td>{formatEasternTimestamp(row.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel stack-section">
        <div className="section-header">
          <div>
            <span className="eyebrow">Market Prices Table</span>
            <h2>Raw price snapshots</h2>
          </div>
          <p>Recent stored price pulls, with captured time and current stored probability.</p>
        </div>
        <div className="table-wrap">
          <table className="dense-table">
            <thead>
              <tr>
                <th>Market ID</th>
                <th>Venue</th>
                <th>Captured</th>
                <th>Prob</th>
                <th>Price</th>
                <th>Volume</th>
                <th>Liquidity</th>
              </tr>
            </thead>
            <tbody>
              {rawData.market_prices.map((row, index) => {
                const previous = rawData.market_prices[index + 1];
                const change =
                  previous && previous.market_external_id === row.market_external_id
                    ? row.probability - previous.probability
                    : null;

                return (
                  <tr key={`raw-price-${row.market_external_id}-${row.captured_at}`}>
                    <td>{row.market_external_id}</td>
                    <td>{row.venue}</td>
                    <td>{formatEasternTimestamp(row.captured_at)}</td>
                    <td>{formatPercent(row.probability)}</td>
                    <td>{formatPercent(row.price)}</td>
                    <td>{formatNumber(row.volume_24h)}</td>
                    <td>
                      {formatMoney(row.liquidity)}
                      {change != null ? (
                        <div className={change >= 0 ? "positive" : "negative"}>{formatSignedPercent(change)}</div>
                      ) : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="content-grid">
        <div className="panel">
          <div className="section-header">
            <div>
              <span className="eyebrow">News Rows</span>
              <h2>Raw news items</h2>
            </div>
            <p>Recent stored articles, their source, and when Potter saved them.</p>
          </div>
          <div className="table-wrap">
            <table className="dense-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Title</th>
                  <th>Published</th>
                  <th>Stored</th>
                </tr>
              </thead>
              <tbody>
                {rawData.news_items.map((row) => (
                  <tr key={`raw-news-${row.external_id}`}>
                    <td>{row.source}</td>
                    <td>
                      <div className="market-cell">
                        <strong>{row.title}</strong>
                        {row.summary ? <span>{row.summary}</span> : null}
                      </div>
                    </td>
                    <td>{formatEasternTimestamp(row.published_at)}</td>
                    <td>{formatEasternTimestamp(row.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel">
          <div className="section-header">
            <div>
              <span className="eyebrow">Audit Rows</span>
              <h2>Raw audit log</h2>
            </div>
            <p>Recent pipeline events exactly as stored in the audit table.</p>
          </div>
          <div className="audit-list audit-list-single">
            {rawData.audit_logs.map((row) => (
              <article key={`raw-audit-${row.event_type}-${row.created_at}`} className="audit-card">
                <strong>{row.event_type}</strong>
                <span>{formatEasternTimestamp(row.created_at)}</span>
                <p>{row.message}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="content-grid">
        <div className="panel">
          <div className="section-header">
            <div>
              <span className="eyebrow">Model Rows</span>
              <h2>Raw model outputs</h2>
            </div>
            <p>Latest scored outputs as stored by the model pipeline.</p>
          </div>
          <div className="table-wrap">
            <table className="dense-table">
              <thead>
                <tr>
                  <th>Market ID</th>
                  <th>Deterministic</th>
                  <th>ML</th>
                  <th>AI</th>
                  <th>Final Prob</th>
                  <th>Mispricing</th>
                  <th>Fee EV</th>
                  <th>Trade Score</th>
                  <th>Action</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {rawData.model_runs.map((row) => (
                  <tr key={`raw-model-${row.market_external_id}-${row.created_at}`}>
                    <td>{row.market_external_id}</td>
                    <td>{formatSignedPercent(row.deterministic_edge)}</td>
                    <td>{formatSignedPercent(row.ml_adjustment)}</td>
                    <td>{formatSignedPercent(row.ai_adjustment)}</td>
                    <td>{formatPercent(row.final_probability)}</td>
                    <td className={row.mispricing >= 0 ? "positive" : "negative"}>{formatSignedPercent(row.mispricing)}</td>
                    <td className={row.fee_adjusted_ev >= 0 ? "positive" : "negative"}>{formatSignedPercent(row.fee_adjusted_ev)}</td>
                    <td className={row.trade_score >= 0 ? "positive" : "negative"}>{formatSignedPercent(row.trade_score)}</td>
                    <td>{row.action}</td>
                    <td>{formatEasternTimestamp(row.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel">
          <div className="section-header">
            <div>
              <span className="eyebrow">Trade Rows</span>
              <h2>Raw trade actions</h2>
            </div>
            <p>Simulated trade records stored by the pipeline and execution layer.</p>
          </div>
          <div className="table-wrap">
            <table className="dense-table">
              <thead>
                <tr>
                  <th>Market ID</th>
                  <th>Venue</th>
                  <th>Side</th>
                  <th>Stake</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {rawData.trade_actions.map((row) => (
                  <tr key={`raw-trade-${row.market_external_id}-${row.created_at}-${row.side}`}>
                    <td>
                      <div className="market-cell">
                        <strong>{row.market_external_id}</strong>
                        <span>{row.rationale}</span>
                      </div>
                    </td>
                    <td>{row.venue}</td>
                    <td>{row.side}</td>
                    <td>{formatMoney(row.stake)}</td>
                    <td>{row.status}</td>
                    <td>{formatEasternTimestamp(row.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </main>
  );
}

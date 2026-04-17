import { Market } from "@/lib/types";
import { formatEasternTimestamp } from "@/lib/time";

function formatPercent(value: number) {
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

export function MarketTable({ markets }: { markets: Market[] }) {
  return (
    <div className="panel">
      <div className="section-header">
        <div>
          <span className="eyebrow">Market Monitor</span>
          <h2>Ingestion status, prices, and per-market model output</h2>
        </div>
        <p>
          Each row is a single stored market. Potter shows the last pull time, previous pull, current probability,
          price change, model breakdown, and current action without grouping multiple titles into one unreadable block.
        </p>
      </div>
      <div className="table-wrap">
        <table className="dense-table">
          <thead>
            <tr>
              <th>Market</th>
              <th>Venue</th>
              <th>Last Pull</th>
              <th>Previous</th>
              <th>Now</th>
              <th>Delta</th>
              <th>Potter</th>
              <th>Edge</th>
              <th>Model</th>
              <th>Action</th>
              <th>Confidence</th>
              <th>Liquidity</th>
            </tr>
          </thead>
          <tbody>
            {markets.map((market) => {
              const displayTitle = market.display_title ?? market.question;
              const questionSegments = market.question_segments ?? [market.question];
              const subtitle = market.subtitle ?? null;

              return (
              <tr key={market.id}>
                <td>
                  <div className="market-cell">
                    <strong>{displayTitle}</strong>
                    {subtitle ? <span>{subtitle}</span> : null}
                    {questionSegments.length > 1 ? (
                      <div className="segment-list">
                        {questionSegments.slice(1).map((segment) => (
                          <span key={`${market.id}-${segment}`} className="mini-pill">
                            {segment}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                </td>
                <td>{market.venue}</td>
                <td>{formatEasternTimestamp(market.latest_pull_at)}</td>
                <td>{market.previous_market_prob == null ? "n/a" : formatPercent(market.previous_market_prob)}</td>
                <td>{formatPercent(market.market_prob)}</td>
                <td className={market.price_change >= 0 ? "positive" : "negative"}>{formatSignedPercent(market.price_change)}</td>
                <td>{formatPercent(market.potter_prob)}</td>
                <td className={market.edge >= 0 ? "positive" : "negative"}>{formatSignedPercent(market.edge)}</td>
                <td>
                  <div className="model-micro">
                    <span>M {formatSignedPercent(market.deterministic_edge)}</span>
                    <span>ML {formatSignedPercent(market.ml_confidence_adjustment)}</span>
                    <span>AI {formatSignedPercent(market.ai_news_adjustment)}</span>
                  </div>
                </td>
                <td>
                  <span className={`pill ${market.action.toLowerCase()}`}>{market.action}</span>
                </td>
                <td>{market.confidence}%</td>
                <td>{formatMoney(market.liquidity)}</td>
              </tr>
            )})}
          </tbody>
        </table>
      </div>

      <div className="breakdown-grid market-breakdowns">
        {markets.slice(0, 12).map((market) => {
          const displayTitle = market.display_title ?? market.question;
          return (
          <article key={`${market.id}-breakdown`} className="breakdown-card">
            <div className="breakdown-head">
              <div className="market-cell">
                <strong>{displayTitle}</strong>
                <span>{market.venue} | Last pull {formatEasternTimestamp(market.latest_pull_at)}</span>
              </div>
              <span className={`pill ${market.action.toLowerCase()}`}>{market.action}</span>
            </div>
            <div className="score-row">
              <span>Market {formatPercent(market.market_prob)}</span>
              <span>Previous {market.previous_market_prob == null ? "n/a" : formatPercent(market.previous_market_prob)}</span>
              <span>Potter {formatPercent(market.potter_prob)}</span>
              <span>Edge {formatSignedPercent(market.edge)}</span>
            </div>
            <div className="score-row">
              <span>Math {formatSignedPercent(market.deterministic_edge)}</span>
              <span>ML {formatSignedPercent(market.ml_confidence_adjustment)}</span>
              <span>AI {formatSignedPercent(market.ai_news_adjustment)}</span>
              <span>Final {formatSignedPercent(market.final_score)}</span>
            </div>
            <p>
              <strong>Pricing:</strong> {market.pricing_summary}
            </p>
            <p>
              <strong>ML:</strong> {market.ml_summary}
            </p>
            <p>
              <strong>AI:</strong> {market.ai_summary}
            </p>
            <p>
              <strong>Model timestamp:</strong> {formatEasternTimestamp(market.latest_model_at)}
            </p>
          </article>
        )})}
      </div>
    </div>
  );
}

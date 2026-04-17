import { Market } from "@/lib/types";

function formatPercent(value: number) {
  return `${(value * 100).toFixed(0)}%`;
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
          <span className="eyebrow">Signal Board</span>
          <h2>Top mispriced markets</h2>
        </div>
        <p>Potter compares venue odds to model probability and highlights the strongest edge.</p>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Market</th>
              <th>Venue</th>
              <th>Market</th>
              <th>Potter</th>
              <th>Edge</th>
              <th>Action</th>
              <th>Confidence</th>
              <th>Liquidity</th>
            </tr>
          </thead>
          <tbody>
            {markets.map((market) => (
              <tr key={market.id}>
                <td>
                  <div className="market-cell">
                    <strong>{market.question}</strong>
                    <span>{market.category}</span>
                  </div>
                </td>
                <td>{market.venue}</td>
                <td>{formatPercent(market.market_prob)}</td>
                <td>{formatPercent(market.potter_prob)}</td>
                <td className={market.edge >= 0 ? "positive" : "negative"}>
                  {market.edge >= 0 ? "+" : ""}
                  {formatPercent(market.edge)}
                </td>
                <td>
                  <span className={`pill ${market.action.toLowerCase()}`}>{market.action}</span>
                </td>
                <td>{market.confidence}%</td>
                <td>{formatMoney(market.liquidity)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="breakdown-grid">
        {markets.map((market) => (
          <article key={`${market.id}-breakdown`} className="breakdown-card">
            <div className="breakdown-head">
              <div className="market-cell">
                <strong>{market.question}</strong>
                <span>{market.venue}</span>
              </div>
              <span className={`pill ${market.action.toLowerCase()}`}>{market.action}</span>
            </div>
            <div className="score-row">
              <span>Math {formatPercent(market.deterministic_edge)}</span>
              <span>
                ML {market.ml_confidence_adjustment >= 0 ? "+" : ""}
                {formatPercent(market.ml_confidence_adjustment)}
              </span>
              <span>
                AI {market.ai_news_adjustment >= 0 ? "+" : ""}
                {formatPercent(market.ai_news_adjustment)}
              </span>
              <span>
                Final {market.final_score >= 0 ? "+" : ""}
                {formatPercent(market.final_score)}
              </span>
            </div>
            <p>
              <strong>Math:</strong> {market.pricing_summary}
            </p>
            <p>
              <strong>ML:</strong> {market.ml_summary}
            </p>
            <p>
              <strong>AI:</strong> {market.ai_summary}
            </p>
          </article>
        ))}
      </div>
    </div>
  );
}

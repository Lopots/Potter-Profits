import { Trade } from "@/lib/types";

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

export function TradeFeed({ trades }: { trades: Trade[] }) {
  return (
    <div className="panel">
      <div className="section-header">
        <div>
          <span className="eyebrow">Execution Log</span>
          <h2>Trades and actions</h2>
        </div>
        <p>Every paper trade, hold, or blocked action is recorded so you can see exactly what Potter did.</p>
      </div>
      <div className="trade-list">
        {trades.map((trade) => (
          <article key={trade.id} className="trade-card">
            <div className="trade-topline">
              <div>
                <strong>{trade.market_question}</strong>
                <span>
                  {trade.venue} • {trade.timestamp}
                </span>
              </div>
              <div className="trade-tags">
                <span className={`pill ${trade.side.toLowerCase()}`}>{trade.side}</span>
                <span className={`pill neutral ${trade.status}`}>{trade.status}</span>
              </div>
            </div>
            <div className="trade-metrics">
              <span>Stake {formatMoney(trade.stake)}</span>
              <span>Edge {formatPercent(trade.edge_at_entry)}</span>
              <span>Confidence {trade.confidence}%</span>
            </div>
            <p>{trade.rationale}</p>
          </article>
        ))}
      </div>
    </div>
  );
}

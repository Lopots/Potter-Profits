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
          <h2>Completed trades</h2>
        </div>
        <p>Only closed paper trades are shown here so the log reflects realized actions instead of every hold signal.</p>
      </div>
      <div className="trade-list">
        {trades.length === 0 ? (
          <article className="trade-card">
            <strong>No completed trades yet</strong>
            <p>Potter has open or pending paper positions, but nothing has been closed out into realized P/L yet.</p>
          </article>
        ) : null}
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
              <span className={trade.profit_loss >= 0 ? "positive" : "negative"}>P/L {formatMoney(trade.profit_loss)}</span>
            </div>
            <p>{trade.rationale}</p>
          </article>
        ))}
      </div>
    </div>
  );
}

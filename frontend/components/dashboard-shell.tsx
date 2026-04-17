import { DashboardPageData, PerformancePoint } from "@/lib/types";
import { getCompletedPaperTrades, getPortfolioFallback } from "@/lib/market-nav";
import { formatEasternTimestamp } from "@/lib/time";
import { AppHeader } from "./app-header";
import { PotterAssistant } from "./potter-assistant";
import { StatCard } from "./stat-card";
import { TradeFeed } from "./trade-feed";

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function buildFallbackPerformancePoints(startingBankroll: number, completedTrades: ReturnType<typeof getCompletedPaperTrades>): PerformancePoint[] {
  let equity = startingBankroll;

  return completedTrades.map((trade) => {
    equity += trade.profit_loss || 0;

    return {
      timestamp: trade.timestamp,
      equity,
      bank_balance: equity,
      active_capital: 0,
    };
  });
}

function buildGraphPath(points: PerformancePoint[], width: number, height: number) {
  if (points.length === 0) {
    return "";
  }

  const values = points.map((point) => point.equity);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  return points
    .map((point, index) => {
      const x = points.length === 1 ? width / 2 : (index / (points.length - 1)) * width;
      const y = height - ((point.equity - min) / range) * height;
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
}

function PerformanceChart({ points }: { points: PerformancePoint[] }) {
  if (points.length === 0) {
    return (
      <div className="panel">
        <div className="section-header">
          <div>
            <span className="eyebrow">Performance</span>
            <h2>Equity curve</h2>
          </div>
          <p>No completed trades yet, so there is no realized performance curve to plot.</p>
        </div>
      </div>
    );
  }

  const width = 900;
  const height = 260;
  const path = buildGraphPath(points, width, height);
  const latestPoint = points[points.length - 1];
  const firstPoint = points[0];
  const delta = latestPoint.equity - firstPoint.equity;

  return (
    <div className="panel">
      <div className="section-header">
        <div>
          <span className="eyebrow">Performance</span>
          <h2>Equity curve</h2>
        </div>
        <p>
          Current equity {formatMoney(latestPoint.equity)}{" "}
          <span className={delta >= 0 ? "positive" : "negative"}>{delta >= 0 ? "+" : ""}{formatMoney(delta)}</span>
        </p>
      </div>
      <div className="chart-panel">
        <svg viewBox={`0 0 ${width} ${height}`} className="equity-chart" role="img" aria-label="Paper trading equity curve">
          <defs>
            <linearGradient id="equity-fill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="rgba(45, 127, 249, 0.45)" />
              <stop offset="100%" stopColor="rgba(45, 127, 249, 0.02)" />
            </linearGradient>
          </defs>
          <path d={`M 0 ${height} ${path} L ${width} ${height} Z`} fill="url(#equity-fill)" />
          <path d={path} fill="none" stroke="#69a3ff" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <div className="chart-footer">
          <span>{formatEasternTimestamp(firstPoint.timestamp)}</span>
          <span>{formatEasternTimestamp(latestPoint.timestamp)}</span>
        </div>
      </div>
    </div>
  );
}

export function DashboardShell({ data }: { data: DashboardPageData }) {
  const { dashboard, systemStatus } = data;
  const { potter, trades, portfolio } = dashboard;
  const completedTrades = getCompletedPaperTrades(trades);
  const safePortfolio = portfolio ?? getPortfolioFallback(trades);
  const performancePoints =
    safePortfolio.performance_points.length > 0
      ? safePortfolio.performance_points
      : buildFallbackPerformancePoints(safePortfolio.starting_bankroll, completedTrades);

  return (
    <main className="page-shell">
      <AppHeader
        activePage="dashboard"
        latestMarketCapture={systemStatus.latest_market_capture}
        latestModelRun={systemStatus.latest_model_run}
        modeLabel={potter.mode === "paper" ? "Paper trading active" : "Live locked"}
      />

      <section className="primary-grid">
        <PotterAssistant />
      </section>

      <section className="stats-grid">
        <StatCard
          label="Bank Balance"
          value={formatMoney(safePortfolio.bank_balance)}
          detail="Cash currently back in the paper bank and not committed to open positions."
        />
        <StatCard
          label="Active Capital"
          value={formatMoney(safePortfolio.active_capital)}
          detail="Paper capital currently deployed into open markets."
        />
        <StatCard
          label="Realized P/L"
          value={formatMoney(safePortfolio.realized_pnl)}
          detail="Profit or loss from completed trades only."
        />
        <StatCard
          label="Unrealized P/L"
          value={formatMoney(safePortfolio.unrealized_pnl)}
          detail="Mark-to-market profit or loss on open positions."
        />
      </section>

      <section className="stats-grid">
        <StatCard
          label="Total Equity"
          value={formatMoney(safePortfolio.total_equity)}
          detail="Bank balance plus active capital and current unrealized P/L."
        />
        <StatCard
          label="Completed Trades"
          value={String(safePortfolio.completed_trades)}
          detail="Only closed trades are counted here."
        />
        <StatCard
          label="Open Positions"
          value={String(safePortfolio.open_positions)}
          detail="Money still in the market and not yet returned to the bank."
        />
        <StatCard
          label="Latest Price Pull"
          value={formatEasternTimestamp(systemStatus.latest_market_capture)}
          detail="Most recent market price refresh driving current marks."
        />
      </section>

      <section className="primary-grid">
        <PerformanceChart points={performancePoints} />
      </section>

      <section className="primary-grid">
        <TradeFeed trades={completedTrades} />
      </section>
    </main>
  );
}

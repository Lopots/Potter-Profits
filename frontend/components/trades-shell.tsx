import { DashboardPageData } from "@/lib/types";
import { getCompletedPaperTrades, getPortfolioFallback } from "@/lib/market-nav";
import { AppHeader } from "./app-header";
import { TradeFeed } from "./trade-feed";

export function TradesShell({ data }: { data: DashboardPageData }) {
  const { dashboard, systemStatus } = data;
  const { potter, trades } = dashboard;
  const completedTrades = getCompletedPaperTrades(trades);
  const safePortfolio = dashboard.portfolio ?? getPortfolioFallback(trades);

  return (
    <main className="page-shell">
      <AppHeader
        activePage="trades"
        latestMarketCapture={systemStatus.latest_market_capture}
        latestModelRun={systemStatus.latest_model_run}
        modeLabel={potter.mode === "paper" ? "Paper trading active" : "Live locked"}
      />
      <section className="panel section-intro">
        <span className="eyebrow">Trades</span>
        <h2>Completed paper trades and realized results</h2>
        <p>
          This page now focuses on completed paper trades instead of showing every hold and blocked action. Open
          positions remain in the portfolio summary, while closed trades stay here as the realized action log.
        </p>
        <div className="mini-summary">
          <span className="mini-pill">{completedTrades.length} completed trades</span>
          <span className="mini-pill">{safePortfolio.open_positions} open positions</span>
          <span className="mini-pill">Realized P/L ${safePortfolio.realized_pnl.toFixed(2)}</span>
        </div>
      </section>
      <section className="stack-section">
        <TradeFeed trades={completedTrades} />
      </section>
    </main>
  );
}

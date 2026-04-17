import { DashboardPageData } from "@/lib/types";
import { AppHeader } from "./app-header";
import { MarketTable } from "./market-table";

export function MarketsShell({ data }: { data: DashboardPageData }) {
  const { dashboard, systemStatus } = data;
  const { potter, markets } = dashboard;

  return (
    <main className="page-shell">
      <AppHeader
        activePage="markets"
        latestMarketCapture={systemStatus.latest_market_capture}
        latestModelRun={systemStatus.latest_model_run}
        modeLabel={potter.mode === "paper" ? "Paper trading active" : "Live locked"}
      />
      <section className="panel section-intro">
        <span className="eyebrow">Markets</span>
        <h2>Per-market pricing, edge, and model breakdowns</h2>
        <p>
          This page is focused entirely on market rows. Each market is separated cleanly, with previous price,
          current price, delta, Potter probability, edge, and model contribution visible in one place.
        </p>
        <div className="mini-summary">
          <span className="mini-pill">{markets.length} tracked markets</span>
          <span className="mini-pill">{dashboard.snapshot.buy_signals} buy signals</span>
          <span className="mini-pill">{dashboard.snapshot.sell_signals} sell signals</span>
        </div>
      </section>
      <section className="stack-section">
        <MarketTable markets={markets} />
      </section>
    </main>
  );
}

import { DashboardPageData } from "@/lib/types";
import { AppHeader } from "./app-header";
import { TradeFeed } from "./trade-feed";

export function TradesShell({ data }: { data: DashboardPageData }) {
  const { dashboard, systemStatus } = data;
  const { potter, trades } = dashboard;

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
        <h2>Execution history, holds, and blocked actions</h2>
        <p>
          This page is dedicated to Potter's action trail so you can inspect simulated trades, skipped markets,
          rationale, edge at entry, and confidence without the rest of the dashboard competing for space.
        </p>
      </section>
      <section className="stack-section">
        <TradeFeed trades={trades} />
      </section>
    </main>
  );
}

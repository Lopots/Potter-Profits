import { DashboardPageData } from "@/lib/types";
import { AppHeader } from "./app-header";
import { formatEasternTimestamp } from "@/lib/time";
import { MarketTable } from "./market-table";
import { ModelStack } from "./model-stack";
import { PotterPanel } from "./potter-panel";
import { StatCard } from "./stat-card";
import { SystemPanel } from "./system-panel";
import { TradeFeed } from "./trade-feed";

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export function DashboardShell({ data }: { data: DashboardPageData }) {
  const { dashboard, systemStatus } = data;
  const { snapshot, model_layers, markets, potter, trades } = dashboard;

  return (
    <main className="page-shell">
      <AppHeader
        activePage="dashboard"
        latestMarketCapture={systemStatus.latest_market_capture}
        latestModelRun={systemStatus.latest_model_run}
        modeLabel={potter.mode === "paper" ? "Paper trading active" : "Live locked"}
      />

      <section id="overview" className="stats-grid">
        <StatCard
          label="Tracked Markets"
          value={String(snapshot.total_markets)}
          detail="Distinct market rows currently being monitored and scored individually."
        />
        <StatCard
          label="Buy Signals"
          value={String(snapshot.buy_signals)}
          detail="Markets whose latest model edge cleared the current buy threshold."
        />
        <StatCard
          label="Average Edge"
          value={formatPercent(snapshot.average_edge)}
          detail="Average difference between venue probability and Potter probability."
        />
        <StatCard
          label="Strongest Edge"
          value={formatPercent(snapshot.strongest_edge)}
          detail="Largest single-market divergence currently stored in the board."
        />
      </section>

      <section className="content-grid">
        <SystemPanel systemStatus={systemStatus} />
        <PotterPanel potter={potter} />
      </section>

      <section className="stats-grid">
        <StatCard
          label="Latest Market Pull"
          value={formatEasternTimestamp(systemStatus.latest_market_capture)}
          detail="Go to the Ingestion page for exact ET pull times and previous-vs-current pricing."
        />
        <StatCard
          label="Stored Model Runs"
          value={String(systemStatus.model_run_count)}
          detail="Go to the Models page for layer details and current reasoning context."
        />
        <StatCard
          label="Stored Trades"
          value={String(trades.length)}
          detail="Go to the Trades page to inspect the latest action trail and rationale."
        />
        <StatCard
          label="Stored News"
          value={String(systemStatus.news_count)}
          detail="Go to the Ingestion page to see freshness and recent pipeline audit events."
        />
      </section>
    </main>
  );
}

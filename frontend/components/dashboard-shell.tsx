import { DashboardPageData } from "@/lib/types";
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
      <section className="topbar panel">
        <div>
          <span className="eyebrow">Potter Profits</span>
          <h1 className="topbar-title">Market Ops Console</h1>
        </div>
        <nav className="page-nav" aria-label="Primary">
          <a href="#overview">Overview</a>
          <a href="#markets">Markets</a>
          <a href="#models">Models</a>
          <a href="#system">System</a>
          <a href="#trades">Trades</a>
        </nav>
        <div className="status-strip">
          <div>
            <span className="eyebrow">Mode</span>
            <strong>{potter.mode === "paper" ? "Paper trading active" : "Live locked"}</strong>
          </div>
          <div>
            <span className="eyebrow">Latest Market Pull</span>
            <strong>{systemStatus.latest_market_capture ? new Date(systemStatus.latest_market_capture).toLocaleString() : "Waiting"}</strong>
          </div>
          <div>
            <span className="eyebrow">Latest Model Run</span>
            <strong>{systemStatus.latest_model_run ? new Date(systemStatus.latest_model_run).toLocaleString() : "Waiting"}</strong>
          </div>
        </div>
      </section>

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

      <section id="markets" className="primary-grid">
        <MarketTable markets={markets} />
      </section>

      <section className="content-grid">
        <SystemPanel systemStatus={systemStatus} />
        <PotterPanel potter={potter} />
      </section>

      <section id="models" className="stack-section">
        <ModelStack layers={model_layers} />
      </section>

      <section id="trades">
        <TradeFeed trades={trades} />
      </section>
    </main>
  );
}

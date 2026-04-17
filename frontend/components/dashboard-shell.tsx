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
      <section className="hero">
        <div className="hero-copy">
          <span className="hero-chip">Potter Profits</span>
          <h1>Find prediction market mispricing before the crowd does.</h1>
          <p>
            Potter watches active markets, estimates fair probability, paper trades high-confidence edges,
            and keeps a full audit trail of every decision.
          </p>
        </div>
        <div className="hero-card">
          <span className="eyebrow">Live Status</span>
          <strong>Potter is running in paper mode</strong>
          <p>Auto-execution is simulated now, with live venues intentionally locked until safety controls are added.</p>
        </div>
      </section>

      <section className="stats-grid">
        <StatCard
          label="Tracked Markets"
          value={String(snapshot.total_markets)}
          detail="Active venues currently monitored by Potter."
        />
        <StatCard
          label="Buy Signals"
          value={String(snapshot.buy_signals)}
          detail="Markets with edge above the current buy threshold."
        />
        <StatCard
          label="Average Edge"
          value={formatPercent(snapshot.average_edge)}
          detail="Mean difference between market odds and Potter probability."
        />
        <StatCard
          label="Strongest Edge"
          value={formatPercent(snapshot.strongest_edge)}
          detail="Largest divergence available on the current board."
        />
      </section>

      <section className="content-grid">
        <PotterPanel potter={potter} />
        <MarketTable markets={markets} />
      </section>

      <section className="stack-section">
        <ModelStack layers={model_layers} />
      </section>

      <section className="stack-section">
        <SystemPanel systemStatus={systemStatus} />
      </section>

      <section>
        <TradeFeed trades={trades} />
      </section>
    </main>
  );
}

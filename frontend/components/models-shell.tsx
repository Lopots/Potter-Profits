import { DashboardPageData } from "@/lib/types";
import { AppHeader } from "./app-header";
import { ModelStack } from "./model-stack";
import { PotterPanel } from "./potter-panel";
import { SystemPanel } from "./system-panel";

export function ModelsShell({ data }: { data: DashboardPageData }) {
  const { dashboard, systemStatus } = data;
  const { potter, model_layers } = dashboard;

  return (
    <main className="page-shell">
      <AppHeader
        activePage="models"
        latestMarketCapture={systemStatus.latest_market_capture}
        latestModelRun={systemStatus.latest_model_run}
        modeLabel={potter.mode === "paper" ? "Paper trading active" : "Live locked"}
      />
      <section className="panel section-intro">
        <span className="eyebrow">Models</span>
        <h2>How Potter builds probability and decides what to do</h2>
        <p>
          This page focuses on the deterministic pricing layer, ML validation layer, AI context layer, and
          the current Potter reasoning feed that sits on top of those model outputs.
        </p>
      </section>
      <section className="stack-section">
        <ModelStack layers={model_layers} />
      </section>
      <section className="content-grid">
        <SystemPanel systemStatus={systemStatus} />
        <PotterPanel potter={potter} />
      </section>
    </main>
  );
}

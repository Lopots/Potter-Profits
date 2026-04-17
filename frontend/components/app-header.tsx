import Link from "next/link";
import { formatEasternTimestamp } from "@/lib/time";

interface AppHeaderProps {
  latestMarketCapture?: string | null;
  latestModelRun?: string | null;
  modeLabel: string;
  activePage?: "dashboard" | "ingestion" | "markets" | "models" | "trades" | "data";
}

export function AppHeader({ latestMarketCapture, latestModelRun, modeLabel, activePage = "dashboard" }: AppHeaderProps) {
  return (
    <section className="topbar panel">
      <div>
        <span className="eyebrow">Potter Profits</span>
        <h1 className="topbar-title">Market Ops Console</h1>
      </div>
      <nav className="page-nav" aria-label="Primary">
        <Link className={activePage === "dashboard" ? "active" : ""} href="/">Dashboard</Link>
        <Link className={activePage === "ingestion" ? "active" : ""} href="/ingestion">Ingestion</Link>
        <Link className={activePage === "markets" ? "active" : ""} href="/markets">Markets</Link>
        <Link className={activePage === "models" ? "active" : ""} href="/models">Models</Link>
        <Link className={activePage === "trades" ? "active" : ""} href="/trades">Trades</Link>
        <Link className={activePage === "data" ? "active" : ""} href="/data">Data</Link>
      </nav>
      <div className="status-strip">
        <div>
          <span className="eyebrow">Mode</span>
          <strong>{modeLabel}</strong>
        </div>
        <div>
          <span className="eyebrow">Latest Market Pull</span>
          <strong>{formatEasternTimestamp(latestMarketCapture)}</strong>
        </div>
        <div>
          <span className="eyebrow">Latest Model Run</span>
          <strong>{formatEasternTimestamp(latestModelRun)}</strong>
        </div>
      </div>
    </section>
  );
}

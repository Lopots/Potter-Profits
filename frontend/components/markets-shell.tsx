import Link from "next/link";

import { DashboardPageData } from "@/lib/types";
import {
  buildCategoryGroups,
  buildSubcategoryGroups,
  getCategoryRoute,
  getMarketDisplayTitle,
  getMarketRoute,
  getNoLabel,
  getNoProbability,
  getPortfolioFallback,
  getYesLabel,
  getYesProbability,
} from "@/lib/market-nav";
import { AppHeader } from "./app-header";

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export function MarketsShell({ data }: { data: DashboardPageData }) {
  const { dashboard, systemStatus } = data;
  const { potter, markets } = dashboard;
  const categoryGroups = buildCategoryGroups(markets);
  const safePortfolio = dashboard.portfolio ?? getPortfolioFallback(dashboard.trades);

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
        <h2>Browse by category first, then drill into an individual market</h2>
        <p>
          This page now works more like a venue browse experience. Start with a category, then open a single market
          to read probability, edge, last pull timing, and model context without the concatenated wall of text.
        </p>
        <div className="mini-summary">
          <span className="mini-pill">{categoryGroups.length} categories</span>
          <span className="mini-pill">{markets.length} total markets</span>
          <span className="mini-pill">{safePortfolio.open_positions} open paper positions</span>
        </div>
      </section>

      <section className="category-grid">
        {categoryGroups.map((group) => {
          const strongest = group.markets[0];

          return (
            <article key={group.slug} className="panel category-card">
              <div className="section-header">
                <div>
                  <span className="eyebrow">Category</span>
                  <h2>{group.label}</h2>
                </div>
                <Link className="mini-pill" href={getCategoryRoute(group.label)}>
                  View category
                </Link>
              </div>
              <p>{group.markets.length} markets currently stored in this category.</p>
              <div className="category-links">
                {buildSubcategoryGroups(group.markets).map((subgroup) => (
                  <span key={`${group.slug}-${subgroup.slug}`} className="mini-pill">
                    {subgroup.label} ({subgroup.markets.length})
                  </span>
                ))}
              </div>
              {strongest ? (
                <div className="category-highlight">
                  <strong>Top edge right now</strong>
                  <Link href={getMarketRoute(group.label, strongest.id)}>{getMarketDisplayTitle(strongest)}</Link>
                  <span>
                    {getYesLabel(strongest)} {formatPercent(getYesProbability(strongest))} | {getNoLabel(strongest)}{" "}
                    {formatPercent(getNoProbability(strongest))}
                  </span>
                </div>
              ) : null}
              <div className="category-links">
                {group.markets.slice(0, 6).map((market) => (
                  <Link key={`${group.slug}-${market.id}`} className="mini-pill" href={getMarketRoute(group.label, market.id)}>
                    {getMarketDisplayTitle(market)}
                  </Link>
                ))}
              </div>
            </article>
          );
        })}
      </section>
    </main>
  );
}

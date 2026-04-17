import Link from "next/link";

import { DashboardPageData } from "@/lib/types";
import {
  MarketCategoryGroup,
  buildSubcategoryGroups,
  getMarketDisplayTitle,
  getMarketRoute,
  getMarketSecondaryLines,
  getNoLabel,
  getNoProbability,
  getYesLabel,
  getYesProbability,
} from "@/lib/market-nav";
import { formatEasternTimestamp } from "@/lib/time";
import { AppHeader } from "./app-header";

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatSignedPercent(value: number) {
  return `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}%`;
}

export function CategoryShell({
  data,
  categoryGroup,
}: {
  data: DashboardPageData;
  categoryGroup: MarketCategoryGroup;
}) {
  const { dashboard, systemStatus } = data;
  const { potter } = dashboard;
  const subcategoryGroups = buildSubcategoryGroups(categoryGroup.markets);

  return (
    <main className="page-shell">
      <AppHeader
        activePage="markets"
        latestMarketCapture={systemStatus.latest_market_capture}
        latestModelRun={systemStatus.latest_model_run}
        modeLabel={potter.mode === "paper" ? "Paper trading active" : "Live locked"}
      />
      <section className="panel section-intro">
        <span className="eyebrow">Category</span>
        <h2>{categoryGroup.label}</h2>
        <p>Each row here is one market. Open a market for the cleaner detail view with probability and model context.</p>
        <div className="mini-summary">
          <span className="mini-pill">{categoryGroup.markets.length} markets</span>
          <Link className="mini-pill" href="/markets">
            Back to categories
          </Link>
        </div>
      </section>

      {subcategoryGroups.map((subgroup) => (
        <section key={`${categoryGroup.slug}-${subgroup.slug}`} className="panel stack-section">
          <div className="section-header">
            <div>
              <span className="eyebrow">Subcategory</span>
              <h2>{subgroup.label}</h2>
            </div>
            <p>{subgroup.markets.length} markets in this slice.</p>
          </div>
          <div className="table-wrap">
            <table className="dense-table">
              <thead>
                <tr>
                  <th>Market</th>
                  <th>Venue</th>
                  <th>Last Pull</th>
                  <th>Yes</th>
                  <th>No</th>
                  <th>Potter</th>
                  <th>Edge</th>
                  <th>Action</th>
                  <th>Open</th>
                </tr>
              </thead>
              <tbody>
                {subgroup.markets.map((market) => (
                  <tr key={`${subgroup.slug}-${market.id}`}>
                    <td>
                      <div className="market-cell">
                        <strong>{getMarketDisplayTitle(market)}</strong>
                        {getMarketSecondaryLines(market).map((line, index) => (
                          <span key={`${market.id}-${index}`}>{line}</span>
                        ))}
                      </div>
                    </td>
                    <td>{market.venue}</td>
                    <td>{formatEasternTimestamp(market.latest_pull_at)}</td>
                    <td>{getYesLabel(market)} {formatPercent(getYesProbability(market))}</td>
                    <td>{getNoLabel(market)} {formatPercent(getNoProbability(market))}</td>
                    <td>{formatPercent(market.potter_prob)}</td>
                    <td className={market.edge >= 0 ? "positive" : "negative"}>{formatSignedPercent(market.edge)}</td>
                    <td>
                      <span className={`pill ${market.action.toLowerCase()}`}>{market.action}</span>
                    </td>
                    <td>
                      <Link className="mini-pill" href={getMarketRoute(categoryGroup.label, market.id)}>
                        View market
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </main>
  );
}

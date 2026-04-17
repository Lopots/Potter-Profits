import Link from "next/link";

import { DashboardPageData, Market } from "@/lib/types";
import {
  MarketCategoryGroup,
  getCategoryRoute,
  getEffectiveSubcategory,
  getMarketDisplayTitle,
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

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function MarketDetailShell({
  data,
  categoryGroup,
  market,
}: {
  data: DashboardPageData;
  categoryGroup: MarketCategoryGroup;
  market: Market;
}) {
  const { dashboard, systemStatus } = data;
  const { potter } = dashboard;
  const subcategory = getEffectiveSubcategory(market);

  return (
    <main className="page-shell">
      <AppHeader
        activePage="markets"
        latestMarketCapture={systemStatus.latest_market_capture}
        latestModelRun={systemStatus.latest_model_run}
        modeLabel={potter.mode === "paper" ? "Paper trading active" : "Live locked"}
      />

      <section className="panel section-intro">
        <span className="eyebrow">Market Detail</span>
        <h2>{getMarketDisplayTitle(market)}</h2>
        <p>{getMarketSecondaryLines(market).join(" • ") || market.subtitle || market.question}</p>
        <div className="mini-summary">
          <span className="mini-pill">{categoryGroup.label}</span>
          <span className="mini-pill">{market.venue}</span>
          <Link className="mini-pill" href={getCategoryRoute(categoryGroup.label)}>
            Back to {categoryGroup.label}
          </Link>
        </div>
      </section>

      <section className="stats-grid">
        <div className="panel stat-card">
          <span className="eyebrow">{getYesLabel(market)} Probability</span>
          <strong>{formatPercent(getYesProbability(market))}</strong>
          <p>Latest venue-implied probability for the Yes side.</p>
        </div>
        <div className="panel stat-card">
          <span className="eyebrow">{getNoLabel(market)} Probability</span>
          <strong>{formatPercent(getNoProbability(market))}</strong>
          <p>Latest venue-implied probability for the No side.</p>
        </div>
        <div className="panel stat-card">
          <span className="eyebrow">Potter Yes Estimate</span>
          <strong>{formatPercent(market.potter_prob)}</strong>
          <p>Potter&apos;s latest blended estimate for the Yes side.</p>
        </div>
        <div className="panel stat-card">
          <span className="eyebrow">Recommended Side</span>
          <strong className={market.edge >= 0 ? "positive" : "negative"}>
            {market.edge >= 0 ? getYesLabel(market) : getNoLabel(market)}
          </strong>
          <p>Current model lean based on the gap between Potter and the venue price.</p>
        </div>
      </section>

      <section className="content-grid">
        <div className="panel">
          <div className="section-header">
            <div>
              <span className="eyebrow">Probability Context</span>
              <h2>Current state</h2>
            </div>
            <p>Read this market on its own instead of bundled with adjacent contract titles.</p>
          </div>
          <div className="explanation-grid explanation-grid-single">
            <article className="explanation-card">
              <span className="eyebrow">Timing</span>
              <p>Last pull: {formatEasternTimestamp(market.latest_pull_at)}</p>
              <p>Previous pull: {formatEasternTimestamp(market.previous_pull_at)}</p>
              <p>Latest model run: {formatEasternTimestamp(market.latest_model_at)}</p>
            </article>
            <article className="explanation-card">
              <span className="eyebrow">Pricing</span>
              <p>{getYesLabel(market)}: {formatPercent(getYesProbability(market))}</p>
              <p>{getNoLabel(market)}: {formatPercent(getNoProbability(market))}</p>
              <p>
                Previous yes probability:{" "}
                {market.previous_market_prob == null ? "n/a" : formatPercent(market.previous_market_prob)}
              </p>
              <p>
                Change:{" "}
                <span className={market.price_change >= 0 ? "positive" : "negative"}>
                  {formatSignedPercent(market.price_change)}
                </span>
              </p>
            </article>
            <article className="explanation-card">
              <span className="eyebrow">Action</span>
              <p>Potter action: {market.action}</p>
              <p>Confidence: {market.confidence}%</p>
              <p>
                Category: {categoryGroup.label}
                {subcategory ? ` • ${subcategory}` : ""}
              </p>
              <p>Liquidity: {formatMoney(market.liquidity)}</p>
            </article>
          </div>
        </div>

        <div className="panel">
          <div className="section-header">
            <div>
              <span className="eyebrow">Model Breakdown</span>
              <h2>Why Potter moved the probability</h2>
            </div>
            <p>The current score is decomposed into deterministic pricing, ML adjustment, and AI/news context.</p>
          </div>
          <div className="breakdown-grid">
            <article className="breakdown-card">
              <div className="breakdown-head">
                <strong>Math</strong>
                <span className={market.deterministic_edge >= 0 ? "positive" : "negative"}>
                  {formatSignedPercent(market.deterministic_edge)}
                </span>
              </div>
              <p>{market.pricing_summary}</p>
            </article>
            <article className="breakdown-card">
              <div className="breakdown-head">
                <strong>ML</strong>
                <span className={market.ml_confidence_adjustment >= 0 ? "positive" : "negative"}>
                  {formatSignedPercent(market.ml_confidence_adjustment)}
                </span>
              </div>
              <p>{market.ml_summary}</p>
            </article>
            <article className="breakdown-card">
              <div className="breakdown-head">
                <strong>AI</strong>
                <span className={market.ai_news_adjustment >= 0 ? "positive" : "negative"}>
                  {formatSignedPercent(market.ai_news_adjustment)}
                </span>
              </div>
              <p>{market.ai_summary}</p>
            </article>
            <article className="breakdown-card">
              <div className="breakdown-head">
                <strong>Final Score</strong>
                <span className={market.final_score >= 0 ? "positive" : "negative"}>
                  {formatSignedPercent(market.final_score)}
                </span>
              </div>
              <p>Potter blends the three layers into a final tradable score and action.</p>
            </article>
          </div>
        </div>
      </section>
    </main>
  );
}

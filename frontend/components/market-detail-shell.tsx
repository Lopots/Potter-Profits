import Link from "next/link";

import { DashboardPageData, Market } from "@/lib/types";
import {
  MarketCategoryGroup,
  getCategoryRoute,
  getEffectiveGameLabel,
  getEffectiveMarketType,
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
  const gameLabel = getEffectiveGameLabel(market);
  const marketType = getEffectiveMarketType(market);

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
        <p>{getMarketSecondaryLines(market).join(" | ") || market.subtitle || market.question}</p>
        <div className="mini-summary">
          <span className="mini-pill">{categoryGroup.label}</span>
          <span className="mini-pill">{subcategory}</span>
          <span className="mini-pill">{marketType}</span>
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
          <span className="eyebrow">Potter True Probability</span>
          <strong>{formatPercent(market.potter_prob)}</strong>
          <p>Potter&apos;s latest blended true-probability estimate for the Yes side.</p>
        </div>
        <div className="panel stat-card">
          <span className="eyebrow">Fee-Adjusted EV</span>
          <strong className={market.fee_adjusted_ev >= 0 ? "positive" : "negative"}>
            {formatSignedPercent(market.fee_adjusted_ev)}
          </strong>
          <p>Net expected value on the Yes side after subtracting the configured prediction-market fee.</p>
        </div>
      </section>

      <section className="content-grid">
        <div className="panel">
          <div className="section-header">
            <div>
              <span className="eyebrow">Probability Context</span>
              <h2>Current state</h2>
            </div>
            <p>Read this market on its own, with pricing, mispricing, EV, and action thresholds visible together.</p>
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
                Mispricing:{" "}
                <span className={market.mispricing >= 0 ? "positive" : "negative"}>
                  {formatSignedPercent(market.mispricing)}
                </span>
              </p>
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
              <span className="eyebrow">Trade Gate</span>
              <p>Potter action: {market.action}</p>
              <p>Confidence: {market.confidence}%</p>
              <p>
                Gross EV Yes:{" "}
                <span className={market.expected_value >= 0 ? "positive" : "negative"}>
                  {formatSignedPercent(market.expected_value)}
                </span>
              </p>
              <p>
                Gross EV No:{" "}
                <span className={market.expected_value_no >= 0 ? "positive" : "negative"}>
                  {formatSignedPercent(market.expected_value_no)}
                </span>
              </p>
              <p>
                Fee-adjusted EV No:{" "}
                <span className={market.fee_adjusted_ev_no >= 0 ? "positive" : "negative"}>
                  {formatSignedPercent(market.fee_adjusted_ev_no)}
                </span>
              </p>
              <p>
                Trade score:{" "}
                <span className={market.trade_score >= 0 ? "positive" : "negative"}>
                  {formatSignedPercent(market.trade_score)}
                </span>
              </p>
              <p>Action threshold: {formatPercent(market.action_threshold)}</p>
              <p>Fee rate: {formatPercent(market.fee_rate)}</p>
              <p>
                Recommended side:{" "}
                <strong className={market.mispricing >= 0 ? "positive" : "negative"}>
                  {market.mispricing >= 0 ? getYesLabel(market) : getNoLabel(market)}
                </strong>
              </p>
              <p>
                Category: {categoryGroup.label}
                {subcategory ? ` | ${subcategory}` : ""}
              </p>
              <p>Game: {gameLabel}</p>
              <p>Market type: {marketType}</p>
              <p>Liquidity: {formatMoney(market.liquidity)}</p>
            </article>
          </div>
        </div>

        <div className="panel">
          <div className="section-header">
            <div>
              <span className="eyebrow">Model Breakdown</span>
              <h2>How Potter gets to a trade</h2>
            </div>
            <p>Potter builds a true probability first, then turns it into mispricing, EV, and an action.</p>
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
                <strong>Decision Metric</strong>
                <span className={market.fee_adjusted_ev >= 0 ? "positive" : "negative"}>
                  {formatSignedPercent(market.fee_adjusted_ev)}
                </span>
              </div>
              <p>
                Potter blends the three layers into a true probability, then converts that into mispricing,
                fee-adjusted EV, and a liquidity/confidence-weighted trade score before deciding whether the
                10-point action threshold is met.
              </p>
            </article>
          </div>
        </div>
      </section>
    </main>
  );
}

import type { Route } from "next";

import { Market, PortfolioSummary, Trade } from "./types";

export interface MarketCategoryGroup {
  slug: string;
  label: string;
  markets: Market[];
}

export interface MarketSubcategoryGroup {
  slug: string;
  label: string;
  markets: Market[];
}

export interface MarketGameGroup {
  slug: string;
  label: string;
  markets: Market[];
}

export function slugifySegment(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function isFiniteNumber(value: number | null | undefined): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function clampProbability(value: number) {
  return Math.min(1, Math.max(0, value));
}

function isGenericLabel(value: string | null | undefined) {
  if (!value) {
    return true;
  }

  return ["kalshi", "polymarket", "general", "uncategorized", "markets"].includes(value.trim().toLowerCase());
}

function marketText(market: Market) {
  return [
    market.display_title,
    market.subtitle,
    market.question,
    market.group_label,
    market.subcategory,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function explicitSegments(market: Market) {
  const directSegments = market.question_segments?.map((segment) => segment.trim()).filter(Boolean) ?? [];
  if (directSegments.length > 0) {
    return [...new Set(directSegments)];
  }

  return [market.display_title || market.question]
    .flatMap((segment) => segment.split("|"))
    .map((segment) => segment.trim())
    .filter(Boolean);
}

export function isStandaloneMarket(market: Market) {
  const text = marketText(market);
  const segments = explicitSegments(market);
  const yesCount = (text.match(/\byes\b/g) ?? []).length;
  const noCount = (text.match(/\bno\b/g) ?? []).length;

  if (market.id.toLowerCase().includes("multigame")) {
    return false;
  }

  if (segments.length >= 4) {
    return false;
  }

  if (yesCount >= 4 || noCount >= 4) {
    return false;
  }

  return true;
}

export function getMarketDisplayTitle(market: Market) {
  const segments = explicitSegments(market);
  return segments[0] ?? market.display_title ?? market.question;
}

export function getMarketSecondaryLines(market: Market) {
  const segments = explicitSegments(market).slice(1);
  if (segments.length > 0) {
    return segments;
  }

  return [market.game_label, market.group_label, market.subtitle]
    .filter(Boolean)
    .map((value) => String(value).trim())
    .filter(Boolean);
}

export function getYesLabel(market: Market) {
  return market.yes_label?.trim() || "Yes";
}

export function getNoLabel(market: Market) {
  return market.no_label?.trim() || "No";
}

export function getYesProbability(market: Market) {
  if (isFiniteNumber(market.yes_prob)) {
    return clampProbability(market.yes_prob);
  }

  if (isFiniteNumber(market.market_prob)) {
    return clampProbability(market.market_prob);
  }

  return 0;
}

export function getNoProbability(market: Market) {
  if (isFiniteNumber(market.no_prob)) {
    return clampProbability(market.no_prob);
  }

  return clampProbability(1 - getYesProbability(market));
}

export function getEffectiveCategory(market: Market) {
  if (!isGenericLabel(market.category)) {
    return market.category;
  }

  const text = marketText(market);

  if (/(nba|mlb|nfl|nhl|soccer|football|baseball|basketball|tennis|golf|runs|goals|points|rebounds|assists|pitcher|innings|touchdown|win game)/.test(text)) {
    return "Sports";
  }

  if (/(election|president|senate|house|governor|vote|approval|democrat|republican|white house|trump|biden)/.test(text)) {
    return "Politics";
  }

  if (/(fed|inflation|rates|cpi|gdp|unemployment|recession|treasury|yield|economy)/.test(text)) {
    return "Economy";
  }

  if (/(bitcoin|btc|ethereum|eth|crypto|solana)/.test(text)) {
    return "Crypto";
  }

  return "Current Events";
}

export function getEffectiveSubcategory(market: Market) {
  if (!isGenericLabel(market.subcategory)) {
    return market.subcategory as string;
  }

  const text = marketText(market);
  const category = getEffectiveCategory(market);

  if (category === "Sports") {
    if (/(nba|basketball|rebounds|assists|points|banchero|booker|miller|knicks|lakers|celtics)/.test(text)) {
      return "NBA";
    }
    if (/(mlb|baseball|runs|innings|cubs|yankees|pitcher|home run|devers|harper)/.test(text)) {
      return "MLB";
    }
    if (/(nfl|touchdown|passing|rushing|receiving|chiefs|eagles|cowboys)/.test(text)) {
      return "NFL";
    }
    if (/(nhl|hockey|goalie|puck|stanley cup)/.test(text)) {
      return "NHL";
    }
    if (/(soccer|fc |goals scored|premier league|champions league|bundesliga|inter |lens|k[öo]ln)/.test(text)) {
      return "Soccer";
    }

    return "Other Sports";
  }

  if (category === "Politics") {
    if (/(president|white house|trump|biden)/.test(text)) {
      return "Presidential";
    }
    if (/(senate)/.test(text)) {
      return "Senate";
    }
    if (/(house)/.test(text)) {
      return "House";
    }

    return "Politics";
  }

  if (category === "Economy") {
    if (/(fed|rates|cpi|inflation)/.test(text)) {
      return "Rates & Inflation";
    }

    return "Macro";
  }

  return category;
}

export function getEffectiveGameLabel(market: Market) {
  if (market.game_label?.trim()) {
    return market.game_label.trim();
  }

  if (market.group_label?.trim()) {
    return market.group_label.trim();
  }

  const secondary = getMarketSecondaryLines(market);
  if (secondary.length > 0) {
    return secondary[0];
  }

  return "Other Markets";
}

export function getEffectiveMarketType(market: Market) {
  if (market.market_type?.trim()) {
    return market.market_type.trim();
  }

  const text = marketText(market);
  if (/(points|rebounds|assists|hits|strikeouts|home runs|passing|rushing|receiving|1\+|2\+|3\+|10\+|15\+|20\+|25\+|30\+)/.test(text)) {
    return "Player Prop";
  }
  if (/(over|under|wins by|spread|run line|goal line|totals|scored)/.test(text)) {
    return "Game Line";
  }
  if (/(win|beat|moneyline|to win)/.test(text)) {
    return "Moneyline";
  }

  return "Market";
}

export function buildCategoryGroups(markets: Market[]) {
  const grouped = new Map<string, Market[]>();
  const standaloneMarkets = markets.filter(isStandaloneMarket);
  const browseMarkets = standaloneMarkets.length > 0 ? standaloneMarkets : markets;

  for (const market of browseMarkets) {
    const label = getEffectiveCategory(market);
    const bucket = grouped.get(label) ?? [];
    bucket.push(market);
    grouped.set(label, bucket);
  }

  return [...grouped.entries()]
    .map(([label, bucket]) => ({
      slug: slugifySegment(label),
      label,
      markets: [...bucket].sort((a, b) => Math.abs(b.edge) - Math.abs(a.edge)),
    }))
    .sort((a, b) => b.markets.length - a.markets.length);
}

export function buildSubcategoryGroups(markets: Market[]) {
  const grouped = new Map<string, Market[]>();

  for (const market of markets) {
    const label = getEffectiveSubcategory(market);
    const bucket = grouped.get(label) ?? [];
    bucket.push(market);
    grouped.set(label, bucket);
  }

  return [...grouped.entries()]
    .map(([label, bucket]) => ({
      slug: slugifySegment(label),
      label,
      markets: [...bucket].sort((a, b) => Math.abs(b.edge) - Math.abs(a.edge)),
    }))
    .sort((a, b) => b.markets.length - a.markets.length);
}

export function buildGameGroups(markets: Market[]) {
  const grouped = new Map<string, Market[]>();

  for (const market of markets) {
    const label = getEffectiveGameLabel(market);
    const bucket = grouped.get(label) ?? [];
    bucket.push(market);
    grouped.set(label, bucket);
  }

  return [...grouped.entries()]
    .map(([label, bucket]) => ({
      slug: slugifySegment(label),
      label,
      markets: [...bucket].sort((a, b) => Math.abs(b.edge) - Math.abs(a.edge)),
    }))
    .sort((a, b) => b.markets.length - a.markets.length);
}

export function getCategoryGroup(markets: Market[], categorySlug: string) {
  return buildCategoryGroups(markets).find((group) => group.slug === categorySlug) ?? null;
}

export function getMarketRoute(categoryLabel: string, marketId: string) {
  return `/markets/${slugifySegment(categoryLabel)}/${encodeURIComponent(marketId)}` as Route;
}

export function getCategoryRoute(categoryLabel: string) {
  return `/markets/${slugifySegment(categoryLabel)}` as Route;
}

export function getCompletedPaperTrades(trades: Trade[]) {
  return trades.filter((trade) => trade.side !== "HOLD" && trade.status === "closed");
}

export function getPortfolioFallback(trades: Trade[]): PortfolioSummary {
  const completedTrades = getCompletedPaperTrades(trades);
  const realizedPnl = completedTrades.reduce((sum, trade) => sum + (trade.profit_loss || 0), 0);
  const startingBankroll = 10000;

  return {
    starting_bankroll: startingBankroll,
    bank_balance: startingBankroll + realizedPnl,
    active_capital: 0,
    realized_pnl: realizedPnl,
    unrealized_pnl: 0,
    total_equity: startingBankroll + realizedPnl,
    completed_trades: completedTrades.length,
    open_positions: 0,
    performance_points: [],
  };
}

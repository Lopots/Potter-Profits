import { notFound } from "next/navigation";

import { MarketDetailShell } from "@/components/market-detail-shell";
import { getDashboardPageData } from "@/lib/api";
import { getCategoryGroup } from "@/lib/market-nav";

export default async function MarketDetailPage({
  params,
}: {
  params: Promise<{ category: string; marketId: string }>;
}) {
  const { category, marketId } = await params;
  const data = await getDashboardPageData();
  const categoryGroup = getCategoryGroup(data.dashboard.markets, category);

  if (!categoryGroup) {
    notFound();
  }

  const market = categoryGroup.markets.find((item) => item.id === decodeURIComponent(marketId));
  if (!market) {
    notFound();
  }

  return <MarketDetailShell data={data} categoryGroup={categoryGroup} market={market} />;
}

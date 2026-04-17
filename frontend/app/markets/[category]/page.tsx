import { notFound } from "next/navigation";

import { CategoryShell } from "@/components/category-shell";
import { getDashboardPageData } from "@/lib/api";
import { getCategoryGroup } from "@/lib/market-nav";

export default async function MarketCategoryPage({ params }: { params: Promise<{ category: string }> }) {
  const { category } = await params;
  const data = await getDashboardPageData();
  const categoryGroup = getCategoryGroup(data.dashboard.markets, category);

  if (!categoryGroup) {
    notFound();
  }

  return <CategoryShell data={data} categoryGroup={categoryGroup} />;
}

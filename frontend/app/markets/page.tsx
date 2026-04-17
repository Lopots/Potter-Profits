import { MarketsShell } from "@/components/markets-shell";
import { getDashboardPageData } from "@/lib/api";

export default async function MarketsPage() {
  const data = await getDashboardPageData();

  return <MarketsShell data={data} />;
}

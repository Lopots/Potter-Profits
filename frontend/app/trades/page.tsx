import { TradesShell } from "@/components/trades-shell";
import { getDashboardPageData } from "@/lib/api";

export default async function TradesPage() {
  const data = await getDashboardPageData();

  return <TradesShell data={data} />;
}

import { DashboardShell } from "@/components/dashboard-shell";
import { getDashboardPageData } from "@/lib/api";

export default async function Home() {
  const data = await getDashboardPageData();

  return <DashboardShell data={data} />;
}

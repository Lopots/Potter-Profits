import { IngestionShell } from "@/components/ingestion-shell";
import { getDashboardPageData } from "@/lib/api";

export default async function IngestionPage() {
  const data = await getDashboardPageData();

  return <IngestionShell data={data} />;
}

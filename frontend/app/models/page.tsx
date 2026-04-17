import { ModelsShell } from "@/components/models-shell";
import { getDashboardPageData } from "@/lib/api";

export default async function ModelsPage() {
  const data = await getDashboardPageData();

  return <ModelsShell data={data} />;
}

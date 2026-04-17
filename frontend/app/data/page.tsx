import { DataShell } from "@/components/data-shell";
import { getDataPageData } from "@/lib/api";

export default async function DataPage() {
  const data = await getDataPageData();

  return <DataShell data={data} />;
}

import { mockSystemStatus } from "./mock-system-status";
import { mockDashboardData } from "./mock-data";
import { DashboardPageData, DashboardResponse, SystemStatus } from "./types";

const API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

export async function getDashboardData(): Promise<DashboardResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/dashboard`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error("Failed to load Potter dashboard");
    }

    return response.json() as Promise<DashboardResponse>;
  } catch {
    return mockDashboardData;
  }
}

export async function getSystemStatus(): Promise<SystemStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/system/status`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error("Failed to load system status");
    }

    return response.json() as Promise<SystemStatus>;
  } catch {
    return mockSystemStatus;
  }
}

export async function getDashboardPageData(): Promise<DashboardPageData> {
  const [dashboard, systemStatus] = await Promise.all([getDashboardData(), getSystemStatus()]);
  return { dashboard, systemStatus };
}

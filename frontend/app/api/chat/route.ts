import { NextRequest, NextResponse } from "next/server";

import { PotterChatRequest, PotterChatResponse } from "@/lib/types";

const API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  const payload = (await request.json()) as PotterChatRequest;

  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error("Failed to chat with Potter");
    }

    const data = (await response.json()) as PotterChatResponse;
    return NextResponse.json(data);
  } catch {
    return NextResponse.json<PotterChatResponse>({
      answer:
        "I could not reach the live Potter backend just now. Ask again in a moment, or reopen the local frontend against the Droplet data source.",
      suggested_prompts: [
        "How does your process work?",
        "What is my paper portfolio doing right now?",
        "What market has the strongest edge right now?",
      ],
      matched_market_ids: [],
    });
  }
}

import { NextRequest } from "next/server";

import { proxyToApi } from "@/lib/bffProxy";

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const date = req.nextUrl.searchParams.get("date") ?? "";
  return proxyToApi(req, `/doctors/${id}/availability?date=${encodeURIComponent(date)}`, "GET");
}

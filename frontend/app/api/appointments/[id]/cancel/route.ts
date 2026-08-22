import { NextRequest } from "next/server";

import { proxyToApi } from "@/lib/bffProxy";

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return proxyToApi(req, `/appointments/${id}/cancel`, "POST");
}

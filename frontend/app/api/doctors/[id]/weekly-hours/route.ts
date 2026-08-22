import { NextRequest } from "next/server";

import { proxyToApi } from "@/lib/bffProxy";

export async function PUT(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return proxyToApi(req, `/doctors/${id}/weekly-hours`, "PUT");
}

import { NextRequest } from "next/server";

import { proxyToApi } from "@/lib/bffProxy";

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return proxyToApi(req, `/doctors/${id}`, "PATCH");
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return proxyToApi(req, `/doctors/${id}`, "DELETE");
}

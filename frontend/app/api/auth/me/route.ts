import { NextRequest } from "next/server";

import { proxyToApi } from "@/lib/bffProxy";

export async function GET(req: NextRequest) {
  return proxyToApi(req, "/auth/me", "GET");
}

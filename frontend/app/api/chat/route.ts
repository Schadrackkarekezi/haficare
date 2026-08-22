import { NextRequest } from "next/server";

import { proxyToApi } from "@/lib/bffProxy";

export async function POST(req: NextRequest) {
  return proxyToApi(req, "/chat", "POST");
}

import { NextRequest } from "next/server";

import { proxyToApi } from "@/lib/bffProxy";

export async function GET(req: NextRequest) {
  return proxyToApi(req, "/doctors", "GET");
}

export async function POST(req: NextRequest) {
  return proxyToApi(req, "/doctors", "POST");
}

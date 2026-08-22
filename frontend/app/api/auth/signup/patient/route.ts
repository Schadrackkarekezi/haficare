import { NextRequest } from "next/server";

import { proxyAuthAndSetCookie } from "@/lib/bffProxy";

export async function POST(req: NextRequest) {
  return proxyAuthAndSetCookie(req, "/auth/signup/patient");
}

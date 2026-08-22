import { NextRequest } from "next/server";

import { proxyToApi } from "@/lib/bffProxy";

// Public list for the patient signup picker -- no auth required.
export async function GET(req: NextRequest) {
  return proxyToApi(req, "/clinics", "GET", false);
}

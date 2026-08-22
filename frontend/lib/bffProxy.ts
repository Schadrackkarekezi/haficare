import { NextRequest, NextResponse } from "next/server";

import { ApiError, apiFetch } from "./apiClient";
import { getServerToken, SESSION_COOKIE } from "./auth";

type TokenResponse = { access_token: string; role: string };

/**
 * Used by login/signup Route Handlers: posts the body to a backend auth
 * endpoint, then stores the returned JWT as an httpOnly, first-party cookie
 * rather than handing it to client-side JS.
 */
export async function proxyAuthAndSetCookie(req: NextRequest, backendPath: string): Promise<NextResponse> {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  }

  try {
    const data = await apiFetch<TokenResponse>(backendPath, { method: "POST", body });
    const res = NextResponse.json({ role: data.role });
    res.cookies.set(SESSION_COOKIE, data.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24,
    });
    return res;
  } catch (err) {
    if (err instanceof ApiError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    return NextResponse.json({ error: "Unexpected error contacting the API" }, { status: 502 });
  }
}

/**
 * Thin proxy from a same-origin Route Handler to the FastAPI backend, attaching
 * the caller's session token as a Bearer header. This is the only way the
 * browser ever reaches the backend -- see the BFF pattern in the project plan.
 */
export async function proxyToApi(
  req: NextRequest,
  path: string,
  method: "GET" | "POST" | "PATCH" | "PUT" | "DELETE" = "GET",
  requireAuth = true
): Promise<NextResponse> {
  const token = await getServerToken();
  if (requireAuth && !token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  let body: unknown;
  if (method !== "GET") {
    try {
      body = await req.json();
    } catch {
      body = undefined;
    }
  }

  try {
    const data = await apiFetch(path, { method, body, token });
    return NextResponse.json(data ?? {});
  } catch (err) {
    if (err instanceof ApiError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    return NextResponse.json({ error: "Unexpected error contacting the API" }, { status: 502 });
  }
}

import { NextRequest, NextResponse } from "next/server";
import { jwtVerify } from "jose";

const SESSION_COOKIE = "haficare_session";

function secretKey(): Uint8Array {
  const secret = process.env.JWT_SECRET_KEY;
  if (!secret) throw new Error("JWT_SECRET_KEY is not set");
  return new TextEncoder().encode(secret);
}

export async function proxy(req: NextRequest) {
  const token = req.cookies.get(SESSION_COOKIE)?.value;
  const loginUrl = new URL("/login", req.url);

  if (!token) {
    return NextResponse.redirect(loginUrl);
  }

  let role: string | undefined;
  try {
    const { payload } = await jwtVerify(token, secretKey());
    role = payload.role as string | undefined;
  } catch {
    // Invalid/expired signature -- treat exactly like "not logged in".
    const res = NextResponse.redirect(loginUrl);
    res.cookies.delete(SESSION_COOKIE);
    return res;
  }

  const { pathname } = req.nextUrl;
  if (pathname.startsWith("/dashboard") && role !== "staff") {
    return NextResponse.redirect(new URL("/app", req.url));
  }
  if (pathname.startsWith("/app") && role !== "patient") {
    return NextResponse.redirect(new URL("/dashboard", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/app/:path*"],
};

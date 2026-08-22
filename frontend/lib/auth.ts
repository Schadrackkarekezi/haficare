import { cookies } from "next/headers";
import { jwtVerify } from "jose";

export const SESSION_COOKIE = "haficare_session";

export type SessionClaims = {
  sub: string;
  clinic_id: number;
  role: "staff" | "patient";
  exp: number;
};

function secretKey(): Uint8Array {
  const secret = process.env.JWT_SECRET_KEY;
  if (!secret) {
    throw new Error("JWT_SECRET_KEY is not set");
  }
  return new TextEncoder().encode(secret);
}

/** Verifies the JWT's signature -- never trust a token without calling this. */
export async function verifyToken(token: string): Promise<SessionClaims | null> {
  try {
    const { payload } = await jwtVerify(token, secretKey());
    return payload as unknown as SessionClaims;
  } catch {
    return null;
  }
}

/** Server Components / Route Handlers only -- reads the httpOnly session cookie. */
export async function getServerToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(SESSION_COOKIE)?.value ?? null;
}

export async function getServerSession(): Promise<SessionClaims | null> {
  const token = await getServerToken();
  if (!token) return null;
  return verifyToken(token);
}

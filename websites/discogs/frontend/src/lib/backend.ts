import { cookies } from "next/headers";

const COOKIE_NAME = "discogs_token";

export function backendUrl(path: string) {
  const base =
    process.env.API_INTERNAL_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
    "http://localhost:12138";
  return `${base}${path.startsWith("/") ? "" : "/"}${path}`;
}

export async function backendFetch(path: string, init?: RequestInit) {
  const token = (await cookies()).get(COOKIE_NAME)?.value;
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (!headers.has("Content-Type") && init?.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);

  return fetch(backendUrl(path), { ...init, headers });
}

export { COOKIE_NAME };


import { API_BASE_URL } from "@/lib/config";

type FetchOptions = RequestInit & { next?: { revalidate?: number } };

export async function apiGet<T>(path: string, opts: FetchOptions = {}): Promise<T> {
  const url = `${API_BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`;
  const res = await fetch(url, {
    ...opts,
    headers: {
      Accept: "application/json",
      ...(opts.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`GET ${path} failed: ${res.status} ${text}`);
  }
  return (await res.json()) as T;
}

export async function apiPost<T>(path: string, body: unknown, opts: FetchOptions = {}): Promise<T> {
  const url = `${API_BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`;
  const res = await fetch(url, {
    method: "POST",
    ...opts,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(opts.headers ?? {}),
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`POST ${path} failed: ${res.status} ${text}`);
  }
  return (await res.json()) as T;
}


export const API_URL =
  process.env.API_INTERNAL_URL?.replace(/\/$/, "") ||
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://localhost:12138";

export type NextFetchOptions = {
  revalidate?: number | false;
  tags?: string[];
};

export async function apiGet<T>(
  path: string,
  opts?: { cache?: RequestCache; next?: NextFetchOptions },
): Promise<T> {
  const url = `${API_URL}${path.startsWith("/") ? "" : "/"}${path}`;
  const res = await fetch(url, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: opts?.cache ?? "no-store",
    next: opts?.next,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`GET ${path} failed: ${res.status} ${text}`);
  }
  return (await res.json()) as T;
}


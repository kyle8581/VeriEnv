export async function serverGet<T>(path: string): Promise<T> {
  const base = process.env.API_BASE_URL || "http://localhost:12127";
  const res = await fetch(`${base}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${res.status} ${res.statusText} for ${path}`);
  }
  return (await res.json()) as T;
}


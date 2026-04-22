export type ApiError = {
  status: number;
  message: string;
};

export async function apiGet<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const body = (await res.json()) as unknown;
      if (
        body &&
        typeof body === "object" &&
        "detail" in body &&
        typeof (body as { detail: unknown }).detail === "string"
      ) {
        msg = (body as { detail: string }).detail;
      }
    } catch {
      // ignore
    }
    const err: ApiError = { status: res.status, message: msg };
    throw err;
  }

  return (await res.json()) as T;
}


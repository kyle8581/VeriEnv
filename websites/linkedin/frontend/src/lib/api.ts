export type ApiError = {
  status: number
  message: string
  details?: unknown
}

export function apiBaseUrl(): string {
  // Prefer a relative API (with Vite proxy in dev).
  return import.meta.env.VITE_API_BASE ?? '/api'
}

function joinUrl(base: string, path: string): string {
  if (!path.startsWith('/')) path = `/${path}`
  return `${base}${path}`
}

export async function apiFetch<T>(
  path: string,
  opts: RequestInit & { accessToken?: string } = {},
): Promise<T> {
  const url = joinUrl(apiBaseUrl(), path)
  const headers = new Headers(opts.headers ?? {})
  if (!headers.has('Content-Type') && opts.body) headers.set('Content-Type', 'application/json')
  if (opts.accessToken) headers.set('Authorization', `Bearer ${opts.accessToken}`)

  const res = await fetch(url, {
    ...opts,
    headers,
  })

  const isJson = (res.headers.get('content-type') ?? '').includes('application/json')
  const body = isJson ? await res.json().catch(() => null) : await res.text().catch(() => '')

  if (!res.ok) {
    const message =
      typeof body === 'object' && body && 'detail' in (body as any)
        ? String((body as any).detail)
        : `Request failed (${res.status})`
    const err: ApiError = { status: res.status, message, details: body }
    throw err
  }

  return body as T
}


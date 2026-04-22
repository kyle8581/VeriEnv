// Use relative path for client-side (Next.js rewrites to backend)
// Use env var or localhost for server-side rendering
export const API_BASE_URL =
  typeof window !== "undefined"
    ? "" // Client-side: use relative path, Next.js rewrites /api/* to backend
    : process.env.NEXT_PUBLIC_API_BASE_URL ?? "";


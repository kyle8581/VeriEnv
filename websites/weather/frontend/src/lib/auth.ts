export type TokenPair = {
  access_token: string;
  refresh_token: string;
  access_expires_at: string;
  refresh_expires_at: string;
  token_type: string;
};

const KEY = "weather_portal_tokens_v1";

export function saveTokens(tokens: TokenPair) {
  localStorage.setItem(KEY, JSON.stringify(tokens));
}

export function loadTokens(): TokenPair | null {
  const raw = localStorage.getItem(KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as TokenPair;
  } catch {
    return null;
  }
}

export function clearTokens() {
  localStorage.removeItem(KEY);
}


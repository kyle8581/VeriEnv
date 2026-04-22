import { API_BASE_URL } from "@/lib/config";
import type {
  Listing,
  ListingSearchResponse,
  Location,
  Token,
  UserPublic,
} from "@/lib/types";

async function apiFetch<T>(
  path: string,
  init: RequestInit & { token?: string } = {},
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (init.token) {
    headers.set("Authorization", `Bearer ${init.token}`);
  }
  const res = await fetch(url, { ...init, headers, cache: "no-store" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export function searchListings(params: {
  q: string;
  min_price?: number;
  max_price?: number;
  min_beds?: number;
  max_beds?: number;
  property_type?: string;
  move_in_date?: string;
  has_videos?: boolean;
  has_virtual_tour?: boolean;
  specials_only?: boolean;
  amenity?: string;
  sort?: string;
  offset?: number;
  limit?: number;
}): Promise<ListingSearchResponse> {
  const usp = new URLSearchParams();
  usp.set("q", params.q);
  if (params.min_price != null) usp.set("min_price", String(params.min_price));
  if (params.max_price != null) usp.set("max_price", String(params.max_price));
  if (params.min_beds != null) usp.set("min_beds", String(params.min_beds));
  if (params.max_beds != null) usp.set("max_beds", String(params.max_beds));
  if (params.property_type) usp.set("property_type", params.property_type);
  if (params.move_in_date) usp.set("move_in_date", params.move_in_date);
  if (params.has_videos) usp.set("has_videos", "true");
  if (params.has_virtual_tour) usp.set("has_virtual_tour", "true");
  if (params.specials_only) usp.set("specials_only", "true");
  if (params.amenity) usp.set("amenity", params.amenity);
  if (params.sort) usp.set("sort", params.sort);
  if (params.offset != null) usp.set("offset", String(params.offset));
  if (params.limit != null) usp.set("limit", String(params.limit));
  return apiFetch(`/api/listings?${usp.toString()}`);
}

export function getListing(listingId: number): Promise<Listing> {
  return apiFetch(`/api/listings/${listingId}`);
}

export function searchLocations(query: string): Promise<Location[]> {
  const usp = new URLSearchParams();
  usp.set("query", query);
  return apiFetch(`/api/locations?${usp.toString()}`);
}

export function register(payload: {
  email: string;
  password: string;
  full_name?: string | null;
}): Promise<UserPublic> {
  return apiFetch(`/api/auth/register`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function login(email: string, password: string): Promise<Token> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  return apiFetch(`/api/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
}

export function me(token: string): Promise<UserPublic> {
  return apiFetch(`/api/auth/me`, { token });
}

export function listFavorites(token: string): Promise<Listing[]> {
  return apiFetch(`/api/favorites`, { token });
}

export function addFavorite(token: string, listingId: number): Promise<void> {
  return apiFetch(`/api/favorites/${listingId}`, { method: "POST", token });
}

export function removeFavorite(token: string, listingId: number): Promise<void> {
  return apiFetch(`/api/favorites/${listingId}`, { method: "DELETE", token });
}

export function createContactRequest(payload: {
  listing_id: number;
  contact_email: string;
  contact_name?: string | null;
  message: string;
  token?: string;
}): Promise<void> {
  const { token, ...body } = payload;
  return apiFetch(`/api/contact-requests`, {
    method: "POST",
    body: JSON.stringify(body),
    token,
  });
}

export function createSavedSearch(payload: {
  name: string;
  query: string;
  filters: Record<string, unknown>;
  token: string;
}): Promise<void> {
  return apiFetch(`/api/saved-searches`, {
    method: "POST",
    body: JSON.stringify({
      name: payload.name,
      query: payload.query,
      filters: payload.filters,
    }),
    token: payload.token,
  });
}


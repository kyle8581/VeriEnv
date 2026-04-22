from __future__ import annotations

from typing import Any, Literal

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from apartments_sdk.errors import APIError, AuthError
from apartments_sdk.models import (
    ContactRequestPublic,
    ListingPublic,
    ListingSearchResponse,
    LocationPublic,
    SavedSearchPublic,
    Token,
    UserPublic,
)


class ApartmentsClient:
    """
    Minimal, production-usable Python SDK for the Apartments clone API.

    - Handles auth via `login()` and stores a bearer token in-memory
    - Provides typed responses via Pydantic models
    """

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float = 15.0,
        token: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ApartmentsClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def set_token(self, token: str | None) -> None:
        self._token = token

    def get_token(self) -> str | None:
        return self._token

    def _auth_headers(self) -> dict[str, str]:
        if not self._token:
            raise AuthError("No token set; call login() first (or pass token=...).")
        return {"Authorization": f"Bearer {self._token}"}

    @retry(wait=wait_exponential(min=0.2, max=2), stop=stop_after_attempt(3))
    def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
    ) -> httpx.Response:
        res = self._client.request(method, path, headers=headers, params=params, json=json, data=data)
        if res.status_code >= 400:
            raise APIError(res.status_code, res.text)
        return res

    # ---- Auth ----
    def register(self, *, email: str, password: str, full_name: str | None = None) -> UserPublic:
        res = self._request(
            "POST",
            "/api/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )
        return UserPublic.model_validate(res.json())

    def login(self, *, email: str, password: str) -> Token:
        res = self._request(
            "POST",
            "/api/auth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"username": email, "password": password},
        )
        tok = Token.model_validate(res.json())
        self._token = tok.access_token
        return tok

    def me(self) -> UserPublic:
        res = self._request("GET", "/api/auth/me", headers=self._auth_headers())
        return UserPublic.model_validate(res.json())

    # ---- Listings ----
    def search_listings(
        self,
        *,
        q: str,
        min_price: int | None = None,
        max_price: int | None = None,
        min_beds: int | None = None,
        max_beds: int | None = None,
        property_type: str | None = None,
        move_in_date: str | None = None,
        has_videos: bool | None = None,
        has_virtual_tour: bool | None = None,
        specials_only: bool | None = None,
        amenity: str | None = None,
        sort: Literal["newest", "price_asc", "price_desc"] = "newest",
        offset: int = 0,
        limit: int = 25,
    ) -> ListingSearchResponse:
        params: dict[str, Any] = {"q": q, "offset": offset, "limit": limit, "sort": sort}
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if min_beds is not None:
            params["min_beds"] = min_beds
        if max_beds is not None:
            params["max_beds"] = max_beds
        if property_type:
            params["property_type"] = property_type
        if move_in_date:
            params["move_in_date"] = move_in_date
        if has_videos:
            params["has_videos"] = "true"
        if has_virtual_tour:
            params["has_virtual_tour"] = "true"
        if specials_only:
            params["specials_only"] = "true"
        if amenity:
            params["amenity"] = amenity

        res = self._request("GET", "/api/listings", params=params)
        return ListingSearchResponse.model_validate(res.json())

    def get_listing(self, listing_id: int) -> ListingPublic:
        res = self._request("GET", f"/api/listings/{listing_id}")
        return ListingPublic.model_validate(res.json())

    # ---- Favorites ----
    def list_favorites(self) -> list[ListingPublic]:
        res = self._request("GET", "/api/favorites", headers=self._auth_headers())
        return [ListingPublic.model_validate(x) for x in res.json()]

    def add_favorite(self, listing_id: int) -> None:
        self._request("POST", f"/api/favorites/{listing_id}", headers=self._auth_headers())

    def remove_favorite(self, listing_id: int) -> None:
        self._request("DELETE", f"/api/favorites/{listing_id}", headers=self._auth_headers())

    # ---- Saved searches ----
    def list_saved_searches(self) -> list[SavedSearchPublic]:
        res = self._request("GET", "/api/saved-searches", headers=self._auth_headers())
        return [SavedSearchPublic.model_validate(x) for x in res.json()]

    def create_saved_search(self, *, name: str, query: str, filters: dict[str, Any]) -> SavedSearchPublic:
        res = self._request(
            "POST",
            "/api/saved-searches",
            headers=self._auth_headers(),
            json={"name": name, "query": query, "filters": filters},
        )
        return SavedSearchPublic.model_validate(res.json())

    def delete_saved_search(self, saved_search_id: int) -> None:
        self._request("DELETE", f"/api/saved-searches/{saved_search_id}", headers=self._auth_headers())

    # ---- Contact requests (Email CTA) ----
    def create_contact_request(
        self,
        *,
        listing_id: int,
        contact_email: str,
        message: str,
        contact_name: str | None = None,
        authenticated: bool = True,
    ) -> ContactRequestPublic:
        headers = self._auth_headers() if authenticated else None
        res = self._request(
            "POST",
            "/api/contact-requests",
            headers=headers,
            json={
                "listing_id": listing_id,
                "contact_email": contact_email,
                "contact_name": contact_name,
                "message": message,
            },
        )
        return ContactRequestPublic.model_validate(res.json())

    # ---- Locations ----
    def search_locations(self, query: str, *, limit: int = 10) -> list[LocationPublic]:
        res = self._request("GET", "/api/locations", params={"query": query, "limit": limit})
        return [LocationPublic.model_validate(x) for x in res.json()]


from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


class DiscogsSdkError(RuntimeError):
    pass


@dataclass
class DiscogsClient:
    """
    Minimal, production-friendly Python client for the Discogs clone API.

    Default base URL targets the web app's proxy:
      http://localhost:12042/api/backend
    """

    base_url: str = "http://localhost:12042/api/backend"
    timeout: float = 30.0
    token: str | None = None

    def _client(self) -> httpx.Client:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return httpx.Client(base_url=self.base_url.rstrip("/"), headers=headers, timeout=self.timeout)

    def _request(self, method: str, path: str, json: Any | None = None, params: Dict[str, Any] | None = None) -> Any:
        with self._client() as c:
            r = c.request(method, path if path.startswith("/") else f"/{path}", json=json, params=params)
        if r.status_code >= 400:
            raise DiscogsSdkError(f"{method} {path} failed: {r.status_code} {r.text}")
        if not r.text:
            return None
        return r.json()

    # -----------------------
    # Auth
    # -----------------------
    def register(self, username: str, email: str, password: str, display_name: str | None = None) -> dict:
        return self._request(
            "POST",
            "/auth/register",
            json={"username": username, "email": email, "password": password, "display_name": display_name},
        )

    def login(self, username_or_email: str, password: str) -> str:
        data = self._request("POST", "/auth/login", json={"username_or_email": username_or_email, "password": password})
        token = data["access_token"]
        self.token = token
        return token

    def me(self) -> dict:
        return self._request("GET", "/auth/me")

    # -----------------------
    # Public catalog
    # -----------------------
    def home(self) -> dict:
        return self._request("GET", "/home")

    def genres(self) -> list[dict]:
        return self._request("GET", "/genres")

    def genre_overview(self, slug: str) -> dict:
        return self._request("GET", f"/genres/{slug}/overview")

    def release(self, release_id: int) -> dict:
        return self._request("GET", f"/releases/{release_id}")

    def listings(
        self,
        release_id: int,
        *,
        media_condition: str | None = None,
        sleeve_condition: str | None = None,
        ships_from: str | None = None,
        min_rating: float | None = None,
        sort: str = "price_asc",
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        params: dict[str, Any] = {"sort": sort, "limit": limit, "offset": offset}
        if media_condition:
            params["media_condition"] = media_condition
        if sleeve_condition:
            params["sleeve_condition"] = sleeve_condition
        if ships_from:
            params["ships_from"] = ships_from
        if min_rating is not None:
            params["min_rating"] = min_rating
        return self._request("GET", f"/releases/{release_id}/listings", params=params)

    def search(self, q: str) -> list[dict]:
        return self._request("GET", "/search", params={"q": q})

    # -----------------------
    # Account / marketplace flows (auth required)
    # -----------------------
    def collection(self) -> list[dict]:
        return self._request("GET", "/me/collection")

    def add_to_collection(self, release_id: int) -> dict:
        return self._request("POST", f"/me/collection/{release_id}")

    def wantlist(self) -> list[dict]:
        return self._request("GET", "/me/wantlist")

    def add_to_wantlist(self, release_id: int) -> dict:
        return self._request("POST", f"/me/wantlist/{release_id}")

    def cart(self) -> dict:
        return self._request("GET", "/cart")

    def cart_add(self, listing_id: int, quantity: int = 1) -> dict:
        return self._request("POST", "/cart/items", json={"listing_id": listing_id, "quantity": quantity})

    def cart_remove(self, cart_item_id: int) -> dict:
        return self._request("DELETE", f"/cart/items/{cart_item_id}")

    def checkout(self) -> dict:
        return self._request("POST", "/checkout")


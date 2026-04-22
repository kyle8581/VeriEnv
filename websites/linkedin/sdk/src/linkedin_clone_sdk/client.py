from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import httpx

from .errors import ApiError


TokenType = Literal["bearer"]


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: TokenType = "bearer"


class LinkedInCloneClient:
    """
    Minimal, production-usable API client for the LinkedIn clone backend.

    - Manages auth tokens (login/register/refresh/logout)
    - Adds Authorization headers automatically
    - Retries once on 401 by refreshing (if refresh_token exists)
    """

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:12079",
        api_prefix: str = "/api",
        timeout: float = 20.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_prefix = api_prefix if api_prefix.startswith("/") else f"/{api_prefix}"
        self.timeout = timeout
        self._client = client or httpx.Client(timeout=timeout)
        self.tokens: TokenPair | None = None

    def close(self) -> None:
        self._client.close()

    @property
    def api_base(self) -> str:
        return f"{self.base_url}{self.api_prefix}"

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Accept": "application/json"}
        if self.tokens:
            h["Authorization"] = f"Bearer {self.tokens.access_token}"
        return h

    def _request(self, method: str, path: str, *, json: Any | None = None, params: dict[str, Any] | None = None) -> Any:
        if not path.startswith("/"):
            path = f"/{path}"
        url = f"{self.api_base}{path}"

        def do() -> httpx.Response:
            return self._client.request(method, url, headers=self._headers(), json=json, params=params)

        res = do()
        if res.status_code == 401 and self.tokens and path not in ("/auth/refresh", "/auth/login", "/auth/register"):
            # Retry once after refresh.
            self.refresh()
            res = do()

        if res.status_code >= 400:
            details: Any = None
            message = f"Request failed ({res.status_code})"
            try:
                details = res.json()
                if isinstance(details, dict) and "detail" in details:
                    message = str(details["detail"])
            except Exception:
                details = res.text
            raise ApiError(status_code=res.status_code, message=message, details=details)

        if res.headers.get("content-type", "").startswith("application/json"):
            return res.json()
        return res.text

    # ---- Auth ----
    def register(self, *, email: str, password: str, first_name: str, last_name: str) -> TokenPair:
        data = self._request(
            "POST",
            "/auth/register",
            json={"email": email, "password": password, "first_name": first_name, "last_name": last_name},
        )
        self.tokens = TokenPair(**data)
        return self.tokens

    def login(self, email: str, password: str) -> TokenPair:
        data = self._request("POST", "/auth/login", json={"email": email, "password": password})
        self.tokens = TokenPair(**data)
        return self.tokens

    def refresh(self) -> TokenPair:
        if not self.tokens:
            raise ValueError("No tokens available; call login() first.")
        data = self._request("POST", "/auth/refresh", json={"refresh_token": self.tokens.refresh_token})
        self.tokens = TokenPair(**data)
        return self.tokens

    def logout(self) -> dict[str, Any]:
        if not self.tokens:
            return {"ok": True}
        out = self._request("POST", "/auth/logout", json={"refresh_token": self.tokens.refresh_token})
        self.tokens = None
        return out

    def me(self) -> dict[str, Any]:
        return self._request("GET", "/auth/me")

    # ---- Feed ----
    def feed(self, *, limit: int = 10, cursor: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return self._request("GET", "/feed", params=params)

    def create_post(self, *, body: str, image_url: str = "") -> dict[str, Any]:
        return self._request("POST", "/feed/posts", json={"body": body, "image_url": image_url})

    def toggle_like(self, post_id: str) -> dict[str, Any]:
        return self._request("POST", f"/feed/posts/{post_id}/like")

    def list_comments(self, post_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/feed/posts/{post_id}/comments")

    def add_comment(self, post_id: str, *, body: str) -> dict[str, Any]:
        return self._request("POST", f"/feed/posts/{post_id}/comments", json={"body": body})

    # ---- Search ----
    def typeahead(self, q: str) -> dict[str, Any]:
        return self._request("GET", "/search/typeahead", params={"q": q})

    def search_people(self, q: str, *, limit: int = 10) -> dict[str, Any]:
        return self._request("GET", "/search/people", params={"q": q, "limit": limit})

    def search_posts(self, q: str, *, limit: int = 10) -> dict[str, Any]:
        return self._request("GET", "/search/posts", params={"q": q, "limit": limit})

    # ---- Jobs ----
    def search_jobs(
        self,
        *,
        query: str = "",
        location: str = "",
        work_mode: list[str] | None = None,
        employment_type: list[str] | None = None,
        experience_level: list[str] | None = None,
        date_posted_days: int | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"query": query, "location": location, "limit": limit, "offset": offset}
        if work_mode:
            params["work_mode"] = work_mode
        if employment_type:
            params["employment_type"] = employment_type
        if experience_level:
            params["experience_level"] = experience_level
        if date_posted_days is not None:
            params["date_posted_days"] = date_posted_days
        return self._request("GET", "/jobs/search", params=params)

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/jobs/{job_id}")

    def save_job(self, job_id: str) -> dict[str, Any]:
        return self._request("POST", f"/jobs/{job_id}/save")

    def unsave_job(self, job_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/jobs/{job_id}/save")

    def apply_job(self, job_id: str) -> dict[str, Any]:
        return self._request("POST", f"/jobs/{job_id}/apply")

    def list_job_alerts(self) -> list[dict[str, Any]]:
        return self._request("GET", "/jobs/alerts/me")

    def toggle_job_alert(self, *, query: str = "", location: str = "", enabled: bool = True) -> dict[str, Any]:
        return self._request("POST", "/jobs/alerts/toggle", params={"query": query, "location": location, "enabled": enabled})


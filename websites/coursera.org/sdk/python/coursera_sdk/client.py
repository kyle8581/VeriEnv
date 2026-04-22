from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


@dataclass
class CourseraClient:
    base_url: str = "http://127.0.0.1:12038"
    token: str | None = None
    token_store_path: str | None = None
    timeout: float = 30.0

    def __post_init__(self) -> None:
        if self.token is None and self.token_store_path:
            self._load_token()

    # -----------------------
    # Auth
    # -----------------------
    def register(self, *, email: str, full_name: str, password: str) -> dict[str, Any]:
        return self._post_json(
            "/api/auth/register",
            {"email": email, "full_name": full_name, "password": password},
        )

    def login(self, *, email: str, password: str) -> str:
        # OAuth2PasswordRequestForm
        res = self._post_form("/api/auth/login", {"username": email, "password": password})
        token = res["access_token"]
        self.token = token
        self._save_token()
        return token

    def me(self) -> dict[str, Any]:
        return self._get("/api/auth/me")

    # -----------------------
    # Catalog
    # -----------------------
    def list_partners(self) -> list[dict[str, Any]]:
        return self._get("/api/partners")

    def list_institutions(self) -> list[dict[str, Any]]:
        return self._get("/api/institutions")

    def list_courses(
        self,
        *,
        q: str | None = None,
        partner: str | None = None,
        level: str | None = None,
        limit: int = 24,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if q:
            params["q"] = q
        if partner:
            params["partner"] = partner
        if level:
            params["level"] = level
        return self._get("/api/courses", params=params)

    def get_course(self, slug: str) -> dict[str, Any]:
        return self._get(f"/api/courses/{slug}")

    def list_resources(self, *, kind: str | None = None, limit: int = 24, offset: int = 0) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if kind:
            params["kind"] = kind
        return self._get("/api/resources", params=params)

    def get_resource(self, slug: str) -> dict[str, Any]:
        return self._get(f"/api/resources/{slug}")

    # -----------------------
    # Leads
    # -----------------------
    def submit_ebook_lead(self, **payload: Any) -> dict[str, Any]:
        return self._post_json("/api/leads/ebook", payload)

    def submit_contact_lead(self, **payload: Any) -> dict[str, Any]:
        return self._post_json("/api/leads/contact", payload)

    # -----------------------
    # HTTP helpers
    # -----------------------
    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout, headers=self._headers()) as client:
            r = client.get(path, params=params)
            self._raise_for_status(r, path)
            return r.json()

    def _post_json(self, path: str, json_body: dict[str, Any]) -> Any:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout, headers=self._headers()) as client:
            r = client.post(path, json=json_body)
            self._raise_for_status(r, path)
            return r.json()

    def _post_form(self, path: str, data: dict[str, Any]) -> Any:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout, headers=self._headers()) as client:
            r = client.post(path, data=data, headers={**client.headers, "Content-Type": "application/x-www-form-urlencoded"})
            self._raise_for_status(r, path)
            return r.json()

    @staticmethod
    def _raise_for_status(r: httpx.Response, path: str) -> None:
        if 200 <= r.status_code < 300:
            return
        body = r.text
        raise RuntimeError(f"Request failed {r.status_code} for {path}: {body}")

    # -----------------------
    # Token storage
    # -----------------------
    def _save_token(self) -> None:
        if not self.token_store_path:
            return
        Path(self.token_store_path).write_text(json.dumps({"access_token": self.token}, indent=2), encoding="utf-8")

    def _load_token(self) -> None:
        p = Path(self.token_store_path or "")
        if not p.exists():
            return
        data = json.loads(p.read_text(encoding="utf-8"))
        self.token = data.get("access_token")


from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional

import httpx
from pydantic import BaseModel, Field


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    access_expires_at: str | None = None
    refresh_expires_at: str | None = None
    token_type: str = "bearer"


class WeatherPortalError(Exception):
    pass


class ApiError(WeatherPortalError):
    def __init__(self, status_code: int, detail: str):
        super().__init__(f"{status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


class Category(BaseModel):
    name: str
    slug: str


class Article(BaseModel):
    title: str
    slug: str
    summary: str
    hero_image_url: str
    is_video: bool
    source: str
    reading_minutes: int
    published_at: str
    category: Category


class ArticleDetail(Article):
    body_md: str


class Photo(BaseModel):
    id: str
    title: str
    image_url: str
    caption: str | None = None
    published_at: str


class Deal(BaseModel):
    id: str
    title: str
    image_url: str
    provider: str
    price_usd: float | None = None
    badge: str | None = None
    cta_url: str


class Location(BaseModel):
    name: str
    state: str | None = None
    country: str
    zip_code: str | None = None
    latitude: float
    longitude: float
    timezone: str
    slug: str


class Me(BaseModel):
    id: str
    email: str
    name: str | None = None
    is_active: bool
    is_admin: bool


class CurrentWeather(BaseModel):
    observed_at: str | None = None
    temperature_c: float | None = None
    apparent_temperature_c: float | None = None
    humidity_percent: float | None = None
    wind_speed_kmh: float | None = None
    wind_direction_deg: float | None = None
    weather: dict


class HourlyPoint(BaseModel):
    time: str
    temperature_c: float | None = None
    precipitation_probability: float | None = None
    wind_speed_kmh: float | None = None
    weather: dict


class DailyPoint(BaseModel):
    date: str
    temp_max_c: float | None = None
    temp_min_c: float | None = None
    sunrise: str | None = None
    sunset: str | None = None
    uv_index_max: float | None = None
    weather: dict


class Plan(BaseModel):
    id: str
    name: str
    price_monthly_usd: float
    description: str
    features: list[str] = Field(default_factory=list)


class Subscription(BaseModel):
    id: str
    status: str
    started_at: str
    ends_at: str | None = None
    plan: Plan


class WeatherPortalClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._tokens: TokenPair | None = None
        self._http = httpx.Client(timeout=30.0)

    def __enter__(self) -> "WeatherPortalClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def _headers(self) -> dict[str, str]:
        if not self._tokens:
            return {}
        return {"Authorization": f"Bearer {self._tokens.access_token}"}

    def _request(
        self,
        method: str,
        path: str,
        *,
        auth: bool = False,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        headers = self._headers() if auth else {}
        r = self._http.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            json=json,
            params=params,
        )
        if r.status_code >= 400:
            detail = ""
            try:
                body = r.json()
                if isinstance(body, dict) and "detail" in body:
                    detail = str(body["detail"])
                else:
                    detail = r.text
            except Exception:
                detail = r.text
            raise ApiError(r.status_code, detail or r.reason_phrase)
        return r.json() if r.content else None

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    # --- Auth ---
    def register(self, *, email: str, password: str, name: str | None = None) -> TokenPair:
        data = self._request(
            "POST",
            "/auth/register",
            json={"email": email, "password": password, "name": name},
        )
        self._tokens = TokenPair(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            access_expires_at=data.get("access_expires_at"),
            refresh_expires_at=data.get("refresh_expires_at"),
            token_type=data.get("token_type", "bearer"),
        )
        return self._tokens

    def login(self, *, email: str, password: str) -> TokenPair:
        data = self._request("POST", "/auth/login", json={"email": email, "password": password})
        self._tokens = TokenPair(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            access_expires_at=data.get("access_expires_at"),
            refresh_expires_at=data.get("refresh_expires_at"),
            token_type=data.get("token_type", "bearer"),
        )
        return self._tokens

    def refresh(self) -> TokenPair:
        if not self._tokens:
            raise WeatherPortalError("Not logged in")
        data = self._request("POST", "/auth/refresh", json={"refresh_token": self._tokens.refresh_token})
        self._tokens = TokenPair(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            access_expires_at=data.get("access_expires_at"),
            refresh_expires_at=data.get("refresh_expires_at"),
            token_type=data.get("token_type", "bearer"),
        )
        return self._tokens

    def logout(self) -> None:
        if not self._tokens:
            return
        self._request("POST", "/auth/logout", json={"refresh_token": self._tokens.refresh_token})
        self._tokens = None

    # --- Me ---
    def me(self) -> Me:
        data = self._request("GET", "/me", auth=True)
        return Me.model_validate(data)

    # --- Content ---
    def list_categories(self) -> list[Category]:
        data = self._request("GET", "/content/categories")
        return [Category.model_validate(x) for x in data]

    def list_articles(
        self,
        *,
        category: str | None = None,
        kind: Literal["all", "video"] = "all",
        limit: int = 24,
        offset: int = 0,
    ) -> list[Article]:
        params: dict[str, Any] = {"kind": kind, "limit": limit, "offset": offset}
        if category:
            params["category"] = category
        data = self._request("GET", "/content/articles", params=params)
        return [Article.model_validate(x) for x in data]

    def get_article(self, slug: str) -> ArticleDetail:
        data = self._request("GET", f"/content/articles/{slug}")
        return ArticleDetail.model_validate(data)

    def list_photos(self, *, limit: int = 24, offset: int = 0) -> list[Photo]:
        data = self._request("GET", "/content/photos", params={"limit": limit, "offset": offset})
        return [Photo.model_validate(x) for x in data]

    def list_deals(self, *, limit: int = 24, offset: int = 0) -> list[Deal]:
        data = self._request("GET", "/content/deals", params={"limit": limit, "offset": offset})
        return [Deal.model_validate(x) for x in data]

    # --- Locations ---
    def search_locations(self, q: str, *, limit: int = 10) -> list[Location]:
        data = self._request("GET", "/locations/search", params={"q": q, "limit": limit})
        return [Location.model_validate(x) for x in data]

    def get_location(self, slug: str) -> Location:
        data = self._request("GET", f"/locations/{slug}")
        return Location.model_validate(data)

    # --- Saved locations (auth) ---
    def list_saved_locations(self) -> list[Location]:
        data = self._request("GET", "/me/locations", auth=True)
        return [Location.model_validate(x) for x in data]

    def save_location(self, slug: str) -> Location:
        data = self._request("POST", "/me/locations", auth=True, json={"location_slug": slug})
        return Location.model_validate(data)

    def remove_saved_location(self, slug: str) -> None:
        self._request("DELETE", f"/me/locations/{slug}", auth=True)

    # --- Weather ---
    def current(self, slug: str) -> CurrentWeather:
        data = self._request("GET", f"/weather/{slug}/current")
        return CurrentWeather.model_validate(data)

    def hourly(self, slug: str) -> list[HourlyPoint]:
        data = self._request("GET", f"/weather/{slug}/hourly")
        return [HourlyPoint.model_validate(x) for x in data]

    def daily(self, slug: str) -> list[DailyPoint]:
        data = self._request("GET", f"/weather/{slug}/daily")
        return [DailyPoint.model_validate(x) for x in data]

    # --- Subscription ---
    def list_plans(self) -> list[Plan]:
        data = self._request("GET", "/subscriptions/plans")
        return [Plan.model_validate(x) for x in data]

    def get_subscription(self) -> Optional[Subscription]:
        data = self._request("GET", "/me/subscription", auth=True)
        if data is None:
            return None
        return Subscription.model_validate(data)

    def subscribe(self, plan_id: str) -> Subscription:
        data = self._request("POST", "/me/subscription/subscribe", auth=True, json={"plan_id": plan_id})
        return Subscription.model_validate(data)

    def cancel_subscription(self) -> None:
        self._request("POST", "/me/subscription/cancel", auth=True)


from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
def fetch_forecast(*, latitude: float, longitude: float, timezone: str) -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone or "auto",
        "current": ",".join(
            [
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m",
            ]
        ),
        "hourly": ",".join(
            [
                "temperature_2m",
                "weather_code",
                "precipitation_probability",
                "wind_speed_10m",
            ]
        ),
        "daily": ",".join(
            [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "sunrise",
                "sunset",
                "uv_index_max",
            ]
        ),
        "forecast_days": 10,
    }
    with httpx.Client(timeout=20.0) as client:
        r = client.get(f"{settings.OPEN_METEO_BASE_URL}/forecast", params=params)
        r.raise_for_status()
        return r.json()


WEATHER_CODE_MAP: dict[int, tuple[str, str]] = {
    0: ("Clear", "clear"),
    1: ("Mostly Clear", "mostly_clear"),
    2: ("Partly Cloudy", "partly_cloudy"),
    3: ("Cloudy", "cloudy"),
    45: ("Fog", "fog"),
    48: ("Depositing Rime Fog", "fog"),
    51: ("Light Drizzle", "drizzle"),
    53: ("Drizzle", "drizzle"),
    55: ("Heavy Drizzle", "drizzle"),
    61: ("Light Rain", "rain"),
    63: ("Rain", "rain"),
    65: ("Heavy Rain", "rain"),
    71: ("Light Snow", "snow"),
    73: ("Snow", "snow"),
    75: ("Heavy Snow", "snow"),
    80: ("Rain Showers", "showers"),
    81: ("Rain Showers", "showers"),
    82: ("Heavy Showers", "showers"),
    95: ("Thunderstorm", "tstorm"),
    96: ("Thunderstorm + Hail", "tstorm"),
    99: ("Thunderstorm + Hail", "tstorm"),
}


def describe_weather(code: int | None) -> dict[str, Any]:
    if code is None:
        return {"code": None, "label": "Unknown", "icon": "unknown"}
    label, icon = WEATHER_CODE_MAP.get(code, ("Unknown", "unknown"))
    return {"code": code, "label": label, "icon": icon}


def cache_expiry_for_kind(kind: str) -> datetime:
    # Naive timestamps (UTC-like) for sqlite simplicity
    now = datetime.now()
    if kind == "current":
        return now + timedelta(minutes=5)
    if kind == "hourly":
        return now + timedelta(minutes=15)
    if kind == "daily":
        return now + timedelta(minutes=60)
    return now + timedelta(minutes=10)


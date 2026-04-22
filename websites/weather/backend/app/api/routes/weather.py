from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.location import Location
from app.models.weather_cache import WeatherCache
from app.services.open_meteo import cache_expiry_for_kind, describe_weather, fetch_forecast


router = APIRouter(prefix="/weather", tags=["weather"])


def _now() -> datetime:
    return datetime.now()


def _get_location(session: Session, slug: str) -> Location:
    loc = session.exec(select(Location).where(Location.slug == slug)).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc


def _get_cached(session: Session, location_id, kind: str) -> dict[str, Any] | None:
    row = session.exec(
        select(WeatherCache)
        .where((WeatherCache.location_id == location_id) & (WeatherCache.kind == kind))
        .order_by(WeatherCache.fetched_at.desc())
    ).first()
    if not row:
        return None
    if row.expires_at <= _now():
        return None
    return row.payload


def _set_cached(session: Session, location_id, kind: str, payload: dict[str, Any]) -> None:
    session.add(
        WeatherCache(
            location_id=location_id,
            kind=kind,
            fetched_at=_now(),
            expires_at=cache_expiry_for_kind(kind),
            payload=payload,
        )
    )
    session.commit()


class CurrentOut(BaseModel):
    observed_at: str | None
    temperature_c: float | None
    apparent_temperature_c: float | None
    humidity_percent: float | None
    wind_speed_kmh: float | None
    wind_direction_deg: float | None
    weather: dict


@router.get("/{slug}/current", response_model=CurrentOut)
def current(slug: str, session: Session = Depends(get_session)):
    loc = _get_location(session, slug)
    cached = _get_cached(session, loc.id, "current")
    if cached:
        return cached

    data = fetch_forecast(latitude=loc.latitude, longitude=loc.longitude, timezone=loc.timezone)
    cur = data.get("current") or {}
    out = CurrentOut(
        observed_at=cur.get("time"),
        temperature_c=cur.get("temperature_2m"),
        apparent_temperature_c=cur.get("apparent_temperature"),
        humidity_percent=cur.get("relative_humidity_2m"),
        wind_speed_kmh=cur.get("wind_speed_10m"),
        wind_direction_deg=cur.get("wind_direction_10m"),
        weather=describe_weather(cur.get("weather_code")),
    ).model_dump()
    _set_cached(session, loc.id, "current", out)
    return out


class HourlyPoint(BaseModel):
    time: str
    temperature_c: float | None
    precipitation_probability: float | None
    wind_speed_kmh: float | None
    weather: dict


@router.get("/{slug}/hourly", response_model=list[HourlyPoint])
def hourly(slug: str, session: Session = Depends(get_session)):
    loc = _get_location(session, slug)
    cached = _get_cached(session, loc.id, "hourly")
    if cached:
        return cached

    data = fetch_forecast(latitude=loc.latitude, longitude=loc.longitude, timezone=loc.timezone)
    h = data.get("hourly") or {}
    times = h.get("time") or []
    temps = h.get("temperature_2m") or []
    codes = h.get("weather_code") or []
    pops = h.get("precipitation_probability") or []
    winds = h.get("wind_speed_10m") or []

    points: list[dict[str, Any]] = []
    for i in range(min(len(times), 48)):
        points.append(
            HourlyPoint(
                time=times[i],
                temperature_c=temps[i] if i < len(temps) else None,
                precipitation_probability=pops[i] if i < len(pops) else None,
                wind_speed_kmh=winds[i] if i < len(winds) else None,
                weather=describe_weather(codes[i] if i < len(codes) else None),
            ).model_dump()
        )

    _set_cached(session, loc.id, "hourly", points)
    return points


class DailyPoint(BaseModel):
    date: str
    temp_max_c: float | None
    temp_min_c: float | None
    sunrise: str | None
    sunset: str | None
    uv_index_max: float | None
    weather: dict


@router.get("/{slug}/daily", response_model=list[DailyPoint])
def daily(slug: str, session: Session = Depends(get_session)):
    loc = _get_location(session, slug)
    cached = _get_cached(session, loc.id, "daily")
    if cached:
        return cached

    data = fetch_forecast(latitude=loc.latitude, longitude=loc.longitude, timezone=loc.timezone)
    d = data.get("daily") or {}
    dates = d.get("time") or []
    tmax = d.get("temperature_2m_max") or []
    tmin = d.get("temperature_2m_min") or []
    codes = d.get("weather_code") or []
    sunr = d.get("sunrise") or []
    suns = d.get("sunset") or []
    uv = d.get("uv_index_max") or []

    points: list[dict[str, Any]] = []
    for i in range(min(len(dates), 10)):
        points.append(
            DailyPoint(
                date=dates[i],
                temp_max_c=tmax[i] if i < len(tmax) else None,
                temp_min_c=tmin[i] if i < len(tmin) else None,
                sunrise=sunr[i] if i < len(sunr) else None,
                sunset=suns[i] if i < len(suns) else None,
                uv_index_max=uv[i] if i < len(uv) else None,
                weather=describe_weather(codes[i] if i < len(codes) else None),
            ).model_dump()
        )

    _set_cached(session, loc.id, "daily", points)
    return points


from __future__ import annotations

import random
import re
import sys
import uuid
from datetime import datetime, timedelta
from typing import Iterable
from urllib.parse import quote_plus

from faker import Faker
from sqlalchemy import delete
from sqlmodel import Session

from app.core.db import engine, init_db
from app.core.security import hash_password
from app.models.content import Article, Category, Deal, Photo
from app.models.location import Location, SavedLocation
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.user import RefreshToken, User
from app.models.weather_cache import WeatherCache


def slugify(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    return t or "item"


UNSPLASH = [
    "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1499346030926-9a72daac6c63?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1482192505345-5655af888cc4?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1458668383970-8ddd3927deed?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1507149833265-60c372daea22?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1501630834273-4b5604d2ee31?auto=format&fit=crop&w=1600&q=80",
]


MAJOR_US_CITIES: list[tuple[str, str, str | None, float, float, str]] = [
    ("Los Angeles", "CA", "90012", 34.0522, -118.2437, "America/Los_Angeles"),
    ("San Francisco", "CA", "94103", 37.7749, -122.4194, "America/Los_Angeles"),
    ("San Diego", "CA", "92101", 32.7157, -117.1611, "America/Los_Angeles"),
    ("Seattle", "WA", "98101", 47.6062, -122.3321, "America/Los_Angeles"),
    ("Portland", "OR", "97205", 45.5152, -122.6784, "America/Los_Angeles"),
    ("Las Vegas", "NV", "89101", 36.1699, -115.1398, "America/Los_Angeles"),
    ("Phoenix", "AZ", "85004", 33.4484, -112.0740, "America/Phoenix"),
    ("Denver", "CO", "80202", 39.7392, -104.9903, "America/Denver"),
    ("Dallas", "TX", "75201", 32.7767, -96.7970, "America/Chicago"),
    ("Houston", "TX", "77002", 29.7604, -95.3698, "America/Chicago"),
    ("Austin", "TX", "78701", 30.2672, -97.7431, "America/Chicago"),
    ("San Antonio", "TX", "78205", 29.4241, -98.4936, "America/Chicago"),
    ("Chicago", "IL", "60601", 41.8781, -87.6298, "America/Chicago"),
    ("Minneapolis", "MN", "55401", 44.9778, -93.2650, "America/Chicago"),
    ("St. Louis", "MO", "63101", 38.6270, -90.1994, "America/Chicago"),
    ("Nashville", "TN", "37219", 36.1627, -86.7816, "America/Chicago"),
    ("Atlanta", "GA", "30303", 33.7490, -84.3880, "America/New_York"),
    ("Miami", "FL", "33130", 25.7617, -80.1918, "America/New_York"),
    ("Orlando", "FL", "32801", 28.5383, -81.3792, "America/New_York"),
    ("Charlotte", "NC", "28202", 35.2271, -80.8431, "America/New_York"),
    ("Washington", "DC", "20001", 38.9072, -77.0369, "America/New_York"),
    ("Baltimore", "MD", "21201", 39.2904, -76.6122, "America/New_York"),
    ("Philadelphia", "PA", "19103", 39.9526, -75.1652, "America/New_York"),
    ("New York", "NY", "10001", 40.7128, -74.0060, "America/New_York"),
    ("Boston", "MA", "02108", 42.3601, -71.0589, "America/New_York"),
    ("Detroit", "MI", "48226", 42.3314, -83.0458, "America/New_York"),
    ("Pittsburgh", "PA", "15222", 40.4406, -79.9959, "America/New_York"),
    ("Cleveland", "OH", "44114", 41.4993, -81.6944, "America/New_York"),
    ("Tampa", "FL", "33602", 27.9506, -82.4572, "America/New_York"),
    ("New Orleans", "LA", "70112", 29.9511, -90.0715, "America/Chicago"),
    ("Salt Lake City", "UT", "84101", 40.7608, -111.8910, "America/Denver"),
    ("Albuquerque", "NM", "87102", 35.0844, -106.6504, "America/Denver"),
]


STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA",
    "MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
    "TX","UT","VT","VA","WA","WV","WI","WY",
]


def guess_tz_from_lon(lon: float) -> str:
    # Rough US tz split by longitude; good enough for seeded data.
    if lon < -114:
        return "America/Los_Angeles"
    if lon < -102:
        return "America/Denver"
    if lon < -85:
        return "America/Chicago"
    return "America/New_York"


def unique_slug(existing: set[str], base: str) -> str:
    s = base
    i = 2
    while s in existing:
        s = f"{base}-{i}"
        i += 1
    existing.add(s)
    return s


def chunked(it: Iterable, size: int):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf


def deal_cta_url(title: str) -> str:
    # Provide a real, non-placeholder destination for deal cards.
    # Using an external search URL keeps the demo seed deterministic and functional.
    return f"https://www.amazon.com/s?k={quote_plus(title)}"


def reset_all(session: Session) -> None:
    # Delete in FK-safe order.
    for model in [
        WeatherCache,
        Subscription,
        SubscriptionPlan,
        SavedLocation,
        RefreshToken,
        Deal,
        Photo,
        Article,
        Category,
        Location,
        User,
    ]:
        session.exec(delete(model))
    session.commit()


def main() -> int:
    random.seed(42)
    fake = Faker()
    fake.seed_instance(42)

    init_db()
    with Session(engine) as session:
        reset_all(session)

        # Users (dev/demo)
        demo_users: list[User] = []
        demo_password = "Password123!"
        for i in range(1, 9):
            demo_users.append(
                User(
                    email=f"demo{i}@example.com",
                    name=fake.name(),
                    hashed_password=hash_password(demo_password),
                )
            )
        session.add_all(demo_users)
        session.commit()

        # Categories
        categories = [
            ("Top Stories", "top-stories"),
            ("Latest News", "latest-news"),
            ("Editor’s Picks", "editors-picks"),
            ("Stay Safe", "stay-safe"),
            ("Recommended", "recommended"),
            ("Video", "video"),
            ("Photos", "photos"),
            ("Deals", "deals"),
        ]
        cat_models: list[Category] = [Category(name=n, slug=s) for n, s in categories]
        session.add_all(cat_models)
        session.commit()
        cat_by_slug = {c.slug: c for c in cat_models}

        # Locations (realistic mix)
        slugs: set[str] = set()
        locations: list[Location] = []
        for name, st, zipc, lat, lon, tz in MAJOR_US_CITIES:
            base = slugify(f"{name}-{st}")
            locations.append(
                Location(
                    name=name,
                    state=st,
                    country="US",
                    zip_code=zipc,
                    latitude=lat,
                    longitude=lon,
                    timezone=tz,
                    slug=unique_slug(slugs, base),
                )
            )

        while len(locations) < 260:
            city = fake.city()
            st = random.choice(STATES)
            lat = round(random.uniform(24.0, 49.0), 4)
            lon = round(random.uniform(-125.0, -66.0), 4)
            zipc = f"{random.randint(10000, 99999)}"
            base = slugify(f"{city}-{st}")
            locations.append(
                Location(
                    name=city,
                    state=st,
                    country="US",
                    zip_code=zipc,
                    latitude=lat,
                    longitude=lon,
                    timezone=guess_tz_from_lon(lon),
                    slug=unique_slug(slugs, base),
                )
            )

        session.add_all(locations)
        session.commit()

        # Saved locations for demos
        for u in demo_users:
            for loc in random.sample(locations, k=5):
                session.add(SavedLocation(user_id=u.id, location_id=loc.id))
        session.commit()

        # Subscription plans
        plans = [
            SubscriptionPlan(
                name="Basic",
                price_monthly_usd=0.0,
                description="Free access to core forecasts and articles.",
                features=["Forecasts", "News feed", "Photos"],
            ),
            SubscriptionPlan(
                name="Premium Bundle",
                price_monthly_usd=4.99,
                description="Fewer ads, premium maps, and extra personalization.",
                features=["Ad-light experience", "Premium radar layers", "Extended alerts", "Saved locations sync"],
            ),
        ]
        session.add_all(plans)
        session.commit()

        # Give a couple demo users a subscription
        premium = plans[1]
        for u in random.sample(demo_users, k=3):
            session.add(Subscription(user_id=u.id, plan_id=premium.id, status="active"))
        session.commit()

        # Deals
        deal_titles = [
            "Waterproof Windbreaker (Packable)",
            "Rechargeable Emergency Weather Radio",
            "Insulated Travel Mug (20 oz)",
            "All-Season Car Floor Mats",
            "Portable Phone Power Bank (20,000mAh)",
            "LED Headlamp (2-pack)",
            "Lightweight Daypack (25L)",
            "Compact Umbrella (Windproof)",
        ]
        deals: list[Deal] = []
        for t in deal_titles:
            deals.append(
                Deal(
                    title=t,
                    image_url=random.choice(UNSPLASH),
                    provider=random.choice(["GoodDeals", "DailySavings", "OutdoorPro"]),
                    price_usd=round(random.uniform(12.0, 129.0), 2),
                    badge=random.choice([None, "Limited Time", "Best Seller"]),
                    cta_url=deal_cta_url(t),
                )
            )
        # Add more deals to reach target volume
        while len(deals) < 22:
            title = f"{fake.word().title()} {random.choice(['Jacket','Boots','Gloves','Backpack','Bottle'])}"
            deals.append(
                Deal(
                    title=title,
                    image_url=random.choice(UNSPLASH),
                    provider=random.choice(["GoodDeals", "DailySavings", "OutdoorPro"]),
                    price_usd=round(random.uniform(9.0, 249.0), 2),
                    badge=random.choice([None, "New", "Limited Time", "Editor Pick"]),
                    cta_url=deal_cta_url(title),
                )
            )
        session.add_all(deals)
        session.commit()

        # Photos
        photos: list[Photo] = []
        for _ in range(100):
            loc = random.choice(locations)
            photos.append(
                Photo(
                    title=fake.sentence(nb_words=6).rstrip("."),
                    image_url=random.choice(UNSPLASH),
                    caption=fake.paragraph(nb_sentences=3),
                    location_id=loc.id if random.random() < 0.7 else None,
                    # Use naive timestamps (stored as UTC-like) for sqlite simplicity.
                    published_at=datetime.now() - timedelta(days=random.randint(0, 60)),
                )
            )
        session.add_all(photos)
        session.commit()

        # Articles
        weather_terms = [
            "Winter Storm",
            "Heat Advisory",
            "Flood Watch",
            "Severe Thunderstorm",
            "Tropical Update",
            "Snow Squall",
            "Gusty Winds",
            "Drought Monitor",
            "Atmospheric River",
            "Ice Storm",
        ]
        title_templates = [
            "{term} Could Impact Travel This Weekend",
            "What To Know About The Next {term}",
            "{term} Threat Shifts East As Conditions Change",
            "Forecasters Track {term} Developing Over The Plains",
            "How {term} May Affect Your Area",
        ]

        def gen_body() -> str:
            return "\n".join(
                [
                    f"## {fake.sentence(nb_words=6).rstrip('.')}",
                    fake.paragraph(nb_sentences=5),
                    "",
                    "### Key takeaways",
                    f"- {fake.sentence(nb_words=10).rstrip('.')}",
                    f"- {fake.sentence(nb_words=10).rstrip('.')}",
                    f"- {fake.sentence(nb_words=10).rstrip('.')}",
                    "",
                    f"## {fake.sentence(nb_words=7).rstrip('.')}",
                    fake.paragraph(nb_sentences=6),
                ]
            )

        article_slugs: set[str] = set()
        articles: list[Article] = []
        cat_choices = [
            cat_by_slug["top-stories"],
            cat_by_slug["latest-news"],
            cat_by_slug["editors-picks"],
            cat_by_slug["stay-safe"],
            cat_by_slug["recommended"],
            cat_by_slug["video"],
        ]
        for i in range(180):
            term = random.choice(weather_terms)
            title = random.choice(title_templates).format(term=term)
            # add variation
            if random.random() < 0.6:
                title = f"{title}: {fake.city()} Braces For Changes"

            slug = unique_slug(article_slugs, slugify(title))
            cat = random.choice(cat_choices)
            is_video = cat.slug == "video" or random.random() < 0.18
            published = datetime.now() - timedelta(hours=random.randint(0, 24 * 21))
            articles.append(
                Article(
                    category_id=cat.id,
                    title=title,
                    slug=slug,
                    summary=fake.paragraph(nb_sentences=2),
                    body_md=gen_body(),
                    hero_image_url=random.choice(UNSPLASH),
                    is_video=is_video,
                    source=random.choice(["The Weather Desk", "StormWatch", "ClimateWire", "Weather Portal"]),
                    reading_minutes=random.randint(2, 8),
                    published_at=published,
                )
            )

        for batch in chunked(articles, 50):
            session.add_all(batch)
            session.commit()

        print("Seed complete.")
        print(f"Users: {len(demo_users)} (password: {demo_password})")
        print(f"Locations: {len(locations)}")
        print(f"Articles: {len(articles)}")
        print(f"Photos: {len(photos)}")
        print(f"Deals: {len(deals)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


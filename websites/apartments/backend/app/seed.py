from __future__ import annotations

import random
from datetime import date, timedelta

from faker import Faker
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.amenity import Amenity
from app.models.listing import Listing, ListingImage
from app.models.location import Location


def _unsplash_urls() -> list[str]:
    # Stable-ish Unsplash photo IDs. (No API key required.)
    base = [
        "https://images.unsplash.com/photo-1501183638710-841dd1904471",
        "https://images.unsplash.com/photo-1505691938895-1758d7feb511",
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2",
        "https://images.unsplash.com/photo-1484154218962-a197022b5858",
        "https://images.unsplash.com/photo-1502005229762-cf1b2da7c5d6",
        "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688",
        "https://images.unsplash.com/photo-1494526585095-c41746248156",
        "https://images.unsplash.com/photo-1449844908441-8829872d2607",
    ]
    return [f"{u}?auto=format&fit=crop&w=1400&q=60" for u in base]


def seed(db: Session, *, seed_random: int = 42) -> None:
    random.seed(seed_random)
    fake = Faker()
    Faker.seed(seed_random)

    # Locations (used for typeahead + default landing city).
    if db.query(Location).count() == 0:
        db.add_all(
            [
                Location(name="Columbus", state="OH", kind="city", latitude=39.9612, longitude=-82.9988),
                Location(name="Boston", state="MA", kind="city", latitude=42.3601, longitude=-71.0589),
                Location(name="Cambridge", state="MA", kind="city", latitude=42.3736, longitude=-71.1097),
                Location(name="Somerville", state="MA", kind="city", latitude=42.3876, longitude=-71.0995),
                Location(name="Brookline", state="MA", kind="city", latitude=42.3318, longitude=-71.1212),
            ]
        )
        db.commit()

    amenity_names = [
        "Dog & Cat Friendly",
        "Fitness Center",
        "Pool",
        "Dishwasher",
        "Refrigerator",
        "In Unit Washer & Dryer",
        "Walk-In Closets",
        "Microwave",
        "Controlled Access",
        "Rooftop Deck",
        "Package Service",
        "Garage Parking",
        "Air Conditioning",
    ]
    if db.query(Amenity).count() == 0:
        db.add_all([Amenity(name=n) for n in amenity_names])
        db.commit()

    if db.query(Listing).count() > 0:
        return

    amenities = db.query(Amenity).all()
    photos = _unsplash_urls()

    def jitter(center: float, magnitude: float) -> float:
        return center + (random.random() - 0.5) * magnitude

    def gen_cluster(*, city: str, state: str, lat0: float, lon0: float, count: int) -> None:
        # Dense cluster for map pins.
        neighborhoods = [
            "Downtown",
            "Seaport",
            "Back Bay",
            "Fenway",
            "South End",
            "East Side",
            "Old Town",
            "Riverside",
            "University District",
        ]
        property_names = [
            "The Brynx",
            "Parkway Apartments",
            "Fenway Triangle",
            "DOT Block",
            "212 Stuart",
            "The Alyx at EchelonSeaport",
            "The Charles at Bexley",
            "Fountain Place",
            "College Park",
            "Raccoon Creek Apartments",
        ]
        mgmt = ["Greystar", "Samuels & Associates", "Lincoln Property Company", "Bozzuto", "AvalonBay"]

        for i in range(count):
            name = random.choice(property_names) if i < 10 else f"{fake.company()} Apartments"
            street = f"{fake.building_number()} {fake.street_name()} St"
            lat = jitter(lat0, 0.25)
            lon = jitter(lon0, 0.35)

            base_price = random.randint(1100, 5200)
            max_price = base_price + random.randint(300, 16000)
            min_beds = random.choice([0, 1, 2])
            max_beds = min(4, min_beds + random.choice([0, 1, 2, 3]))
            if max_beds < min_beds:
                max_beds = min_beds

            listing = Listing(
                name=name,
                street=street,
                city=city,
                state=state,
                postal_code=str(random.randint(2100, 2199)) if state == "MA" else str(random.randint(4300, 4329)),
                latitude=lat,
                longitude=lon,
                min_price=base_price,
                max_price=max_price,
                min_beds=min_beds,
                max_beds=max_beds,
                property_type=random.choice(["apartment", "condo", "townhome"]),
                move_in_date=(date.today() + timedelta(days=random.randint(0, 60))) if random.random() < 0.5 else None,
                description=(
                    f"Modern living near {random.choice(neighborhoods)} with premium finishes, "
                    "thoughtful amenities, and easy access to dining, transit, and parks."
                ),
                phone=f"({random.randint(617, 857) if state == 'MA' else random.randint(380, 740)}) "
                f"{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                management_name=random.choice(mgmt),
                specials="Specials" if random.random() < 0.25 else None,
                has_videos=random.random() < 0.35,
                has_virtual_tour=random.random() < 0.55,
            )
            listing.amenities = random.sample(amenities, k=random.randint(4, min(9, len(amenities))))
            db.add(listing)
            db.flush()  # get listing.id

            for j in range(3):
                db.add(ListingImage(listing_id=listing.id, url=random.choice(photos), sort_order=j))

    # Generate a dense cluster around Boston to match the map-heavy reference screenshots.
    gen_cluster(city="Boston", state="MA", lat0=42.3601, lon0=-71.0589, count=180)
    # Landing page references Columbus, OH; keep a smaller dataset there too.
    gen_cluster(city="Columbus", state="OH", lat0=39.9612, lon0=-82.9988, count=60)

    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed(db)
    print("Seed complete.")


if __name__ == "__main__":
    main()


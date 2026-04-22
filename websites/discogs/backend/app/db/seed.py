from __future__ import annotations

import random
import re
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

from faker import Faker
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import (
    Artist,
    CartItem,
    CollectionItem,
    Comment,
    Genre,
    Label,
    MarketplaceListing,
    Order,
    OrderItem,
    Release,
    ReleaseArtist,
    ReleaseFormat,
    ReleaseGenre,
    ReleaseLabel,
    ReleaseStyle,
    Style,
    Track,
    User,
    WantlistItem,
)
from app.services.auth import hash_password


fake = Faker()


UNSPLASH = [
    # music / vinyl / studio themed
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1519985176271-adb1088fa94c?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1517211903932-4f4c0b9b2bfb?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1485579149621-3123dd979885?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1521334884684-d80222895322?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1525286116112-b59af11adad1?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1465847899084-d164df4dedc6?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1524678606370-a47ad25cb82a?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1517230878791-4d28214057c2?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1530133532239-eda6f53fcf0f?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1514924013411-cbf25faa35bb?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1531058020387-3be344556be6?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1517263904808-5dc91e3e7044?auto=format&fit=crop&w=600&q=80",
]


MEDIA_CONDITIONS = ["Mint (M)", "Near Mint (NM or M-)", "Very Good Plus (VG+)", "Very Good (VG)", "Good (G)", "Fair (F)"]
SLEEVE_CONDITIONS = ["Mint (M)", "Near Mint (NM or M-)", "Very Good Plus (VG+)", "Very Good (VG)", "Good (G)"]
COUNTRIES = ["US", "UK", "Germany", "Japan", "France", "Canada", "Netherlands", "Australia", "Sweden", "Italy"]


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\\s-]", "", text)
    text = re.sub(r"\\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-") or "item"


def _clear_all(db: Session) -> None:
    # Delete order matters because of FK constraints.
    for model in [
        OrderItem,
        Order,
        CartItem,
        MarketplaceListing,
        Comment,
        WantlistItem,
        CollectionItem,
        Track,
        ReleaseFormat,
        ReleaseStyle,
        ReleaseGenre,
        ReleaseLabel,
        ReleaseArtist,
        Release,
        Style,
        Genre,
        Label,
        Artist,
        User,
    ]:
        db.execute(delete(model))
    db.commit()


def seed(db: Session, seed: int = 42) -> None:
    random.seed(seed)
    Faker.seed(seed)

    _clear_all(db)

    # Users
    demo = User(
        username="demo",
        email="demo@example.com",
        password_hash=hash_password("password123"),
        display_name="Demo User",
        avatar_url=random.choice(UNSPLASH),
        location="New York, USA",
        seller_rating=99.6,
    )
    db.add(demo)

    users: list[User] = [demo]
    for _ in range(29):
        username = slugify(fake.user_name())[:20] + str(random.randint(10, 99))
        user = User(
            username=username,
            email=f"{username}@example.com",
            password_hash=hash_password("password123"),
            display_name=fake.name(),
            avatar_url=random.choice(UNSPLASH),
            location=f"{fake.city()}, {fake.country()}",
            seller_rating=round(random.uniform(92.0, 100.0), 1),
        )
        users.append(user)
        db.add(user)

    # Genres & styles (include Rock page tags)
    genres_data = {
        "Rock": [
            "Pop Rock",
            "Hard Rock",
            "Indie Rock",
            "Alternative Rock",
            "Psychedelic Rock",
            "Prog Rock",
            "Classic Rock",
            "Garage Rock",
            "Blues Rock",
            "Folk Rock",
        ],
        "Electronic": ["Synth-pop", "Techno", "House", "Ambient", "Electro", "Downtempo"],
        "Pop": ["Vocal", "Europop", "Dance-pop"],
        "Hip Hop": ["Boom Bap", "Trap", "Instrumental"],
        "Jazz": ["Fusion", "Bebop", "Modal", "Cool Jazz"],
    }

    genres: dict[str, Genre] = {}
    styles: dict[str, Style] = {}

    rock_description = (
        "Rock music is a broad genre of popular music that originated as \"rock and roll\" in the United States "
        "in the late 1940s and early 1950s, developing into a range of different styles in the mid-1960s and later. "
        "It drew on blues, rhythm and blues, and country music, but also borrowed from other genres such as folk, jazz, "
        "and classical. Rock music is known for a strong back beat and often revolves around the electric guitar."
    )

    for gname, style_names in genres_data.items():
        g = Genre(
            name=gname,
            slug=slugify(gname),
            description=rock_description if gname == "Rock" else fake.paragraph(nb_sentences=6),
        )
        db.add(g)
        db.flush()
        genres[gname] = g
        for sname in style_names:
            s = Style(genre_id=g.id, name=sname, slug=slugify(sname))
            db.add(s)
            db.flush()
            styles[f"{gname}:{sname}"] = s

    # Artists & labels (mix of known-like and generated)
    curated_artists = [
        "Pink Floyd",
        "The Beatles",
        "David Bowie",
        "Kraftwerk",
        "New Order",
        "Depeche Mode",
        "Talking Heads",
        "Daft Punk",
        "Radiohead",
        "Nirvana",
        "The Cure",
        "Joy Division",
    ]
    curated_labels = ["Harvest", "EMI", "Columbia", "Warner Bros.", "Mute", "Factory", "Atlantic", "Capitol"]

    artist_rows: list[Artist] = []
    for name in curated_artists:
        a = Artist(name=name, slug=slugify(name), profile_text=fake.paragraph(nb_sentences=4), image_url=random.choice(UNSPLASH))
        db.add(a)
        artist_rows.append(a)

    for _ in range(60):
        name = f"{fake.last_name()} {random.choice(['Trio','Ensemble','Project','Band','Collective','Duo','Quartet'])}"
        a = Artist(name=name, slug=slugify(name) + str(random.randint(1, 999)), profile_text=fake.paragraph(nb_sentences=5), image_url=random.choice(UNSPLASH))
        db.add(a)
        artist_rows.append(a)

    label_rows: list[Label] = []
    for name in curated_labels:
        l = Label(name=name, slug=slugify(name), profile_text=fake.paragraph(nb_sentences=3), image_url=random.choice(UNSPLASH))
        db.add(l)
        label_rows.append(l)

    for _ in range(40):
        name = f"{fake.last_name()} Records"
        l = Label(name=name, slug=slugify(name) + str(random.randint(1, 999)), profile_text=fake.paragraph(nb_sentences=4), image_url=random.choice(UNSPLASH))
        db.add(l)
        label_rows.append(l)

    db.flush()

    # Releases
    releases: list[Release] = []
    now = datetime.now(timezone.utc)
    for i in range(220):
        gname = random.choices(list(genres.keys()), weights=[0.35, 0.25, 0.15, 0.15, 0.10])[0]
        g = genres[gname]
        style_candidates = [s for k, s in styles.items() if k.startswith(gname + ":")]
        chosen_styles = random.sample(style_candidates, k=min(len(style_candidates), random.choice([1, 1, 2])))

        year = random.randint(1965, 2025)
        released = date(year, random.randint(1, 12), random.randint(1, 28))

        title = fake.catch_phrase()[:60]
        r = Release(
            title=title,
            year=year,
            released_date=released,
            country=random.choice(COUNTRIES),
            notes=fake.paragraph(nb_sentences=12),
            cover_image_url=random.choice(UNSPLASH),
            submitted_by_user_id=random.choice(users).id,
            created_at=now - timedelta(days=random.randint(0, 1200)),
            updated_at=now - timedelta(days=random.randint(0, 300)),
        )
        db.add(r)
        db.flush()

        # artists
        main_artist = random.choice(artist_rows)
        db.add(ReleaseArtist(release_id=r.id, artist_id=main_artist.id, role="Main", position=0))
        if random.random() < 0.18:
            feat = random.choice(artist_rows)
            db.add(ReleaseArtist(release_id=r.id, artist_id=feat.id, role="Featuring", position=1))

        # labels
        lbl = random.choice(label_rows)
        db.add(ReleaseLabel(release_id=r.id, label_id=lbl.id, catalog_no=f"{slugify(lbl.name).upper()[:4]}-{random.randint(100,9999)}"))

        # genre/style
        db.add(ReleaseGenre(release_id=r.id, genre_id=g.id))
        for s in chosen_styles:
            db.add(ReleaseStyle(release_id=r.id, style_id=s.id))

        # formats
        fmt_name = random.choices(["Vinyl", "CD", "Cassette", "File"], weights=[0.55, 0.3, 0.1, 0.05])[0]
        fmt_text = random.choice(["LP, Album", "LP, Reissue", "12\", Single", "Album", "EP", "Compilation"])
        db.add(ReleaseFormat(release_id=r.id, name=fmt_name, qty=1, text=fmt_text))

        # tracks
        track_count = random.randint(7, 12) if fmt_name != "File" else random.randint(8, 16)
        for t in range(1, track_count + 1):
            pos = str(t) if fmt_name != "Vinyl" else f"{'A' if t <= track_count//2 else 'B'}{t if t <= track_count//2 else t-track_count//2}"
            db.add(
                Track(
                    release_id=r.id,
                    position=pos,
                    title=fake.sentence(nb_words=random.randint(2, 5)).rstrip("."),
                    duration_seconds=random.randint(120, 420),
                )
            )

        releases.append(r)

    # Add one explicitly recognizable record to match the homepage banner vibe
    pink_floyd = next(a for a in artist_rows if a.name == "Pink Floyd")
    harvest = next(l for l in label_rows if l.name == "Harvest")
    rock = genres["Rock"]
    psychedelic = styles["Rock:Psychedelic Rock"]
    classic = styles["Rock:Classic Rock"]

    dsotm = Release(
        title="The Dark Side Of The Moon",
        year=1973,
        released_date=date(1973, 3, 1),
        country="UK",
        notes=(
            "A landmark progressive rock album featuring lush production, conceptual continuity, "
            "and iconic artwork. This entry is seeded for the clone’s demo dataset."
        ),
        cover_image_url="https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=600&q=80",
        submitted_by_user_id=random.choice(users).id,
    )
    db.add(dsotm)
    db.flush()
    db.add(ReleaseArtist(release_id=dsotm.id, artist_id=pink_floyd.id, role="Main", position=0))
    db.add(ReleaseLabel(release_id=dsotm.id, label_id=harvest.id, catalog_no="SHVL 804"))
    db.add(ReleaseGenre(release_id=dsotm.id, genre_id=rock.id))
    db.add(ReleaseStyle(release_id=dsotm.id, style_id=psychedelic.id))
    db.add(ReleaseStyle(release_id=dsotm.id, style_id=classic.id))
    db.add(ReleaseFormat(release_id=dsotm.id, name="Vinyl", qty=1, text="LP, Album"))

    dsotm_tracks = [
        ("A1", "Speak to Me", 90),
        ("A2", "Breathe (In the Air)", 163),
        ("A3", "On the Run", 216),
        ("A4", "Time", 413),
        ("A5", "The Great Gig in the Sky", 276),
        ("B1", "Money", 382),
        ("B2", "Us and Them", 462),
        ("B3", "Any Colour You Like", 205),
        ("B4", "Brain Damage", 228),
        ("B5", "Eclipse", 123),
    ]
    for pos, title, secs in dsotm_tracks:
        db.add(Track(release_id=dsotm.id, position=pos, title=title, duration_seconds=secs))

    releases.append(dsotm)
    db.flush()

    # Marketplace listings
    # Ensure the seeded banner release has plenty of listings for the marketplace page demo.
    for _ in range(24):
        price = int(random.triangular(1200, 9000, 2600))
        if random.random() < 0.08:
            price *= random.randint(3, 12)
        db.add(
            MarketplaceListing(
                release_id=dsotm.id,
                seller_user_id=random.choice(users).id,
                media_condition=random.choice(MEDIA_CONDITIONS),
                sleeve_condition=random.choice(SLEEVE_CONDITIONS),
                price_cents=price,
                currency="USD",
                ships_from=random.choice(COUNTRIES),
                comments=fake.sentence(nb_words=14),
                quantity=random.randint(1, 2),
                status="active",
            )
        )

    for r in random.sample(releases, k=min(len(releases), 160)):
        for _ in range(random.randint(1, 7)):
            price = int(random.triangular(800, 5500, 1800))
            if random.random() < 0.03:
                price *= random.randint(4, 20)  # expensive outliers

            listing = MarketplaceListing(
                release_id=r.id,
                seller_user_id=random.choice(users).id,
                media_condition=random.choice(MEDIA_CONDITIONS),
                sleeve_condition=random.choice(SLEEVE_CONDITIONS),
                price_cents=price,
                currency="USD",
                ships_from=random.choice(COUNTRIES),
                comments=fake.sentence(nb_words=12),
                quantity=random.randint(1, 3),
                status="active",
            )
            db.add(listing)

    db.flush()

    # Collections / wantlists
    for u in users:
        for r in random.sample(releases, k=random.randint(10, 35)):
            db.add(CollectionItem(user_id=u.id, release_id=r.id))
        for r in random.sample(releases, k=random.randint(8, 25)):
            db.add(WantlistItem(user_id=u.id, release_id=r.id))

    # Comments
    for _ in range(120):
        r = random.choice(releases)
        u = random.choice(users)
        db.add(
            Comment(
                user_id=u.id,
                entity_type="release",
                entity_id=r.id,
                body=fake.paragraph(nb_sentences=3),
            )
        )

    # Orders to power "sold this month" and "expensive sold"
    listings = db.query(MarketplaceListing).all()
    for _ in range(120):
        buyer = random.choice(users)
        items = random.sample(listings, k=random.randint(1, 3))
        total = sum(i.price_cents for i in items)
        o = Order(
            buyer_user_id=buyer.id,
            total_cents=total,
            currency="USD",
            status="paid",
            created_at=now - timedelta(days=random.randint(0, 28)),
        )
        db.add(o)
        db.flush()
        for it in items:
            db.add(OrderItem(order_id=o.id, listing_id=it.id, price_cents=it.price_cents, quantity=1))

    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        seed(db)
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()


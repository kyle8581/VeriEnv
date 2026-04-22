from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.base import Base
from app.db.models import (
    Company,
    EmploymentType,
    ExperienceLevel,
    Job,
    Post,
    Reaction,
    ReactionType,
    SearchSuggestion,
    User,
    WorkMode,
)
from app.db.session import SessionLocal, engine

fake = Faker()


def _unsplash_image(*, width: int, height: int, sig: int, topic: str) -> str:
    # Deterministic-ish Unsplash random image URL (allowed by requirements).
    # Using `sig` avoids repeated caching collisions.
    return f"https://images.unsplash.com/random/{width}x{height}?sig={sig}&{topic}"


def reset_db() -> None:
    from app.db import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed_db(*, reset: bool = False) -> None:
    if reset:
        reset_db()
    else:
        # Ensure tables exist
        from app.db import models  # noqa: F401

        Base.metadata.create_all(bind=engine)

    rnd = random.Random(1337)
    Faker.seed(1337)

    with SessionLocal() as db:
        # Idempotency guard: if users exist, don't double seed unless reset=True
        existing = db.scalar(select(User.id).limit(1))
        if existing and not reset:
            return

        _seed_suggestions(db)
        users = _seed_users(db, rnd)
        db.flush()  # assign user IDs

        companies = _seed_companies(db, rnd)
        db.flush()  # assign company IDs (needed before creating jobs)

        jobs = _seed_jobs(db, rnd, companies)
        posts = _seed_posts(db, rnd, users)
        _seed_reactions_and_comments(db, rnd, users, posts)

        # Make sure at least one user has saved/applied jobs (for UI states)
        _seed_user_job_states(db, rnd, users, jobs)

        db.commit()


def _seed_suggestions(db: Session) -> None:
    suggestions = [
        ("bioinformatician", 1000),
        ("bioinformatician jobs", 950),
        ("bioinformatician intern", 750),
        ("bioinformatician salary", 720),
        ("bioinformatics", 680),
        ("bioinformatics jobs", 620),
        ("bioinformatician analyst", 540),
        ("bioinformatics scientist", 520),
        ("computational biology", 500),
        ("data scientist", 480),
        ("machine learning engineer", 460),
        ("research scientist", 440),
    ]
    for q, pop in suggestions:
        db.add(SearchSuggestion(query=q, popularity=pop))


def _seed_users(db: Session, rnd: random.Random) -> list[User]:
    users: list[User] = []

    # Known demo user for local testing / SDK examples
    demo = User(
        email="jane.doe@example.com",
        password_hash=hash_password("password123"),
        first_name="Jane",
        last_name="Doe",
        headline="Senior Bioinformatics Analyst • Genomics • Data Products",
        location="United States",
        avatar_url=_unsplash_image(width=200, height=200, sig=1, topic="face"),
        banner_url=_unsplash_image(width=1200, height=300, sig=2, topic="office"),
    )
    db.add(demo)
    users.append(demo)

    for i in range(2, 62):
        first = fake.first_name()
        last = fake.last_name()
        headline = rnd.choice(
            [
                "Software Engineer • Distributed Systems",
                "Data Scientist • NLP • Recommender Systems",
                "Product Manager • Growth • B2B SaaS",
                "Research Scientist • Computational Biology",
                "UX Designer • Design Systems",
                "Security Engineer • Cloud • Threat Detection",
                "Bioinformatics Scientist • Sequence Analysis",
            ]
        )
        location = rnd.choice(
            [
                "United States",
                "Los Angeles, CA",
                "San Francisco Bay Area",
                "New York, NY",
                "Boston, MA",
                "Chicago, IL",
                "Seattle, WA",
                "Austin, TX",
            ]
        )
        u = User(
            email=f"{first.lower()}.{last.lower()}{i}@example.com",
            password_hash=hash_password("password123"),
            first_name=first,
            last_name=last,
            headline=headline,
            location=location,
            avatar_url=_unsplash_image(width=200, height=200, sig=1000 + i, topic="portrait"),
            banner_url=_unsplash_image(width=1200, height=300, sig=2000 + i, topic="workspace"),
        )
        db.add(u)
        users.append(u)

    # A “LinkedIn News” style account for news posts
    news = User(
        email="linkedin.news@example.com",
        password_hash=hash_password("password123"),
        first_name="LinkedIn",
        last_name="News",
        headline="Top stories and analysis",
        location="",
        avatar_url=_unsplash_image(width=200, height=200, sig=9999, topic="logo"),
        banner_url=_unsplash_image(width=1200, height=300, sig=9998, topic="news"),
    )
    db.add(news)
    users.append(news)

    return users


def _seed_companies(db: Session, rnd: random.Random) -> list[Company]:
    companies: list[Company] = []
    seeds = [
        ("Cedars-Sinai", "Hospitals and Health Care", "10,001+ employees"),
        ("UCLA Health", "Hospitals and Health Care", "10,001+ employees"),
        ("Tempus Labs, Inc.", "Biotechnology Research", "1,001-5,000 employees"),
        ("BioTalent", "Staffing and Recruiting", "201-500 employees"),
        ("Gene Therapy Program", "Research Services", "501-1,000 employees"),
        ("McGovern Lab", "Research Services", "51-200 employees"),
        ("WGU", "Higher Education", "5,001-10,000 employees"),
        ("HelixWorks", "Biotechnology Research", "201-500 employees"),
        ("Nimbus AI", "Software Development", "501-1,000 employees"),
        ("Northwind Analytics", "Information Services", "51-200 employees"),
        ("BluePeak Security", "Computer and Network Security", "201-500 employees"),
        ("Orchard Bio", "Biotechnology Research", "51-200 employees"),
        ("Redwood Robotics", "Robotics Engineering", "201-500 employees"),
        ("Atlas Cloud", "Cloud Services", "1,001-5,000 employees"),
        ("Cedar Grove University", "Higher Education", "10,001+ employees"),
    ]
    for idx, (name, industry, size_label) in enumerate(seeds, start=1):
        c = Company(
            name=name,
            industry=industry,
            size_label=size_label,
            headquarters=rnd.choice(["Los Angeles, CA", "Boston, MA", "San Francisco, CA", "Chicago, IL", "Remote"]),
            website_url=f"https://{''.join(ch for ch in name.lower() if ch.isalnum())}.example.com",
            about=fake.paragraph(nb_sentences=6),
            logo_url=_unsplash_image(width=96, height=96, sig=3000 + idx, topic="brand"),
        )
        db.add(c)
        companies.append(c)
    return companies


def _seed_jobs(db: Session, rnd: random.Random, companies: list[Company]) -> list[Job]:
    jobs: list[Job] = []
    titles = [
        "Research Bioinformatician II",
        "Bioinformatics Scientist",
        "Jr Bioinformatician",
        "Junior Bioinformatician Analyst",
        "Principal Scientist / Associate Director, Bioinformatics",
        "Bioinformatics, Vector",
        "Computational Biologist",
        "Data Scientist, Genomics",
        "Machine Learning Engineer (Healthcare)",
        "Research Scientist, NLP",
        "Security Engineer, Detection & Response",
        "Product Manager, Platform",
    ]
    skills_pool = [
        "Bioinformatics",
        "Sequence Alignment",
        "Python",
        "R",
        "SQL",
        "AWS",
        "Docker",
        "Kubernetes",
        "Machine Learning",
        "Statistics",
        "Genomics",
        "Nextflow",
        "Snakemake",
        "Linux",
        "ETL",
        "Data Modeling",
    ]
    locations = [
        "Los Angeles, CA",
        "United States",
        "Chicago, IL",
        "Greater Boston (Hybrid)",
        "Greater Philadelphia (Hybrid)",
        "New York, NY",
        "Seattle, WA",
        "San Francisco Bay Area",
        "Austin, TX",
    ]
    for i in range(1, 141):
        company = rnd.choice(companies)
        title = rnd.choice(titles)
        location = rnd.choice(locations)
        work_mode = rnd.choice([WorkMode.onsite, WorkMode.hybrid, WorkMode.remote])
        employment_type = rnd.choice([EmploymentType.full_time, EmploymentType.contract, EmploymentType.internship])
        experience_level = rnd.choice(
            [
                ExperienceLevel.entry,
                ExperienceLevel.mid,
                ExperienceLevel.senior,
                ExperienceLevel.internship,
                ExperienceLevel.director,
            ]
        )
        promoted = rnd.random() < 0.18
        salary_min = rnd.choice([None, 65000, 78400, 95000, 120000, 145000])
        salary_max = None if salary_min is None else salary_min + rnd.choice([25000, 35000, 45000, 55000])
        posted_at = datetime.now(UTC) - timedelta(days=rnd.randint(0, 14), hours=rnd.randint(0, 23))
        skills = rnd.sample(skills_pool, k=rnd.randint(6, 10))
        description = "\n\n".join([fake.paragraph(nb_sentences=7) for _ in range(5)])
        apply_url = f"https://{''.join(ch for ch in company.name.lower() if ch.isalnum())}.example.com/careers/{i}"
        job = Job(
            company_id=company.id,
            title=title,
            location=location,
            work_mode=work_mode,
            employment_type=employment_type,
            experience_level=experience_level,
            promoted=promoted,
            actively_recruiting=rnd.random() < 0.7,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency="USD",
            skills_csv=", ".join(skills),
            description=description,
            apply_url=apply_url,
            posted_at=posted_at,
        )
        db.add(job)
        jobs.append(job)
    return jobs


def _seed_posts(db: Session, rnd: random.Random, users: list[User]) -> list[Post]:
    posts: list[Post] = []
    image_topics = ["technology", "teamwork", "office", "university", "cybersecurity", "data", "biology"]

    for i in range(1, 221):
        author = rnd.choice(users)
        body = fake.paragraph(nb_sentences=rnd.randint(2, 7))
        with_image = rnd.random() < 0.35
        image_url = (
            _unsplash_image(width=1200, height=700, sig=5000 + i, topic=rnd.choice(image_topics)) if with_image else ""
        )
        created_at = datetime.now(UTC) - timedelta(days=rnd.randint(0, 10), hours=rnd.randint(0, 23), minutes=rnd.randint(0, 59))
        p = Post(author_id=author.id, body=body, image_url=image_url, created_at=created_at)
        db.add(p)
        posts.append(p)

    # Ensure a few “news-like” posts exist
    news_author = next((u for u in users if u.email == "linkedin.news@example.com"), None)
    if news_author:
        for i in range(1, 8):
            p = Post(
                author_id=news_author.id,
                body=f"{fake.sentence(nb_words=10)}\n\n{fake.paragraph(nb_sentences=5)}",
                image_url="",
                created_at=datetime.now(UTC) - timedelta(hours=i * 6),
            )
            db.add(p)
            posts.append(p)

    return posts


def _seed_reactions_and_comments(db: Session, rnd: random.Random, users: list[User], posts: list[Post]) -> None:
    # Flush to ensure IDs exist
    db.flush()

    # Reactions
    for post in rnd.sample(posts, k=min(len(posts), 180)):
        likers = rnd.sample(users, k=rnd.randint(3, 18))
        for u in likers:
            db.add(Reaction(user_id=u.id, post_id=post.id, type=ReactionType.like))

    # Comments
    from app.db.models import Comment

    for post in rnd.sample(posts, k=min(len(posts), 120)):
        commenters = rnd.sample(users, k=rnd.randint(1, 6))
        for u in commenters:
            db.add(Comment(post_id=post.id, author_id=u.id, body=fake.sentence(nb_words=rnd.randint(8, 18))))


def _seed_user_job_states(db: Session, rnd: random.Random, users: list[User], jobs: list[Job]) -> None:
    from app.db.models import JobApplication, SavedJob

    db.flush()
    for u in rnd.sample(users, k=min(len(users), 18)):
        for job in rnd.sample(jobs, k=rnd.randint(1, 6)):
            if rnd.random() < 0.7:
                db.add(SavedJob(user_id=u.id, job_id=job.id))
            if rnd.random() < 0.35:
                db.add(JobApplication(user_id=u.id, job_id=job.id, cover_letter=""))


if __name__ == "__main__":
    seed_db(reset=True)
    print("Seeded database.")


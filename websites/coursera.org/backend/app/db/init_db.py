from __future__ import annotations

import os
import random
import re
from pathlib import Path

from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import engine
from app.models.catalog import Course, Partner, Resource
from app.models.leads import ContactLead, EbookLead
from app.models.institution import Institution
from app.models.user import User, UserRole


_faker = Faker()
Faker.seed(20260108)
random.seed(20260108)


def create_all() -> None:
    # Ensure models are imported/registered for metadata
    _ = (User, Institution, Partner, Course, Resource, EbookLead, ContactLead)
    # Ensure sqlite folder exists if using ./data/app.db
    if str(engine.url).startswith("sqlite:///./"):
        rel = str(engine.url).replace("sqlite:///./", "")
        Path(rel).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "item"


def seed_if_empty(db: Session) -> None:
    has_any = db.scalar(select(User.id).limit(1))
    if has_any:
        return
    seed(db)


def seed(db: Session) -> None:
    """
    Seed realistic data (not just a handful of dummy rows).
    Target sizes:
    - 20+ partners
    - 50+ courses
    - 10+ resources
    """

    # Users
    admin = User(
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.admin,
        password_hash=get_password_hash("adminadmin"),
    )
    learner = User(
        email="learner@example.com",
        full_name="Jamie Learner",
        role=UserRole.learner,
        password_hash=get_password_hash("learner1234"),
    )
    db.add_all([admin, learner])

    # Institutions
    institution_names = [
        ("Arizona State University", "US", "https://www.asu.edu"),
        ("University of Michigan", "US", "https://umich.edu"),
        ("University of Toronto", "CA", "https://www.utoronto.ca"),
        ("University of London", "GB", "https://www.london.ac.uk"),
        ("Georgia Institute of Technology", "US", "https://www.gatech.edu"),
        ("University of Illinois Urbana-Champaign", "US", "https://illinois.edu"),
        ("Duke University", "US", "https://www.duke.edu"),
        ("Johns Hopkins University", "US", "https://www.jhu.edu"),
        ("University of Washington", "US", "https://www.washington.edu"),
        ("University of Colorado Boulder", "US", "https://www.colorado.edu"),
        ("National University of Singapore", "SG", "https://www.nus.edu.sg"),
        ("Seoul National University", "KR", "https://www.snu.ac.kr"),
    ]
    institutions: list[Institution] = []
    for name, country, url in institution_names:
        institutions.append(
            Institution(
                name=name,
                slug=_slugify(name),
                country=country,
                website_url=url,
            )
        )
    db.add_all(institutions)

    # Partners (mix university/industry)
    partner_names = [
        "University of Michigan",
        "Yale University",
        "University of Illinois Urbana-Champaign",
        "University of Toronto",
        "Duke University",
        "University of Washington",
        "Georgia Institute of Technology",
        "University of London",
        "Johns Hopkins University",
        "Stanford Online",
        "IBM",
        "Google",
        "Microsoft",
        "Meta",
        "AWS",
        "DeepLearning.AI",
        "Intuit",
        "Salesforce",
        "SAP",
        "PwC",
        "KPMG",
        "University of California, Irvine",
        "Arizona State University",
        "University of Colorado Boulder",
    ]
    # Unsplash logo placeholders (simple square marks)
    logo_pool = [
        "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=256&h=256&q=80",
        "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=256&h=256&q=80",
        "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=256&h=256&q=80",
        "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=256&h=256&q=80",
    ]
    partners: list[Partner] = []
    for name in partner_names:
        kind = "industry" if name in {"IBM", "Google", "Microsoft", "Meta", "AWS", "Intuit", "Salesforce", "SAP", "PwC", "KPMG", "DeepLearning.AI"} else "university"
        partners.append(
            Partner(
                name=name,
                slug=_slugify(name),
                kind=kind,
                logo_url=random.choice(logo_pool),
            )
        )
    db.add_all(partners)
    db.flush()  # get partner ids

    # Courses
    course_image_pool = [
        "https://images.unsplash.com/photo-1556761175-129418cb2dfe?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80",
    ]
    levels = ["Beginner", "Intermediate", "Advanced"]
    languages = ["English", "Spanish", "French", "German", "Portuguese"]
    skill_sets = [
        ["Data Analysis", "SQL", "Dashboards", "Business Intelligence"],
        ["Machine Learning", "Python", "Model Evaluation", "Feature Engineering"],
        ["Cloud Computing", "AWS", "Networking", "Security"],
        ["Project Management", "Agile", "Scrum", "Stakeholder Management"],
        ["UX Research", "Prototyping", "Figma", "Design Systems"],
        ["Cybersecurity", "Threat Modeling", "Incident Response", "Risk Management"],
        ["Marketing Analytics", "A/B Testing", "Customer Segmentation", "Attribution"],
        ["Finance", "Valuation", "Accounting", "Forecasting"],
        ["Leadership", "Communication", "Strategy", "Team Management"],
    ]

    def unique_course_slug(base: str, existing: set[str]) -> str:
        slug = _slugify(base)
        candidate = slug
        i = 2
        while candidate in existing:
            candidate = f"{slug}-{i}"
            i += 1
        existing.add(candidate)
        return candidate

    existing_slugs: set[str] = set()
    courses: list[Course] = []
    for _ in range(60):
        topic = random.choice(
            [
                "Data Science",
                "Business",
                "Computer Science",
                "AI",
                "Cloud",
                "Cybersecurity",
                "Design",
                "Leadership",
                "Marketing",
                "Finance",
            ]
        )
        title = f"{topic}: {_faker.catch_phrase()}"
        headline = _faker.sentence(nb_words=10).rstrip(".")
        desc = "\n\n".join([_faker.paragraph(nb_sentences=5) for _ in range(3)])
        partner = random.choice(partners)
        skills = random.choice(skill_sets)
        courses.append(
            Course(
                title=title,
                slug=unique_course_slug(title, existing_slugs),
                headline=headline,
                description=desc,
                level=random.choice(levels),
                language=random.choice(languages),
                duration_hours=random.choice([6, 8, 10, 12, 15, 20, 24, 30, 40]),
                skills_csv=", ".join(skills),
                image_url=random.choice(course_image_pool),
                partner_id=partner.id,
            )
        )
    db.add_all(courses)

    # Resources (include the referenced ebook + bottom cards)
    resources: list[Resource] = [
        Resource(
            kind="ebook",
            title="Job Skills of 2023 Report",
            slug="job-skills-of-2023-report",
            summary="Discover the fastest-growing job skills for businesses, governments, and higher education institutions.",
            body_md=(
                "Explore the fastest-growing human and digital skills for 2023 and understand which skills you can prioritize "
                "to strengthen student employment outcomes.\n\n"
                "This report draws on data from Coursera learners across businesses, higher education institutions, and governments globally."
            ),
            hero_image_url="https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1600&q=80",
            cta_label="Download",
        ),
        Resource(
            kind="event",
            title="Coursera Conference 2023",
            slug="coursera-conference-2023",
            summary="Join leaders in higher education to explore the future of career-ready learning.",
            body_md="An event for institutions to connect, learn, and share outcomes.\n\nAgenda, speakers, and sessions available inside.",
            hero_image_url="https://images.unsplash.com/photo-1556761175-129418cb2dfe?auto=format&fit=crop&w=1600&q=80",
            cta_label="Explore",
        ),
        Resource(
            kind="ebook",
            title="Advancing Higher Education with Industry Micro-Credentials",
            slug="advancing-higher-education-with-industry-micro-credentials",
            summary="A practical guide to aligning curriculum with employer needs using industry credentials.",
            body_md="Learn how institutions can integrate micro-credentials into programs to improve employment outcomes.",
            hero_image_url="https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=1600&q=80",
            cta_label="Explore",
        ),
    ]
    # Add additional resources to reach 10+
    for _ in range(8):
        title = _faker.sentence(nb_words=6).rstrip(".")
        kind = random.choice(["ebook", "article", "event"])
        resources.append(
            Resource(
                kind=kind,
                title=title,
                slug=_slugify(f"{title}-{_faker.pyint(min_value=1000, max_value=9999)}"),
                summary=_faker.sentence(nb_words=18).rstrip("."),
                body_md="\n\n".join([_faker.paragraph(nb_sentences=6) for _ in range(2)]),
                hero_image_url=random.choice(course_image_pool),
                cta_label="Explore",
            )
        )
    db.add_all(resources)

    db.commit()


def reset_db_file(db_url: str) -> None:
    """
    Best-effort reset for local SQLite: delete db file, then recreate and seed.
    """
    if not db_url.startswith("sqlite"):
        raise RuntimeError("reset_db_file currently supports only sqlite")
    # sqlite:///./data/app.db or sqlite:////abs/path
    if db_url.startswith("sqlite:///./"):
        rel = db_url.replace("sqlite:///./", "")
        path = Path(rel)
    elif db_url.startswith("sqlite:////"):
        path = Path(db_url.replace("sqlite:////", "/"))
    else:
        raise RuntimeError(f"Unsupported sqlite url format: {db_url}")

    if path.exists():
        path.unlink()

    create_all()
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        seed(db)


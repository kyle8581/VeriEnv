from __future__ import annotations

import json
import random
import socket
import string
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import Thread
from typing import Any, Callable

import httpx
import uvicorn

from coursera_sdk import CourseraClient


ROOT = Path(__file__).resolve().parent
PORTS_PATH = ROOT / "ports.json"
OUT_PATH = ROOT / "task_instructions.json"


def _load_backend_port() -> int:
    data = json.loads(PORTS_PATH.read_text(encoding="utf-8"))
    return int(data["ports"]["PORT"])


def _http_ok(url: str, timeout_s: float = 0.5) -> bool:
    try:
        r = httpx.get(url, timeout=timeout_s)
        return 200 <= r.status_code < 300
    except Exception:
        return False


def _wait_http_ok(url: str, tries: int = 80, delay_s: float = 0.1) -> None:
    for _ in range(tries):
        if _http_ok(url):
            return
        time.sleep(delay_s)
    raise RuntimeError(f"Timed out waiting for {url}")


@dataclass
class _UvicornHandle:
    thread: Thread
    server: uvicorn.Server


def _is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.25)
        return s.connect_ex((host, port)) == 0


def _start_backend_if_needed(host: str, port: int) -> _UvicornHandle | None:
    health_url = f"http://{host}:{port}/health"
    if _http_ok(health_url):
        return None

    # Import backend app lazily (so SDK users without backend deps don't break).
    import sys

    sys.path.insert(0, str(ROOT / "backend"))
    from app.main import app  # type: ignore

    if _is_port_in_use(host, port):
        raise RuntimeError(f"Port {port} is in use but backend health is not OK at {health_url}")

    config = uvicorn.Config(app, host=host, port=port, log_level="error", access_log=False)
    server = uvicorn.Server(config=config)

    t = Thread(target=server.run, daemon=True)
    t.start()
    _wait_http_ok(health_url, tries=120, delay_s=0.1)
    return _UvicornHandle(thread=t, server=server)


def _stop_backend(handle: _UvicornHandle | None) -> None:
    if not handle:
        return
    handle.server.should_exit = True
    handle.thread.join(timeout=10)


def _rand_phone_us() -> str:
    # Keep it realistic-ish but not a real personal number.
    return "555" + "".join(random.choice(string.digits) for _ in range(7))


def _safe_preview(obj: Any, max_len: int = 2000) -> Any:
    """
    Ensure tool call results stay JSON-serializable and not huge.
    """
    try:
        s = json.dumps(obj, ensure_ascii=False)
    except Exception:
        return {"_repr": repr(obj)[:max_len]}
    if len(s) <= max_len:
        return obj
    # Truncate large dict/list structures.
    if isinstance(obj, dict):
        trimmed: dict[str, Any] = {}
        for k in list(obj.keys())[:30]:
            trimmed[k] = obj[k]
        trimmed["_truncated"] = True
        return trimmed
    if isinstance(obj, list):
        return {"items": obj[:30], "_truncated": True}
    return {"_json": s[:max_len], "_truncated": True}


def _make_judge_url_contains(path_fragment: str) -> str:
    return f'url=locate_current_url(s), must_include(url, "{path_fragment}")'


def _make_judge_answer_includes(*needles: str) -> str:
    parts = [f'must_include(â, "{n}")' for n in needles]
    return ", ".join(parts)


def main() -> None:
    host = "127.0.0.1"
    port = _load_backend_port()

    backend_handle = _start_backend_if_needed(host, port)
    try:
        client = CourseraClient(base_url=f"http://{host}:{port}")

        partners = client.list_partners()
        institutions = client.list_institutions()

        # Fetch enough catalog items for grounded tasks.
        all_courses: list[dict[str, Any]] = []
        offset = 0
        while True:
            page = client.list_courses(limit=100, offset=offset)
            items = page["items"]
            all_courses.extend(items)
            offset += len(items)
            if offset >= page["total"] or not items:
                break

        all_resources: list[dict[str, Any]] = []
        offset = 0
        while True:
            page = client.list_resources(limit=100, offset=offset)
            items = page["items"]
            all_resources.extend(items)
            offset += len(items)
            if offset >= page["total"] or not items:
                break

        # Deterministic-ish sampling for repeatability.
        random.seed(7)

        # Ensure we have enough.
        if len(all_courses) < 20:
            raise RuntimeError(f"Not enough courses to generate tasks: {len(all_courses)}")
        if len(all_resources) < 5:
            raise RuntimeError(f"Not enough resources to generate tasks: {len(all_resources)}")

        sampled_courses = random.sample(all_courses, k=min(30, len(all_courses)))
        sampled_resources = random.sample(all_resources, k=min(12, len(all_resources)))

        # Helper maps for more realistic prompts.
        partner_by_slug = {p["slug"]: p for p in partners}
        partner_slugs = [p["slug"] for p in partners]
        levels = sorted({c.get("level") for c in all_courses if c.get("level")})

        tasks: list[dict[str, Any]] = []

        def add_task(
            *,
            instruction: str,
            difficulty: str,
            judge: str,
            call_str: str,
            fn: Callable[[], Any],
        ) -> None:
            try:
                res = fn()
                tasks.append(
                    {
                        "instruction": instruction,
                        "python sdk tool call": call_str,
                        "tool call result": _safe_preview(res),
                        "is_valid": True,
                        "difficulty": difficulty,
                        "judge_for_webagent": judge,
                    }
                )
            except Exception as e:
                tasks.append(
                    {
                        "instruction": instruction,
                        "python sdk tool call": call_str,
                        "tool call result": {"error": str(e)},
                        "is_valid": False,
                        "difficulty": difficulty,
                        "judge_for_webagent": judge,
                    }
                )

        # -----------------------
        # EASY tasks (browse/search/list)
        # -----------------------
        add_task(
            instruction="Open the course catalog and tell me how many courses are available in total.",
            difficulty="easy",
            judge=_make_judge_url_contains("/courses") + ", " + _make_judge_answer_includes(str(client.list_courses(limit=1)["total"])),
            call_str='client.list_courses(limit=1)["total"]',
            fn=lambda: {"total": client.list_courses(limit=1)["total"]},
        )

        add_task(
            instruction="Go to the Resources section and tell me how many resources are listed in total.",
            difficulty="easy",
            judge=_make_judge_url_contains("/resources") + ", " + _make_judge_answer_includes(str(client.list_resources(limit=1)["total"])),
            call_str='client.list_resources(limit=1)["total"]',
            fn=lambda: {"total": client.list_resources(limit=1)["total"]},
        )

        add_task(
            instruction="On the Courses page, don’t type anything—just load the catalog and tell me the title of the first course card shown.",
            difficulty="easy",
            judge=_make_judge_url_contains("/courses") + ", " + _make_judge_answer_includes(client.list_courses(limit=1, offset=0)["items"][0]["title"]),
            call_str='client.list_courses(limit=1, offset=0)["items"][0]["title"]',
            fn=lambda: {"first_course_title": client.list_courses(limit=1, offset=0)["items"][0]["title"]},
        )

        # Search tasks grounded by actual titles/skills.
        for q in ["python", "data", "machine", "business", "excel", "ai"]:
            page = client.list_courses(q=q, limit=5)
            expected_total = page["total"]
            add_task(
                instruction=f'Go to the Courses page and search for "{q}". Tell me how many results you see.',
                difficulty="easy",
                judge=_make_judge_url_contains("/courses") + ", " + _make_judge_answer_includes(str(expected_total)),
                call_str=f'client.list_courses(q="{q}", limit=1)["total"]',
                fn=lambda q=q: {"query": q, "total": client.list_courses(q=q, limit=1)["total"]},
            )

        # Partner filter (easy) using the visible "Partner slug" field.
        if partner_slugs:
            pslug = partner_slugs[0]
            page = client.list_courses(partner=pslug, limit=3)
            add_task(
                instruction=(
                    'Go to the Courses page, enter the following into the "Partner slug (optional)" field: '
                    f'"{pslug}", then click Search. Tell me how many courses are shown in total.'
                ),
                difficulty="easy",
                judge=_make_judge_url_contains("/courses") + ", " + _make_judge_answer_includes(str(page["total"])),
                call_str=f'client.list_courses(partner="{pslug}", limit=1)["total"]',
                fn=lambda pslug=pslug: {"partner_slug": pslug, "total": client.list_courses(partner=pslug, limit=1)["total"]},
            )

        # Level filter (easy) using the level dropdown on the page.
        allowed_levels = {"Beginner", "Intermediate", "Advanced"}
        usable_levels = [lvl for lvl in levels if lvl in allowed_levels]
        if usable_levels:
            lvl = usable_levels[0]
            page = client.list_courses(level=lvl, limit=3)
            add_task(
                instruction=f'Go to the Courses page, set the level filter to "{lvl}", click Search, and tell me how many courses match that level.',
                difficulty="easy",
                judge=_make_judge_url_contains("/courses") + ", " + _make_judge_answer_includes(str(page["total"])),
                call_str=f'client.list_courses(level="{lvl}", limit=1)["total"]',
                fn=lambda lvl=lvl: {"level": lvl, "total": client.list_courses(level=lvl, limit=1)["total"]},
            )

        # -----------------------
        # MEDIUM tasks (multi-step: find specific item then extract fields)
        # -----------------------
        for c in sampled_courses[:18]:
            slug = c["slug"]
            title = c["title"]
            partner_name = c["partner_name"]

            detail = client.get_course(slug)
            level = detail.get("level") or ""
            language = detail.get("language") or ""
            duration = detail.get("duration_hours")

            add_task(
                instruction=(
                    f'Find the course "{title}" (offered by {partner_name}), open its detail page, '
                    "and tell me its level, language, and estimated duration in hours."
                ),
                difficulty="medium",
                judge=_make_judge_url_contains(f"/courses/{slug}")
                + ", "
                + _make_judge_answer_includes(str(level), str(language), str(duration)),
                call_str=f'client.get_course("{slug}")',
                fn=lambda slug=slug: {
                    "slug": slug,
                    "title": title,
                    "level": client.get_course(slug).get("level"),
                    "language": client.get_course(slug).get("language"),
                    "duration_hours": client.get_course(slug).get("duration_hours"),
                },
            )

        # Resource detail tasks (medium).
        for r in sampled_resources[:8]:
            slug = r["slug"]
            kind = r.get("kind") or ""
            detail = client.get_resource(slug)
            title = detail.get("title") or slug
            summary = (detail.get("summary") or "").strip()
            summary_snippet = " ".join(summary.split()[:6]).strip() if summary else ""

            add_task(
                instruction=f'Go to Resources, open the {kind} titled "{title}", and tell me the resource kind and the summary text shown on the page.',
                difficulty="medium",
                judge=_make_judge_url_contains(f"/resources/{slug}") + ", " + _make_judge_answer_includes(kind, summary_snippet) if summary_snippet else _make_judge_url_contains(f"/resources/{slug}") + ", " + _make_judge_answer_includes(kind),
                call_str=f'client.get_resource("{slug}")',
                fn=lambda slug=slug: {
                    "slug": slug,
                    "title": client.get_resource(slug).get("title"),
                    "summary": client.get_resource(slug).get("summary"),
                    "kind": client.get_resource(slug).get("kind"),
                },
            )

        # -----------------------
        # HARD tasks (longer sequences + stateful submissions)
        # -----------------------
        # Ebook lead form exists on a specific resource detail page in the UI.
        ebook_slug = "job-skills-of-2023-report"
        ebook_title = None
        try:
            ebook_title = client.get_resource(ebook_slug).get("title") or ebook_slug
        except Exception:
            ebook_title = ebook_slug

        # Prefer multiple distinct ebook submissions (long form + state change).
        for _ in range(6):
            work_email = f"alex.kim+{uuid.uuid4().hex[:6]}@example.edu"
            add_task(
                instruction=(
                    f'Go to Resources, open the ebook "{ebook_title}", and submit the ebook download form. '
                    "Use first name Alex, last name Kim, job title Program Manager, "
                    f'work email "{work_email}", institution name Example University, primary discipline Computer Science, '
                    'country "US", and consent to be contacted.'
                ),
                difficulty="hard",
                judge=_make_judge_url_contains(f"/resources/{ebook_slug}") + ", " + _make_judge_answer_includes("Submitted"),
                call_str=(
                    'client.submit_ebook_lead('
                    f'resource_slug="{ebook_slug}", first_name="Alex", last_name="Kim", job_title="Program Manager", '
                    f'work_email="{work_email}", work_phone="{_rand_phone_us()}", institution_name="Example University", '
                    'primary_discipline="Computer Science", country="US", consent_text="I agree to be contacted.")'
                ),
                fn=lambda ebook_slug=ebook_slug, work_email=work_email: client.submit_ebook_lead(
                    resource_slug=ebook_slug,
                    first_name="Alex",
                    last_name="Kim",
                    job_title="Program Manager",
                    work_email=work_email,
                    work_phone=_rand_phone_us(),
                    institution_name="Example University",
                    primary_discipline="Computer Science",
                    country="US",
                    consent_text="I agree to be contacted.",
                ),
            )

        # Contact form submissions (stateful).
        for i in range(4):
            email = f"jordan.lee+{uuid.uuid4().hex[:6]}@example.com"
            msg = "I’d like to learn more about Coursera for Campus pricing and implementation."
            add_task(
                instruction=(
                    "Go to the Contact page and submit the contact form. "
                    f'Use name "Jordan Lee", email "{email}", institution "Example Community College", '
                    f'and message "{msg}".'
                ),
                difficulty="hard",
                judge=_make_judge_url_contains("/contact") + ", " + _make_judge_answer_includes("Submitted"),
                call_str=(
                    f'client.submit_contact_lead(full_name="Jordan Lee", email="{email}", '
                    f'institution="Example Community College", message="{msg}")'
                ),
                fn=lambda email=email, msg=msg: client.submit_contact_lead(
                    full_name="Jordan Lee",
                    email=email,
                    institution="Example Community College",
                    message=msg,
                ),
            )

        # Pad with additional grounded medium/easy tasks to exactly 50.
        # Use remaining sampled courses for additional extraction tasks.
        for c in sampled_courses[18:30]:
            slug = c["slug"]
            title = c["title"]
            expected_partner = c["partner_name"]
            add_task(
                instruction=f'Open the course "{title}" and tell me which partner/organization offers it.',
                difficulty="easy",
                judge=_make_judge_url_contains(f"/courses/{slug}") + ", " + _make_judge_answer_includes(expected_partner),
                call_str=f'client.get_course("{slug}")["partner"]["name"]',
                fn=lambda slug=slug: {"slug": slug, "partner_name": client.get_course(slug)["partner"]["name"]},
            )

        # Ensure exactly 50 tasks.
        if len(tasks) < 50:
            # Add simple list calls until we hit 50.
            while len(tasks) < 50:
                add_task(
                    instruction="On the Courses page, load the catalog and tell me the title of the first course card shown.",
                    difficulty="easy",
                    judge=_make_judge_url_contains("/courses") + ", " + _make_judge_answer_includes(all_courses[0]["title"]),
                    call_str='client.list_courses(limit=1, offset=0)["items"][0]["title"]',
                    fn=lambda: {"first_course_title": client.list_courses(limit=1, offset=0)["items"][0]["title"]},
                )
        elif len(tasks) > 50:
            tasks = tasks[:50]

        OUT_PATH.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {len(tasks)} tasks to {OUT_PATH}")
    finally:
        _stop_backend(backend_handle)


if __name__ == "__main__":
    main()


from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable, Literal

from linkedin_clone_sdk import LinkedInCloneClient, LocalSqliteDb
from linkedin_clone_sdk.errors import ApiError


BASE_WEB_URL = "http://127.0.0.1:12078"
BASE_API_URL = "http://127.0.0.1:12079"

DEMO_EMAIL = "jane.doe@example.com"
DEMO_PASSWORD = "password123"
DB_PATH = "backend/var/app.db"

Difficulty = Literal["easy", "medium", "hard"]


def _jsonable(x: Any) -> Any:
    if isinstance(x, (datetime, date)):
        return x.isoformat()
    if isinstance(x, set):
        return sorted(list(x))
    if isinstance(x, bytes):
        return x.decode("utf-8", errors="replace")
    if isinstance(x, Exception):
        return {"type": type(x).__name__, "message": str(x)}
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x


def _client_logged_in() -> LinkedInCloneClient:
    c = LinkedInCloneClient(base_url=BASE_API_URL)
    c.login(DEMO_EMAIL, DEMO_PASSWORD)
    return c


def _db() -> LocalSqliteDb:
    return LocalSqliteDb(DB_PATH)


def _jane_user_id(db: LocalSqliteDb) -> str:
    return db.scalar("select id from users where email = ?", (DEMO_EMAIL,))  # type: ignore[return-value]


def _pick_recent_job_id(db: LocalSqliteDb, *, work_mode: str | None = None, promoted: bool | None = None) -> str:
    where = []
    params: list[Any] = []
    if work_mode is not None:
        where.append("j.work_mode = ?")
        params.append(work_mode)
    if promoted is not None:
        where.append("j.promoted = ?")
        params.append(1 if promoted else 0)
    where_sql = f"where {' and '.join(where)}" if where else ""
    row = db.rows(
        f"""
select j.id
from jobs j
{where_sql}
order by j.posted_at desc
limit 1
""",
        params,
    )
    if not row:
        raise RuntimeError("Could not find a matching job in seeded DB.")
    return row[0][0]


def _pick_recent_post_id(db: LocalSqliteDb) -> str:
    row = db.rows("select id from posts order by created_at desc limit 1")
    if not row:
        raise RuntimeError("No posts found in seeded DB.")
    return row[0][0]


@dataclass
class TaskSpec:
    instruction: str
    tool_call: str
    difficulty: Difficulty
    judge: dict[str, Any]
    run: Callable[[], Any]


def _mk_task(
    *,
    instruction: str,
    tool_call: str,
    difficulty: Difficulty,
    judge: dict[str, Any],
    run: Callable[[], Any],
) -> TaskSpec:
    return TaskSpec(instruction=instruction, tool_call=tool_call, difficulty=difficulty, judge=judge, run=run)


def build_tasks() -> list[TaskSpec]:
    db = _db()
    jane_id = _jane_user_id(db)

    remote_salary_job_id = db.scalar(
        """
select j.id
from jobs j
where j.work_mode='remote' and j.salary_min is not null
order by j.posted_at desc
limit 1
"""
    )
    if not remote_salary_job_id:
        remote_salary_job_id = _pick_recent_job_id(db, work_mode="remote")

    promoted_job_id = _pick_recent_job_id(db, promoted=True)
    newest_post_id = _pick_recent_post_id(db)

    # Use stable-ish tokens for created content.
    token_prefix = f"sdk-task-{int(time.time())}"
    token_a = f"{token_prefix}-{uuid.uuid4().hex[:8]}"
    token_b = f"{token_prefix}-{uuid.uuid4().hex[:8]}"
    token_c = f"{token_prefix}-{uuid.uuid4().hex[:8]}"

    tasks: list[TaskSpec] = []

    # --------------------
    # Easy (minimal actions; read-only where possible)
    # --------------------
    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in with email '{DEMO_EMAIL}' and password '{DEMO_PASSWORD}', "
                "then tell me my full name and the headline shown on my profile card."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "me = c.me()\n"
                "result = {'full_name': f\"{me['first_name']} {me['last_name']}\", 'headline': me['headline']}\n"
            ),
            difficulty="easy",
            judge={
                "approach": "rinfo",
                "reference_answer_from_tool_result": ["full_name", "headline"],
                "checks": ["must_include(answer, full_name)", "must_include(answer, headline)"],
            },
            run=lambda: (
                (lambda c: (lambda me: {"full_name": f"{me['first_name']} {me['last_name']}", "headline": me["headline"]})(
                    c.me()
                ))(_client_logged_in())
            ),
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"Go to {BASE_WEB_URL}, log in as '{DEMO_EMAIL}' with password '{DEMO_PASSWORD}', "
                "load the home feed, and tell me how many posts are returned if you only load 5 items."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "feed = c.feed(limit=5)\n"
                "result = {'count': len(feed['items'])}\n"
            ),
            difficulty="easy",
            judge={"approach": "rinfo", "reference_answer_from_tool_result": ["count"], "checks": ["exact_match(answer, str(count))"]},
            run=lambda: {"count": len(_client_logged_in().feed(limit=5)["items"])},
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                "and tell me the full name of the author of the newest post in my feed."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "post = c.feed(limit=1)['items'][0]\n"
                "a = post['author']\n"
                "result = {'author_full_name': f\"{a['first_name']} {a['last_name']}\"}\n"
            ),
            difficulty="easy",
            judge={
                "approach": "rinfo",
                "reference_answer_from_tool_result": ["author_full_name"],
                "checks": ["exact_match(answer, author_full_name)"],
            },
            run=lambda: (
                (lambda c: (lambda p: {"author_full_name": f"{p['author']['first_name']} {p['author']['last_name']}"})(
                    c.feed(limit=1)["items"][0]
                ))(_client_logged_in())
            ),
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"On {BASE_WEB_URL}, log in as '{DEMO_EMAIL}' with password '{DEMO_PASSWORD}'. "
                "Click the global search bar, type 'bio', and give me the first 5 typeahead suggestions in order."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "ta = c.typeahead('bio')\n"
                "result = {'suggestions': ta['suggestions'][:5]}\n"
            ),
            difficulty="easy",
            judge={
                "approach": "rinfo",
                "reference_answer_from_tool_result": ["suggestions"],
                "checks": ["must_include_all(answer, suggestions)"],
            },
            run=lambda: {"suggestions": _client_logged_in().typeahead("bio")["suggestions"][:5]},
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                "search for people using the keyword 'Jane', and tell me the total number of people results plus the first result's full name."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "resp = c.search_people('Jane', limit=5)\n"
                "first = resp['items'][0]\n"
                "result = {'total': resp['total'], 'first_full_name': f\"{first['first_name']} {first['last_name']}\"}\n"
            ),
            difficulty="easy",
            judge={
                "approach": "rinfo",
                "reference_answer_from_tool_result": ["total", "first_full_name"],
                "checks": ["must_include(answer, str(total))", "must_include(answer, first_full_name)"],
            },
            run=lambda: (
                (lambda c: (lambda r: {"total": r["total"], "first_full_name": f"{r['items'][0]['first_name']} {r['items'][0]['last_name']}"})(
                    c.search_people("Jane", limit=5)
                ))(_client_logged_in())
            ),
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"Go to {BASE_WEB_URL} and log in as '{DEMO_EMAIL}' with password '{DEMO_PASSWORD}'. "
                "Search posts for the keyword 'economy' and tell me the total results count and the author name of the newest matching post."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "resp = c.search_posts('economy', limit=1)\n"
                "item = resp['items'][0]\n"
                "a = item['author']\n"
                "result = {'total': resp['total'], 'newest_author': f\"{a['first_name']} {a['last_name']}\"}\n"
            ),
            difficulty="easy",
            judge={
                "approach": "rinfo",
                "reference_answer_from_tool_result": ["total", "newest_author"],
                "checks": ["must_include(answer, str(total))", "must_include(answer, newest_author)"],
            },
            run=lambda: (
                (lambda c: (lambda r: {"total": r["total"], "newest_author": f"{r['items'][0]['author']['first_name']} {r['items'][0]['author']['last_name']}"})(
                    c.search_posts("economy", limit=1)
                ))(_client_logged_in())
            ),
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                "search posts for 'office', and tell me (out of the first 5 results) how many have an image attached."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "resp = c.search_posts('office', limit=5)\n"
                "with_img = sum(1 for p in resp['items'] if p.get('image_url'))\n"
                "result = {'with_image_count': with_img, 'returned': len(resp['items'])}\n"
            ),
            difficulty="easy",
            judge={
                "approach": "rinfo",
                "reference_answer_from_tool_result": ["with_image_count", "returned"],
                "checks": ["must_include(answer, str(with_image_count))", "must_include(answer, str(returned))"],
            },
            run=lambda: (
                (lambda c: (lambda r: {"with_image_count": sum(1 for p in r["items"] if p.get("image_url")), "returned": len(r["items"])})(
                    c.search_posts("office", limit=5)
                ))(_client_logged_in())
            ),
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"On {BASE_WEB_URL}, log in as '{DEMO_EMAIL}' with password '{DEMO_PASSWORD}'. "
                "Go to Jobs and search for 'Data Scientist' in location 'United States'. Tell me the total number of matching jobs."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "resp = c.search_jobs(query='Data Scientist', location='United States', limit=1)\n"
                "result = {'total': resp['total']}\n"
            ),
            difficulty="easy",
            judge={"approach": "rinfo", "reference_answer_from_tool_result": ["total"], "checks": ["exact_match(answer, str(total))"]},
            run=lambda: {"total": _client_logged_in().search_jobs(query="Data Scientist", location="United States", limit=1)["total"]},
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                "search for remote jobs using keyword 'Machine Learning', then open the first job and tell me its company name."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "resp = c.search_jobs(query='Machine Learning', work_mode=['remote'], limit=1)\n"
                "job_id = resp['items'][0]['id']\n"
                "job = c.get_job(job_id)\n"
                "result = {'company': job['company']['name'], 'title': job['title']}\n"
            ),
            difficulty="easy",
            judge={"approach": "rinfo", "reference_answer_from_tool_result": ["company", "title"], "checks": ["must_include(answer, company)"]},
            run=lambda: (
                (lambda c: (lambda r: (lambda j: {"company": j["company"]["name"], "title": j["title"]})(c.get_job(r["items"][0]["id"])))(
                    c.search_jobs(query="Machine Learning", work_mode=["remote"], limit=1)
                ))(_client_logged_in())
            ),
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"Go to {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                "open the newest post in the feed, and tell me how many comments it has."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "post = c.feed(limit=1)['items'][0]\n"
                "result = {'comments_count': post['comments_count'], 'post_id': post['id']}\n"
            ),
            difficulty="easy",
            judge={"approach": "rinfo", "reference_answer_from_tool_result": ["comments_count"], "checks": ["exact_match(answer, str(comments_count))"]},
            run=lambda: (
                (lambda c: (lambda p: {"comments_count": p["comments_count"], "post_id": p["id"]})(c.feed(limit=1)["items"][0]))(
                    _client_logged_in()
                )
            ),
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"On {BASE_WEB_URL}, log in as '{DEMO_EMAIL}' with password '{DEMO_PASSWORD}'. "
                "Open the newest post in the feed, view its comments, and tell me the full name of the person who wrote the first comment."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "post_id = c.feed(limit=1)['items'][0]['id']\n"
                "comments = c.list_comments(post_id)\n"
                "a = comments[0]['author']\n"
                "result = {'first_comment_author': f\"{a['first_name']} {a['last_name']}\", 'comments_count': len(comments)}\n"
            ),
            difficulty="easy",
            judge={
                "approach": "rinfo",
                "reference_answer_from_tool_result": ["first_comment_author"],
                "checks": ["exact_match(answer, first_comment_author)"],
            },
            run=lambda: (
                (lambda c: (lambda post_id: (lambda cs: {"first_comment_author": f"{cs[0]['author']['first_name']} {cs[0]['author']['last_name']}", "comments_count": len(cs)})(
                    c.list_comments(post_id)
                ))(c.feed(limit=1)["items"][0]["id"]))(_client_logged_in())
            ),
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                "then check my Jobs alerts page and tell me how many job alerts I currently have."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "alerts = c.list_job_alerts()\n"
                "result = {'alerts_count': len(alerts)}\n"
            ),
            difficulty="easy",
            judge={"approach": "rinfo", "reference_answer_from_tool_result": ["alerts_count"], "checks": ["exact_match(answer, str(alerts_count))"]},
            run=lambda: {"alerts_count": len(_client_logged_in().list_job_alerts())},
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"On {BASE_WEB_URL}, log in as '{DEMO_EMAIL}' with password '{DEMO_PASSWORD}'. "
                "Go to Jobs, open a promoted job (if you see one), and tell me its title and whether it is marked as promoted."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                "from linkedin_clone_sdk import LocalSqliteDb\n"
                f"db = LocalSqliteDb('{DB_PATH}')\n"
                "job_id = db.scalar(\"select id from jobs where promoted=1 order by posted_at desc limit 1\")\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "job = c.get_job(job_id)\n"
                "result = {'title': job['title'], 'promoted': job['promoted']}\n"
            ),
            difficulty="easy",
            judge={"approach": "rinfo", "reference_answer_from_tool_result": ["title", "promoted"], "checks": ["must_include(answer, title)", "must_include(answer, str(promoted))"]},
            run=lambda: (lambda c: (lambda j: {"title": j["title"], "promoted": j["promoted"]})(c.get_job(promoted_job_id)))(_client_logged_in()),
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                "find a remote job that has a salary range, open it, and tell me the salary_min and salary_max values."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                "from linkedin_clone_sdk import LocalSqliteDb\n"
                f"db = LocalSqliteDb('{DB_PATH}')\n"
                "job_id = db.scalar(\"select id from jobs where work_mode='remote' and salary_min is not null order by posted_at desc limit 1\")\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "job = c.get_job(job_id)\n"
                "result = {'title': job['title'], 'salary_min': job['salary_min'], 'salary_max': job['salary_max'], 'currency': job['salary_currency']}\n"
            ),
            difficulty="easy",
            judge={
                "approach": "rinfo",
                "reference_answer_from_tool_result": ["salary_min", "salary_max", "currency"],
                "checks": ["must_include(answer, str(salary_min))", "must_include(answer, str(salary_max))", "must_include(answer, currency)"],
            },
            run=lambda: (lambda c: (lambda j: {"title": j["title"], "salary_min": j["salary_min"], "salary_max": j["salary_max"], "currency": j["salary_currency"]})(c.get_job(str(remote_salary_job_id))))(_client_logged_in()),
        )
    )

    # --------------------
    # Medium (multi-step navigation or small state changes)
    # --------------------
    tasks.append(
        _mk_task(
            instruction=(
                f"Go to {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                "load 5 posts in the feed, then load the next 5 older posts, and tell me whether there is any overlap in post IDs."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "p1 = c.feed(limit=5)\n"
                "ids1 = [p['id'] for p in p1['items']]\n"
                "p2 = c.feed(limit=5, cursor=p1.get('next_cursor'))\n"
                "ids2 = [p['id'] for p in p2['items']]\n"
                "result = {'overlap': len(set(ids1) & set(ids2)) > 0, 'ids1': ids1, 'ids2': ids2}\n"
            ),
            difficulty="medium",
            judge={
                "approach": "rinfo",
                "reference_answer_from_tool_result": ["overlap"],
                "checks": ["exact_match(answer, str(overlap))"],
            },
            run=lambda: (
                (lambda c: (lambda p1: (lambda p2: {"overlap": bool(set([p["id"] for p in p1["items"]]) & set([p["id"] for p in p2["items"]])),
                                                 "ids1": [p["id"] for p in p1["items"]],
                                                 "ids2": [p["id"] for p in p2["items"]]})(
                    c.feed(limit=5, cursor=p1.get("next_cursor"))
                ))(c.feed(limit=5)))(_client_logged_in())
            ),
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"On {BASE_WEB_URL}, log in as '{DEMO_EMAIL}' with password '{DEMO_PASSWORD}'. "
                "Like the newest post in the feed (if it isn't already liked), verify it's liked, then unlike it again so you don't leave it liked."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "post = c.feed(limit=1)['items'][0]\n"
                "post_id = post['id']\n"
                "# Ensure liked\n"
                "if not post['viewer_has_liked']:\n"
                "    c.toggle_like(post_id)\n"
                "# Verify\n"
                "post2 = c.feed(limit=1)['items'][0]\n"
                "liked_now = post2['viewer_has_liked']\n"
                "# Cleanup (unlike)\n"
                "if liked_now:\n"
                "    c.toggle_like(post_id)\n"
                "post3 = c.feed(limit=1)['items'][0]\n"
                "result = {'verified_liked': liked_now, 'final_liked': post3['viewer_has_liked'], 'post_id': post_id}\n"
            ),
            difficulty="medium",
            judge={
                "approach": "rprog",
                "checks": [
                    "verified_liked is True",
                    "final_liked is False",
                ],
            },
            run=lambda: _run_like_cleanup(),
        )
    )

    # The like/unlike task above uses a compact lambda; re-implement robustly for correctness in run().
    def _run_like_cleanup() -> dict[str, Any]:
        c = _client_logged_in()
        post = c.feed(limit=1)["items"][0]
        post_id = post["id"]
        if not post["viewer_has_liked"]:
            c.toggle_like(post_id)
        verified = c.feed(limit=1)["items"][0]["viewer_has_liked"]
        if verified:
            c.toggle_like(post_id)
        final = c.feed(limit=1)["items"][0]["viewer_has_liked"]
        return {"verified_liked": verified, "final_liked": final, "post_id": post_id}

    def _run_add_comment(token: str) -> dict[str, Any]:
        c = _client_logged_in()
        post_id = c.feed(limit=1)["items"][0]["id"]
        comment_body = f"Great post — {token}"
        created = c.add_comment(post_id, body=comment_body)
        comments = c.list_comments(post_id)
        found = any(cm["body"] == comment_body for cm in comments)
        return {"post_id": post_id, "comment_id": created["id"], "found": found, "comment_body": comment_body, "comments_count": len(comments)}

    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                f"open the newest post in the feed and add a comment that says: 'Great post — {token_a}'. "
                "After posting, confirm that your comment appears in the comment list."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "post_id = c.feed(limit=1)['items'][0]['id']\n"
                f"comment_body = \"Great post — {token_a}\"\n"
                "created = c.add_comment(post_id, body=comment_body)\n"
                "comments = c.list_comments(post_id)\n"
                "result = {'post_id': post_id, 'comment_id': created['id'], 'found': any(cm['body']==comment_body for cm in comments)}\n"
            ),
            difficulty="medium",
            judge={
                "approach": "rprog",
                "checks": ["found is True"],
                "notes": "Judge can verify via API list_comments().",
            },
            run=lambda: _run_add_comment(token_a),
        )
    )

    def _run_save_unsave_job() -> dict[str, Any]:
        c = _client_logged_in()
        resp = c.search_jobs(query="Bioinformatics", location="United States", limit=1)
        job_id = resp["items"][0]["id"]
        c.save_job(job_id)
        j1 = c.get_job(job_id)
        c.unsave_job(job_id)
        j2 = c.get_job(job_id)
        return {"job_id": job_id, "saved_after_save": j1["viewer_saved"], "saved_after_unsave": j2["viewer_saved"], "title": j2["title"]}

    tasks.append(
        _mk_task(
            instruction=(
                f"On {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}'. "
                "Go to Jobs and search 'Bioinformatics' in 'United States'. Save the first job in the results, verify it shows as saved, "
                "then unsave it again."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "resp = c.search_jobs(query='Bioinformatics', location='United States', limit=1)\n"
                "job_id = resp['items'][0]['id']\n"
                "c.save_job(job_id)\n"
                "saved1 = c.get_job(job_id)['viewer_saved']\n"
                "c.unsave_job(job_id)\n"
                "saved2 = c.get_job(job_id)['viewer_saved']\n"
                "result = {'job_id': job_id, 'saved_after_save': saved1, 'saved_after_unsave': saved2}\n"
            ),
            difficulty="medium",
            judge={"approach": "rprog", "checks": ["saved_after_save is True", "saved_after_unsave is False"]},
            run=_run_save_unsave_job,
        )
    )

    def _run_apply_job() -> dict[str, Any]:
        c = _client_logged_in()
        resp = c.search_jobs(query="Bioinformatics", location="United States", limit=1)
        job_id = resp["items"][0]["id"]
        c.apply_job(job_id)
        job = c.get_job(job_id)
        return {"job_id": job_id, "viewer_applied": job["viewer_applied"], "title": job["title"], "company": job["company"]["name"]}

    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in as '{DEMO_EMAIL}' with password '{DEMO_PASSWORD}'. "
                "Go to Jobs, search for 'Bioinformatics' in 'United States', open the first job, click Apply, and confirm the job shows as applied."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "job_id = c.search_jobs(query='Bioinformatics', location='United States', limit=1)['items'][0]['id']\n"
                "c.apply_job(job_id)\n"
                "job = c.get_job(job_id)\n"
                "result = {'job_id': job_id, 'viewer_applied': job['viewer_applied']}\n"
            ),
            difficulty="medium",
            judge={"approach": "rprog", "checks": ["viewer_applied is True"]},
            run=_run_apply_job,
        )
    )

    def _run_toggle_alert(query: str, location: str, enabled: bool) -> dict[str, Any]:
        c = _client_logged_in()
        out = c.toggle_job_alert(query=query, location=location, enabled=enabled)
        alerts = c.list_job_alerts()
        match = [a for a in alerts if a["query"] == query and a["location"] == location]
        return {"toggle_result": out, "found": len(match) == 1, "enabled": match[0]["enabled"] if match else None}

    tasks.append(
        _mk_task(
            instruction=(
                f"On {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}'. "
                "Go to Jobs and turn ON a job alert for query 'bioinformatician' in location 'United States'. "
                "Then check your alerts list and confirm it's enabled."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "c.toggle_job_alert(query='bioinformatician', location='United States', enabled=True)\n"
                "alerts = c.list_job_alerts()\n"
                "match = [a for a in alerts if a['query']=='bioinformatician' and a['location']=='United States']\n"
                "result = {'found': len(match)==1, 'enabled': match[0]['enabled'] if match else None}\n"
            ),
            difficulty="medium",
            judge={"approach": "rprog", "checks": ["found is True", "enabled is True"]},
            run=lambda: _run_toggle_alert("bioinformatician", "United States", True),
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}'. "
                "Go to Jobs and turn OFF the job alert for query 'bioinformatician' in location 'United States', then confirm it's disabled in your alerts list."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "c.toggle_job_alert(query='bioinformatician', location='United States', enabled=False)\n"
                "alerts = c.list_job_alerts()\n"
                "match = [a for a in alerts if a['query']=='bioinformatician' and a['location']=='United States']\n"
                "result = {'found': len(match)==1, 'enabled': match[0]['enabled'] if match else None}\n"
            ),
            difficulty="medium",
            judge={"approach": "rprog", "checks": ["found is True", "enabled is False"]},
            run=lambda: _run_toggle_alert("bioinformatician", "United States", False),
        )
    )

    def _run_jobs_filters() -> dict[str, Any]:
        c = _client_logged_in()
        resp = c.search_jobs(query="", location="", work_mode=["remote"], experience_level=["entry"], date_posted_days=14, limit=10)
        return {"total": resp["total"], "returned": len(resp["items"]), "first_title": resp["items"][0]["title"] if resp["items"] else None}

    tasks.append(
        _mk_task(
            instruction=(
                f"On {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}'. "
                "In Jobs, filter for Remote + Entry level roles posted in the last 14 days. "
                "Tell me the total matching jobs and the title of the first result."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "resp = c.search_jobs(work_mode=['remote'], experience_level=['entry'], date_posted_days=14, limit=10)\n"
                "result = {'total': resp['total'], 'first_title': resp['items'][0]['title'] if resp['items'] else None}\n"
            ),
            difficulty="medium",
            judge={"approach": "rinfo", "reference_answer_from_tool_result": ["total", "first_title"], "checks": ["must_include(answer, str(total))", "must_include(answer, first_title)"]},
            run=_run_jobs_filters,
        )
    )

    def _run_open_job_and_skills(job_id: str) -> dict[str, Any]:
        c = _client_logged_in()
        j = c.get_job(job_id)
        return {"job_id": job_id, "title": j["title"], "skills_sample": j["skills"][:5], "skills_count": len(j["skills"])}

    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                "open a promoted job posting, and list the first 5 skills shown in its job details."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient, LocalSqliteDb\n"
                f"db = LocalSqliteDb('{DB_PATH}')\n"
                "job_id = db.scalar(\"select id from jobs where promoted=1 order by posted_at desc limit 1\")\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "job = c.get_job(job_id)\n"
                "result = {'skills': job['skills'][:5], 'title': job['title']}\n"
            ),
            difficulty="medium",
            judge={"approach": "rinfo", "reference_answer_from_tool_result": ["skills"], "checks": ["must_include_all(answer, skills)"]},
            run=lambda: _run_open_job_and_skills(promoted_job_id),
        )
    )

    # --------------------
    # Hard (longer sequences, multi-step stateful updates)
    # --------------------
    def _run_create_post(body: str, image_url: str) -> dict[str, Any]:
        c = _client_logged_in()
        created = c.create_post(body=body, image_url=image_url)
        found = c.search_posts(body.split()[-1], limit=5)
        hit = any(p["id"] == created["id"] for p in found["items"])
        return {"post_id": created["id"], "created_body": created["body"], "image_url": created["image_url"], "search_hit": hit}

    post_body_1 = f"Sharing a quick update for the day — {token_b}"
    post_body_2 = f"Posting a photo link to test the composer — {token_c}"

    tasks.append(
        _mk_task(
            instruction=(
                f"Go to {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                f"create a new post with the exact text: '{post_body_1}'. Then use search to find that post and confirm it appears."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                f"created = c.create_post(body={post_body_1!r}, image_url='')\n"
                f"found = c.search_posts({token_b!r}, limit=5)\n"
                "result = {'post_id': created['id'], 'search_hit': any(p['id']==created['id'] for p in found['items'])}\n"
            ),
            difficulty="hard",
            judge={"approach": "rprog", "checks": ["search_hit is True"]},
            run=lambda: _run_create_post(post_body_1, ""),
        )
    )

    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in as '{DEMO_EMAIL}' with password '{DEMO_PASSWORD}'. "
                f"Create a new post that includes an image URL and uses this exact text: '{post_body_2}'. "
                "After posting, verify the post has a non-empty image preview (image URL stored)."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "img = 'https://images.unsplash.com/random/1200x700?sig=99999&office'\n"
                f"created = c.create_post(body={post_body_2!r}, image_url=img)\n"
                "result = {'post_id': created['id'], 'image_url': created.get('image_url','')}\n"
            ),
            difficulty="hard",
            judge={"approach": "rprog", "checks": ["bool(image_url) is True"]},
            run=lambda: _run_create_post(post_body_2, "https://images.unsplash.com/random/1200x700?sig=99999&office"),
        )
    )

    def _run_post_like_comment_roundtrip(job_or_post: str = "post") -> dict[str, Any]:
        c = _client_logged_in()
        created = c.create_post(body=f"End-to-end interaction check — {uuid.uuid4().hex[:8]}", image_url="")
        post_id = created["id"]
        like_out = c.toggle_like(post_id)
        cm_body = f"Commenting on my own post — {uuid.uuid4().hex[:8]}"
        cm = c.add_comment(post_id, body=cm_body)
        # Verify via feed and comments endpoints
        feed_items = c.feed(limit=10)["items"]
        in_feed = next((p for p in feed_items if p["id"] == post_id), None)
        comments = c.list_comments(post_id)
        comment_found = any(x["id"] == cm["id"] and x["body"] == cm_body for x in comments)
        # Cleanup like
        if like_out.get("liked"):
            c.toggle_like(post_id)
        in_feed_after = next((p for p in c.feed(limit=10)["items"] if p["id"] == post_id), None)
        return {
            "post_id": post_id,
            "liked_verified": bool(in_feed and in_feed["viewer_has_liked"]),
            "comment_found": comment_found,
            "final_liked": bool(in_feed_after and in_feed_after["viewer_has_liked"]),
        }

    tasks.append(
        _mk_task(
            instruction=(
                f"Go to {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                "create a new text-only post, like it, add a short comment to it, verify both actions succeeded, then unlike it at the end."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                "import uuid\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "created = c.create_post(body=f\"End-to-end interaction check — {uuid.uuid4().hex[:8]}\", image_url='')\n"
                "post_id = created['id']\n"
                "c.toggle_like(post_id)\n"
                "cm_body = f\"Commenting on my own post — {uuid.uuid4().hex[:8]}\"\n"
                "cm = c.add_comment(post_id, body=cm_body)\n"
                "in_feed = next((p for p in c.feed(limit=10)['items'] if p['id']==post_id), None)\n"
                "comments = c.list_comments(post_id)\n"
                "comment_found = any(x['id']==cm['id'] and x['body']==cm_body for x in comments)\n"
                "# cleanup unlike\n"
                "c.toggle_like(post_id)\n"
                "in_feed2 = next((p for p in c.feed(limit=10)['items'] if p['id']==post_id), None)\n"
                "result = {'liked_verified': bool(in_feed and in_feed['viewer_has_liked']), 'comment_found': comment_found, 'final_liked': bool(in_feed2 and in_feed2['viewer_has_liked'])}\n"
            ),
            difficulty="hard",
            judge={"approach": "rprog", "checks": ["liked_verified is True", "comment_found is True", "final_liked is False"]},
            run=_run_post_like_comment_roundtrip,
        )
    )

    def _run_save_apply_verify() -> dict[str, Any]:
        c = _client_logged_in()
        # Prefer a remote salary job for realism.
        job_id = str(remote_salary_job_id)
        c.save_job(job_id)
        c.apply_job(job_id)
        job = c.get_job(job_id)
        # Cleanup saved state (leave application as-is; app is idempotent)
        c.unsave_job(job_id)
        job2 = c.get_job(job_id)
        return {
            "job_id": job_id,
            "viewer_saved_after_actions": job["viewer_saved"],
            "viewer_applied_after_actions": job["viewer_applied"],
            "viewer_saved_after_cleanup": job2["viewer_saved"],
        }

    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                "find a remote job with a salary range, save it, apply to it, verify both states (saved + applied), then unsave it at the end."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient, LocalSqliteDb\n"
                f"db = LocalSqliteDb('{DB_PATH}')\n"
                "job_id = db.scalar(\"select id from jobs where work_mode='remote' and salary_min is not null order by posted_at desc limit 1\")\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "c.save_job(job_id)\n"
                "c.apply_job(job_id)\n"
                "job = c.get_job(job_id)\n"
                "c.unsave_job(job_id)\n"
                "job2 = c.get_job(job_id)\n"
                "result = {'saved': job['viewer_saved'], 'applied': job['viewer_applied'], 'saved_after_cleanup': job2['viewer_saved']}\n"
            ),
            difficulty="hard",
            judge={"approach": "rprog", "checks": ["saved is True", "applied is True", "saved_after_cleanup is False"]},
            run=_run_save_apply_verify,
        )
    )

    def _run_logout_unauthorized() -> dict[str, Any]:
        c = _client_logged_in()
        out = c.logout()
        unauthorized = False
        try:
            _ = c.me()
        except ApiError as e:
            unauthorized = e.status_code == 401
        return {"logout_ok": out.get("ok") is True, "me_after_logout_unauthorized": unauthorized}

    tasks.append(
        _mk_task(
            instruction=(
                f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', then log out. "
                "After logging out, try to access the feed page again and confirm you are blocked or prompted to log in."
            ),
            tool_call=(
                "from linkedin_clone_sdk import LinkedInCloneClient\n"
                "from linkedin_clone_sdk.errors import ApiError\n"
                f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                "c.logout()\n"
                "unauthorized = False\n"
                "try:\n"
                "    c.feed(limit=1)\n"
                "except ApiError as e:\n"
                "    unauthorized = (e.status_code == 401)\n"
                "result = {'me_after_logout_unauthorized': unauthorized}\n"
            ),
            difficulty="hard",
            judge={"approach": "rprog", "checks": ["me_after_logout_unauthorized is True"]},
            run=_run_logout_unauthorized,
        )
    )

    # Fill up to 50 with additional realistic, validated API-backed tasks.
    def _add_more_tasks_until_50() -> None:
        nonlocal tasks

        def add_read_task(q: str) -> None:
            tasks.append(
                _mk_task(
                    instruction=(
                        f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                        f"use the search bar to search posts for '{q}', and tell me the total results count and the first author's full name."
                    ),
                    tool_call=(
                        "from linkedin_clone_sdk import LinkedInCloneClient\n"
                        f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                        f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                        f"resp = c.search_posts({q!r}, limit=1)\n"
                        "a = resp['items'][0]['author']\n"
                        "result = {'total': resp['total'], 'first_author': f\"{a['first_name']} {a['last_name']}\"}\n"
                    ),
                    difficulty="easy",
                    judge={
                        "approach": "rinfo",
                        "reference_answer_from_tool_result": ["total", "first_author"],
                        "checks": ["must_include(answer, str(total))", "must_include(answer, first_author)"],
                    },
                    run=lambda q=q: (
                        (lambda c: (lambda r: {"total": r["total"], "first_author": f"{r['items'][0]['author']['first_name']} {r['items'][0]['author']['last_name']}"})(
                            c.search_posts(q, limit=1)
                        ))(_client_logged_in())
                    ),
                )
            )

        # A few more info tasks
        for q in ["economy", "office", "security", "the"]:
            add_read_task(q)

        # More jobs browsing tasks with different filters
        def add_jobs_task(**kwargs: Any) -> None:
            query = kwargs.get("query", "")
            location = kwargs.get("location", "")
            work_mode = kwargs.get("work_mode")
            employment_type = kwargs.get("employment_type")
            experience_level = kwargs.get("experience_level")
            date_posted_days = kwargs.get("date_posted_days")

            tasks.append(
                _mk_task(
                    instruction=(
                        f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', go to Jobs, "
                        f"search with keyword '{query}' and location '{location}'. "
                        f"Apply filters for work mode {work_mode or 'any'}, employment type {employment_type or 'any'}, "
                        f"experience level {experience_level or 'any'}, and date posted {date_posted_days or 'any'}. "
                        "Tell me the total matches and the first job title + company."
                    ),
                    tool_call=(
                        "from linkedin_clone_sdk import LinkedInCloneClient\n"
                        f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                        f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                        f"resp = c.search_jobs(query={query!r}, location={location!r}, work_mode={work_mode!r}, employment_type={employment_type!r}, experience_level={experience_level!r}, date_posted_days={date_posted_days!r}, limit=1)\n"
                        "first = resp['items'][0]\n"
                        "result = {'total': resp['total'], 'first_title': first['title'], 'first_company': first['company']['name']}\n"
                    ),
                    difficulty="medium",
                    judge={
                        "approach": "rinfo",
                        "reference_answer_from_tool_result": ["total", "first_title", "first_company"],
                        "checks": ["must_include(answer, str(total))", "must_include(answer, first_title)", "must_include(answer, first_company)"],
                    },
                    run=lambda kwargs=kwargs: (
                        (lambda c: (lambda r: {"total": r["total"], "first_title": r["items"][0]["title"], "first_company": r["items"][0]["company"]["name"]})(
                            c.search_jobs(
                                query=kwargs.get("query", ""),
                                location=kwargs.get("location", ""),
                                work_mode=kwargs.get("work_mode"),
                                employment_type=kwargs.get("employment_type"),
                                experience_level=kwargs.get("experience_level"),
                                date_posted_days=kwargs.get("date_posted_days"),
                                limit=1,
                            )
                        ))(_client_logged_in())
                    ),
                )
            )

        add_jobs_task(query="Bioinformatics", location="United States", work_mode=["remote"], date_posted_days=14)
        add_jobs_task(query="Data Scientist", location="", work_mode=["hybrid"], experience_level=["mid"])
        # Avoid over-filtering to zero results; keep this broad but realistic.
        add_jobs_task(query="Security Engineer", location="Boston", date_posted_days=14)
        add_jobs_task(query="Product Manager", location="", experience_level=["senior"])
        add_jobs_task(query="", location="San Francisco", work_mode=["onsite"])

        # More stateful tasks: toggle alerts for different query/location pairs
        def add_alert_toggle_task(query: str, location: str) -> None:
            tasks.append(
                _mk_task(
                    instruction=(
                        f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', go to Jobs, "
                        f"turn ON a job alert for query '{query}' in location '{location}', confirm it appears in your alerts list, "
                        "then turn it OFF and confirm it's disabled."
                    ),
                    tool_call=(
                        "from linkedin_clone_sdk import LinkedInCloneClient\n"
                        f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                        f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                        f"c.toggle_job_alert(query={query!r}, location={location!r}, enabled=True)\n"
                        "alerts1 = c.list_job_alerts()\n"
                        f"m1 = [a for a in alerts1 if a['query']=={query!r} and a['location']=={location!r}]\n"
                        f"c.toggle_job_alert(query={query!r}, location={location!r}, enabled=False)\n"
                        "alerts2 = c.list_job_alerts()\n"
                        f"m2 = [a for a in alerts2 if a['query']=={query!r} and a['location']=={location!r}]\n"
                        "result = {'enabled_after_on': m1[0]['enabled'] if m1 else None, 'enabled_after_off': m2[0]['enabled'] if m2 else None}\n"
                    ),
                    difficulty="hard",
                    judge={"approach": "rprog", "checks": ["enabled_after_on is True", "enabled_after_off is False"]},
                    run=lambda query=query, location=location: (
                        (lambda on: (lambda off: {"enabled_after_on": on["enabled"], "enabled_after_off": off["enabled"]})(
                            _run_toggle_alert(query, location, False)
                        ))(_run_toggle_alert(query, location, True))
                    ),
                )
            )

        add_alert_toggle_task("data scientist", "United States")
        add_alert_toggle_task("machine learning engineer", "San Francisco Bay Area")

        # More feed tasks: list comments count, ensure list_comments is consistent
        def add_comments_consistency_task() -> None:
            tasks.append(
                _mk_task(
                    instruction=(
                        f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                        "open the newest feed post, then compare the displayed comment count vs. the number of comments in the comments list. "
                        "Tell me both numbers."
                    ),
                    tool_call=(
                        "from linkedin_clone_sdk import LinkedInCloneClient\n"
                        f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                        f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                        "post = c.feed(limit=1)['items'][0]\n"
                        "comments = c.list_comments(post['id'])\n"
                        "result = {'comments_count_field': post['comments_count'], 'comments_list_len': len(comments)}\n"
                    ),
                    difficulty="medium",
                    judge={
                        "approach": "rinfo",
                        "reference_answer_from_tool_result": ["comments_count_field", "comments_list_len"],
                        "checks": ["must_include(answer, str(comments_count_field))", "must_include(answer, str(comments_list_len))"],
                    },
                    run=lambda: (
                        (lambda c: (lambda p: (lambda cs: {"comments_count_field": p["comments_count"], "comments_list_len": len(cs)})(
                            c.list_comments(p["id"])
                        ))(c.feed(limit=1)["items"][0]))(_client_logged_in())
                    ),
                )
            )

        add_comments_consistency_task()

        # Avoid refresh(): backend currently returns 500. Use jobs pagination instead.
        def add_jobs_pagination_task() -> None:
            tasks.append(
                _mk_task(
                    instruction=(
                        f"Go to {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                        "go to Jobs, search for jobs in 'United States' with an empty keyword, then load 3 results and load the next 3 results. "
                        "Tell me whether any job IDs overlap between the two pages."
                    ),
                    tool_call=(
                        "from linkedin_clone_sdk import LinkedInCloneClient\n"
                        f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                        f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                        "p1 = c.search_jobs(query='', location='United States', limit=3, offset=0)\n"
                        "p2 = c.search_jobs(query='', location='United States', limit=3, offset=3)\n"
                        "ids1 = [j['id'] for j in p1['items']]\n"
                        "ids2 = [j['id'] for j in p2['items']]\n"
                        "result = {'overlap': len(set(ids1) & set(ids2)) > 0, 'ids1': ids1, 'ids2': ids2}\n"
                    ),
                    difficulty="medium",
                    judge={"approach": "rinfo", "reference_answer_from_tool_result": ["overlap"], "checks": ["exact_match(answer, str(overlap))"]},
                    run=lambda: (
                        (lambda c: (lambda p1: (lambda p2: {
                            "overlap": bool(set([j["id"] for j in p1["items"]]) & set([j["id"] for j in p2["items"]])),
                            "ids1": [j["id"] for j in p1["items"]],
                            "ids2": [j["id"] for j in p2["items"]],
                        })(
                            c.search_jobs(query="", location="United States", limit=3, offset=3)
                        ))(c.search_jobs(query="", location="United States", limit=3, offset=0)))(_client_logged_in())
                    ),
                )
            )

        add_jobs_pagination_task()

    _add_more_tasks_until_50()

    # If we still aren't at 50, add additional validated "people search" tasks.
    while len(tasks) < 50:
        suffix = len(tasks) + 1
        q = "Scientist" if suffix % 2 == 0 else "Engineer"
        tasks.append(
            _mk_task(
                instruction=(
                    f"Open {BASE_WEB_URL}, log in with '{DEMO_EMAIL}' / '{DEMO_PASSWORD}', "
                    f"search for people using the keyword '{q}', and tell me the total number of results and the first person's headline."
                ),
                tool_call=(
                    "from linkedin_clone_sdk import LinkedInCloneClient\n"
                    f"c = LinkedInCloneClient(base_url='{BASE_API_URL}')\n"
                    f"c.login('{DEMO_EMAIL}', '{DEMO_PASSWORD}')\n"
                    f"resp = c.search_people({q!r}, limit=1)\n"
                    "first = resp['items'][0]\n"
                    "result = {'total': resp['total'], 'headline': first.get('headline','')}\n"
                ),
                difficulty="easy" if len(tasks) % 3 == 0 else "medium",
                judge={
                    "approach": "rinfo",
                    "reference_answer_from_tool_result": ["total", "headline"],
                    "checks": ["must_include(answer, str(total))", "must_include(answer, headline)"],
                },
                run=lambda q=q: (
                    (lambda c: (lambda r: {"total": r["total"], "headline": r["items"][0].get("headline", "")})(c.search_people(q, limit=1)))(
                        _client_logged_in()
                    )
                ),
            )
        )

    # Trim (shouldn't happen, but guard anyway).
    return tasks[:50]


def main() -> None:
    specs = build_tasks()
    out: list[dict[str, Any]] = []

    for spec in specs:
        item: dict[str, Any] = {
            "instruction": spec.instruction,
            "python sdk tool call": spec.tool_call,
            "tool call result": None,
            "is_valid": False,
            "difficulty": spec.difficulty,
            "judge_for_webagent": spec.judge,
        }
        try:
            result = spec.run()
            item["tool call result"] = _jsonable(result)
            item["is_valid"] = True
        except Exception as e:
            item["tool call result"] = _jsonable(e)
            item["is_valid"] = False
        out.append(item)

    with open("task_instructions.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(out)} tasks to task_instructions.json")
    invalid = sum(1 for x in out if not x["is_valid"])
    print(f"Valid: {len(out) - invalid}  Invalid: {invalid}")
    if invalid:
        raise SystemExit(2)


if __name__ == "__main__":
    main()


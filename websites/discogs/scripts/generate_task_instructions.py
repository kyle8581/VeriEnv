import json
import os
import threading
import time
from datetime import datetime

import httpx
import uvicorn

from discogs_sdk import DiscogsClient


DB_URL = "sqlite+pysqlite:////app/.data/discogs.db"
BASE_URL = "http://127.0.0.1:12160"
OUT_PATH = str(Path(__file__).parent.parent / "task_instructions.json")


def web_release_url(release_id: int) -> str:
    return f"http://localhost:12042/release/{release_id}"


def web_market_url(release_id: int) -> str:
    return f"http://localhost:12042/sell/release/{release_id}"


def judge_rinfo(*expected_substrings: str) -> dict:
    return {
        "approach": "rinfo",
        "checks": [f"must_include(^a, {json.dumps(s)})" for s in expected_substrings if s is not None and s != ""],
    }


def judge_url_and_rinfo(path_substring: str, *expected_substrings: str) -> dict:
    return {
        "approach": "rprog+rinfo",
        "checks": [
            f"url=locate_current_url(s), must_include(url, {json.dumps(path_substring)})",
            *[
                f"must_include(^a, {json.dumps(s)})"
                for s in expected_substrings
                if s is not None and s != ""
            ],
        ],
    }


def add_task(tasks: list, *, instruction: str, code: str, result, difficulty: str, judge: dict, is_valid: bool = True):
    tasks.append(
        {
            "instruction": instruction,
            "python sdk tool call": code,
            "tool call result": result,
            "is_valid": bool(is_valid),
            "difficulty": difficulty,
            "judge_for_webagent": judge,
        }
    )


def start_backend() -> tuple[uvicorn.Server, threading.Thread]:
    # Make sure backend reads the correct SQLite DB.
    os.environ["DATABASE_URL"] = DB_URL
    os.environ.setdefault("CORS_ORIGINS", "http://localhost:12042")
    os.environ.setdefault("JWT_SECRET", "dev_secret_change_me")

    # Import after env vars are set.
    from app.main import create_app  # noqa: WPS433 (runtime import is intentional)

    app = create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=12160, log_level="warning")
    server = uvicorn.Server(config)

    t = threading.Thread(target=server.run, daemon=True)
    t.start()

    for _ in range(120):
        try:
            if httpx.get(f"{BASE_URL}/healthz", timeout=1.0).status_code == 200:
                return server, t
        except Exception:
            pass
        time.sleep(0.1)

    raise RuntimeError("Backend did not start in time")


def main() -> None:
    server, thread = start_backend()

    try:
        c = DiscogsClient(base_url=BASE_URL)

        home = c.home()
        genres = c.genres()
        rock = c.genre_overview("rock")

        banner_release_id = home["banner"]["release_id"]
        if banner_release_id is None:
            raise RuntimeError("Expected home.banner.release_id to be present")

        banner_release = c.release(int(banner_release_id))

        # Build a pool of release IDs we can reference in tasks.
        release_pool: list[int] = []
        for key in ["trending_releases", "newly_added"]:
            for r in home.get(key, []):
                rid = int(r["id"])
                if rid not in release_pool:
                    release_pool.append(rid)
        for key in ["most_collected", "early_releases", "most_sold_this_month"]:
            for r in rock.get(key, []):
                rid = int(r["id"])
                if rid not in release_pool:
                    release_pool.append(rid)
        if int(banner_release_id) not in release_pool:
            release_pool.insert(0, int(banner_release_id))

        tasks: list[dict] = []

        # -----------------
        # Easy / Medium: homepage + genres
        # -----------------
        add_task(
            tasks,
            instruction=(
                "Go to the Discogs clone homepage at http://localhost:12042/. "
                "What is the big hero headline text at the top of the page?"
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "home = c.home()\n"
                "home['hero_title']"
            ),
            result={"hero_title": home["hero_title"]},
            difficulty="easy",
            judge=judge_url_and_rinfo("/", home["hero_title"]),
        )

        add_task(
            tasks,
            instruction=(
                "On the homepage (http://localhost:12042/), look at the wide banner promo right below the hero section. "
                "Tell me the banner title exactly as shown."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "c.home()['banner']['title']"
            ),
            result={"banner_title": home["banner"]["title"]},
            difficulty="easy",
            judge=judge_url_and_rinfo("/", home["banner"]["title"]),
        )

        add_task(
            tasks,
            instruction=(
                "On the homepage (http://localhost:12042/), count how many small promo tiles are shown in the hero area "
                "(the stack of clickable cards next to the hero image). Return just the number."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "len(c.home()['hero_tiles'])"
            ),
            result={"hero_tiles_count": len(home["hero_tiles"])},
            difficulty="easy",
            judge=judge_rinfo(str(len(home["hero_tiles"]))),
        )

        add_task(
            tasks,
            instruction=(
                "Go to http://localhost:12042/ and scroll to the 'Trending Releases' section. "
                "How many release cards are shown there?"
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "len(c.home()['trending_releases'])"
            ),
            result={"trending_releases_count": len(home["trending_releases"])},
            difficulty="easy",
            judge=judge_rinfo(str(len(home["trending_releases"]))),
        )

        tr0 = home["trending_releases"][0]
        add_task(
            tasks,
            instruction=(
                "On the homepage (http://localhost:12042/), open the first item under 'Trending Releases'. "
                "Tell me the release title and the artist name shown on that card."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "r = c.home()['trending_releases'][0]\n"
                "{'title': r['title'], 'artist': r.get('artist'), 'id': r['id']}"
            ),
            result={"id": tr0["id"], "title": tr0["title"], "artist": tr0.get("artist")},
            difficulty="easy",
            judge=judge_url_and_rinfo(f"/release/{tr0['id']}", tr0["title"], tr0.get("artist") or ""),
        )

        add_task(
            tasks,
            instruction=(
                "Open the genres list by navigating to any genre page from the header "
                "(or directly visit http://localhost:12042/genre/rock). "
                "List all genre names available on this site."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "[g['name'] for g in c.genres()]"
            ),
            result={"genres": [g["name"] for g in genres]},
            difficulty="easy",
            judge=judge_rinfo(*[g["name"] for g in genres]),
        )

        # -----------------
        # Easy / Medium: Rock genre overview
        # -----------------
        add_task(
            tasks,
            instruction=(
                "Go to the Rock genre overview page at http://localhost:12042/genre/rock. "
                "In the Rock description block, what is the first sentence?"
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "desc = c.genre_overview('rock')['genre']['description']\n"
                "desc.split('.')[0].strip() + '.'"
            ),
            result={"rock_description_first_sentence": rock["genre"]["description"].split(".")[0].strip() + "."},
            difficulty="medium",
            judge=judge_url_and_rinfo("/genre/rock", rock["genre"]["description"].split(".")[0].strip()),
        )

        add_task(
            tasks,
            instruction=(
                "On http://localhost:12042/genre/rock, find the 'Related Styles of Music' pills. "
                "Return the full list of related style names shown."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "c.genre_overview('rock')['related_styles']"
            ),
            result={"rock_related_styles": rock["related_styles"]},
            difficulty="easy",
            judge=judge_rinfo(*rock["related_styles"][:10]),
        )

        add_task(
            tasks,
            instruction=(
                "On the Rock overview page (http://localhost:12042/genre/rock), look for the chart/table called "
                "'Rock Music Releases by Decade'. Report the decade labels and counts exactly as listed in the table."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "c.genre_overview('rock')['stats']['releases_by_decade']"
            ),
            result={"releases_by_decade": rock["stats"]["releases_by_decade"]},
            difficulty="medium",
            judge=judge_rinfo(*[f"{row['label']}: {row['value']}" for row in rock["stats"]["releases_by_decade"]]),
        )

        add_task(
            tasks,
            instruction=(
                "On http://localhost:12042/genre/rock, find the chart/table titled 'Top Submitters of Rock Music'. "
                "Return the contributor labels and counts exactly as shown."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "c.genre_overview('rock')['stats']['top_submitters']"
            ),
            result={"top_submitters": rock["stats"]["top_submitters"]},
            difficulty="medium",
            judge=judge_rinfo(*[f"{row['label']}: {row['value']}" for row in rock["stats"]["top_submitters"]]),
        )

        mc0 = rock["most_collected"][0]
        mc0_detail = c.release(int(mc0["id"]))
        add_task(
            tasks,
            instruction=(
                "Go to http://localhost:12042/genre/rock and open the first release shown under 'Most Collected Rock Music'. "
                "Tell me the release title and year shown on its release page."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "rid = c.genre_overview('rock')['most_collected'][0]['id']\n"
                "r = c.release(rid)\n"
                "{'id': rid, 'title': r['title'], 'year': r['year']}"
            ),
            result={"id": mc0["id"], "title": mc0_detail["title"], "year": mc0_detail["year"]},
            difficulty="medium",
            judge=judge_url_and_rinfo(f"/release/{mc0['id']}", mc0_detail["title"], str(mc0_detail["year"])),
        )

        ear0 = rock["early_releases"][0]
        ear0_detail = c.release(int(ear0["id"]))
        add_task(
            tasks,
            instruction=(
                "On http://localhost:12042/genre/rock, open the very first item under 'Early Rock Releases'. "
                "What is the release title, and what year is it from?"
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "rid = c.genre_overview('rock')['early_releases'][0]['id']\n"
                "r = c.release(rid)\n"
                "{'id': rid, 'title': r['title'], 'year': r['year']}"
            ),
            result={"id": ear0["id"], "title": ear0_detail["title"], "year": ear0_detail["year"]},
            difficulty="medium",
            judge=judge_url_and_rinfo(f"/release/{ear0['id']}", ear0_detail["title"], str(ear0_detail["year"])),
        )

        ms0 = rock["most_sold_this_month"][0]
        ms0_detail = c.release(int(ms0["id"]))
        ms0_artist = (ms0_detail["artists"][0]["name"] if ms0_detail.get("artists") else None)
        add_task(
            tasks,
            instruction=(
                "Go to http://localhost:12042/genre/rock and open the first release shown under 'Most Sold Rock Releases This Month'. "
                "Tell me the title and artist displayed on the release page header."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "rid = c.genre_overview('rock')['most_sold_this_month'][0]['id']\n"
                "r = c.release(rid)\n"
                "{'id': rid, 'title': r['title'], 'main_artist': (r['artists'][0]['name'] if r['artists'] else None)}"
            ),
            result={"id": ms0["id"], "title": ms0_detail["title"], "main_artist": ms0_artist},
            difficulty="medium",
            judge=judge_url_and_rinfo(f"/release/{ms0['id']}", ms0_detail["title"]),
        )

        # -----------------
        # Featured release (banner) details
        # -----------------
        r = banner_release
        add_task(
            tasks,
            instruction=(
                f"Open the featured release page at {web_release_url(int(banner_release_id))}. "
                "What year is this release, and what country is listed?"
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"r = c.release({int(banner_release_id)})\n"
                "{'year': r['year'], 'country': r['country']}"
            ),
            result={"release_id": int(banner_release_id), "year": r["year"], "country": r["country"]},
            difficulty="easy",
            judge=judge_url_and_rinfo(f"/release/{int(banner_release_id)}", str(r["year"]), r.get("country") or ""),
        )

        label0 = r["labels"][0] if r.get("labels") else None
        add_task(
            tasks,
            instruction=(
                f"Go to {web_release_url(int(banner_release_id))} and look at the metadata table. "
                "What is the label name and catalog number shown for this release?"
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"r = c.release({int(banner_release_id)})\n"
                "r['labels'][0]"
            ),
            result={"release_id": int(banner_release_id), "label": label0},
            difficulty="easy",
            judge=judge_url_and_rinfo(
                f"/release/{int(banner_release_id)}", (label0 or {}).get("name", ""), (label0 or {}).get("catalog_no", "")
            ),
        )

        fmt0 = r["formats"][0] if r.get("formats") else None
        add_task(
            tasks,
            instruction=(
                f"On {web_release_url(int(banner_release_id))}, check the 'Format' field. "
                "Report the format name and the format text exactly as shown."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"r = c.release({int(banner_release_id)})\n"
                "r['formats'][0]"
            ),
            result={"release_id": int(banner_release_id), "format": fmt0},
            difficulty="easy",
            judge=judge_rinfo((fmt0 or {}).get("name", ""), (fmt0 or {}).get("text", "")),
        )

        tracks = r.get("tracks") or []
        a1_title = next(t["title"] for t in tracks if t["position"] == "A1")
        add_task(
            tasks,
            instruction=(
                f"On {web_release_url(int(banner_release_id))}, scroll to the Tracklist. "
                "What is the title of track A1?"
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"tracks = c.release({int(banner_release_id)})['tracks']\n"
                "next(t['title'] for t in tracks if t['position'] == 'A1')"
            ),
            result={"release_id": int(banner_release_id), "A1_title": a1_title},
            difficulty="easy",
            judge=judge_rinfo(a1_title),
        )

        time_secs = next(t["duration_seconds"] for t in tracks if t["title"] == "Time")
        add_task(
            tasks,
            instruction=(
                f"On {web_release_url(int(banner_release_id))}, find the track 'Time' in the tracklist. "
                "What duration is shown for it (in seconds)?"
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"tracks = c.release({int(banner_release_id)})['tracks']\n"
                "next(t['duration_seconds'] for t in tracks if t['title'] == 'Time')"
            ),
            result={"release_id": int(banner_release_id), "Time_duration_seconds": time_secs},
            difficulty="medium",
            judge=judge_rinfo(str(time_secs)),
        )

        add_task(
            tasks,
            instruction=(
                f"Open {web_release_url(int(banner_release_id))} and count how many tracks are in the tracklist. "
                "Return just the number."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"len(c.release({int(banner_release_id)})['tracks'])"
            ),
            result={"release_id": int(banner_release_id), "track_count": len(tracks)},
            difficulty="easy",
            judge=judge_rinfo(str(len(tracks))),
        )

        notes = r.get("notes") or ""
        first_20_words = " ".join(notes.split()[:20])
        add_task(
            tasks,
            instruction=(
                f"On {web_release_url(int(banner_release_id))}, scroll to the Notes section. "
                "Copy the first 20 words of the notes text."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"notes = (c.release({int(banner_release_id)}).get('notes') or '')\n"
                "' '.join(notes.split()[:20])"
            ),
            result={"release_id": int(banner_release_id), "notes_first_20_words": first_20_words},
            difficulty="medium",
            judge=judge_rinfo(*notes.split()[:6]),
        )

        add_task(
            tasks,
            instruction=(
                f"On {web_release_url(int(banner_release_id))}, read the Genre and Style fields. "
                "List all genres and styles shown."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"r = c.release({int(banner_release_id)})\n"
                "{'genres': r['genres'], 'styles': r['styles']}"
            ),
            result={"release_id": int(banner_release_id), "genres": r.get("genres"), "styles": r.get("styles")},
            difficulty="easy",
            judge=judge_rinfo(*((r.get("genres") or []) + (r.get("styles") or []))),
        )

        add_task(
            tasks,
            instruction=(
                f"On {web_release_url(int(banner_release_id))}, look at the marketplace summary near the top (For Sale). "
                "How many copies are for sale, and what is the lowest price shown (in cents)?"
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"r = c.release({int(banner_release_id)})\n"
                "{'for_sale_count': r['for_sale_count'], 'lowest_price_cents': r['lowest_price_cents']}"
            ),
            result={
                "release_id": int(banner_release_id),
                "for_sale_count": r["for_sale_count"],
                "lowest_price_cents": r["lowest_price_cents"],
            },
            difficulty="medium",
            judge=judge_rinfo(str(r["for_sale_count"]), str(r["lowest_price_cents"])),
        )

        # -----------------
        # Medium: marketplace listings filters/sorting
        # -----------------
        listings_all = c.listings(int(banner_release_id), sort="price_asc", limit=10)
        cheapest = listings_all["items"][0]
        add_task(
            tasks,
            instruction=(
                f"Go to the marketplace page for this release: {web_market_url(int(banner_release_id))}. "
                "Without applying any filters, identify the cheapest listing currently shown and tell me "
                "the seller username and the price in cents."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"page = c.listings({int(banner_release_id)}, sort='price_asc', limit=1)\n"
                "it = page['items'][0]\n"
                "{'seller': it['seller']['username'], 'price_cents': it['price_cents'], 'listing_id': it['id']}"
            ),
            result={
                "release_id": int(banner_release_id),
                "listing_id": cheapest["id"],
                "seller": cheapest["seller"]["username"],
                "price_cents": cheapest["price_cents"],
            },
            difficulty="medium",
            judge=judge_url_and_rinfo(
                f"/sell/release/{int(banner_release_id)}", cheapest["seller"]["username"], str(cheapest["price_cents"])
            ),
        )

        page_min_rating = c.listings(int(banner_release_id), min_rating=99.0, sort="price_asc", limit=1)
        add_task(
            tasks,
            instruction=(
                f"On {web_market_url(int(banner_release_id))}, set the minimum seller rating filter to 99 and apply. "
                "How many listings match after filtering?"
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"page = c.listings({int(banner_release_id)}, min_rating=99.0, sort='price_asc', limit=1)\n"
                "page['total']"
            ),
            result={"release_id": int(banner_release_id), "min_rating_99_total": page_min_rating["total"]},
            difficulty="medium",
            judge=judge_rinfo(str(page_min_rating["total"])),
        )

        # Choose a media condition that actually yields listings.
        cond_used = None
        cond_page = None
        for cond in ["Mint (M)", "Near Mint (NM or M-)", "Very Good Plus (VG+)", "Very Good (VG)"]:
            p = c.listings(int(banner_release_id), media_condition=cond, sort="price_asc", limit=1)
            if p["total"] > 0:
                cond_used = cond
                cond_page = p
                break
        if cond_used is None or cond_page is None:
            raise RuntimeError("No marketplace listings found for expected media conditions")

        add_task(
            tasks,
            instruction=(
                f"On {web_market_url(int(banner_release_id))}, set the Media Condition filter to {cond_used!r} and apply. "
                "Then report the seller username for the cheapest filtered listing."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"page = c.listings({int(banner_release_id)}, media_condition={cond_used!r}, sort='price_asc', limit=1)\n"
                "page['items'][0]['seller']['username']"
            ),
            result={
                "release_id": int(banner_release_id),
                "media_condition": cond_used,
                "cheapest_filtered_seller": cond_page["items"][0]["seller"]["username"],
            },
            difficulty="medium",
            judge=judge_rinfo(cond_page["items"][0]["seller"]["username"]),
        )

        newest_page = c.listings(int(banner_release_id), sort="newest", limit=1)
        add_task(
            tasks,
            instruction=(
                f"On {web_market_url(int(banner_release_id))}, change the sort order to 'Newest' and apply. "
                "What is the listing ID of the first row shown?"
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"page = c.listings({int(banner_release_id)}, sort='newest', limit=1)\n"
                "page['items'][0]['id']"
            ),
            result={"release_id": int(banner_release_id), "newest_first_listing_id": newest_page["items"][0]["id"]},
            difficulty="medium",
            judge=judge_rinfo(str(newest_page["items"][0]["id"])),
        )

        # -----------------
        # Easy/Medium: search + other releases
        # -----------------
        search_res = c.search("Dark Side Of The Moon")
        add_task(
            tasks,
            instruction=(
                "Use the site search box to search for 'Dark Side Of The Moon'. "
                "Open the matching release result and tell me the release ID from the URL."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "results = c.search('Dark Side Of The Moon')\n"
                "[r['id'] for r in results]"
            ),
            result={
                "search_query": "Dark Side Of The Moon",
                "result_ids": [r["id"] for r in search_res],
                "expected_release_id": int(banner_release_id),
            },
            difficulty="easy",
            judge=judge_url_and_rinfo(f"/release/{int(banner_release_id)}", str(int(banner_release_id))),
        )

        # Keep this small so we can fit hard (auth) tasks in the final 50.
        other_ids = [rid for rid in release_pool if rid != int(banner_release_id)][:7]
        for rid in other_ids:
            rd = c.release(int(rid))
            main_artist = rd["artists"][0]["name"] if rd.get("artists") else None
            tcount = len(rd.get("tracks") or [])

            add_task(
                tasks,
                instruction=(
                    f"Open this release page: {web_release_url(int(rid))}. "
                    "Tell me the release title, the main artist, and the year."
                ),
                code=(
                    "from discogs_sdk import DiscogsClient\n"
                    f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                    f"r = c.release({int(rid)})\n"
                    "{'title': r['title'], 'artist': (r['artists'][0]['name'] if r['artists'] else None), 'year': r['year']}"
                ),
                result={"release_id": int(rid), "title": rd["title"], "artist": main_artist, "year": rd["year"]},
                difficulty="easy",
                judge=judge_url_and_rinfo(f"/release/{int(rid)}", rd["title"], str(rd["year"])),
            )

            add_task(
                tasks,
                instruction=f"On {web_release_url(int(rid))}, count the number of tracks in the tracklist and return just the number.",
                code=(
                    "from discogs_sdk import DiscogsClient\n"
                    f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                    f"len(c.release({int(rid)})['tracks'])"
                ),
                result={"release_id": int(rid), "track_count": tcount},
                difficulty="easy",
                judge=judge_rinfo(str(tcount)),
            )

        # -----------------
        # Hard: authentication + account state
        # -----------------
        authed = DiscogsClient(base_url=BASE_URL)
        authed.login("demo", "password123")
        me = authed.me()

        add_task(
            tasks,
            instruction=(
                "Log in to the site at http://localhost:12042/login using username 'demo' and password 'password123'. "
                "After logging in, open your profile/account page and tell me the username that is displayed."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "c.login('demo', 'password123')\n"
                "c.me()['username']"
            ),
            result={"me": me},
            difficulty="hard",
            judge=judge_url_and_rinfo("/me", "demo"),
        )

        want_before = authed.wantlist()
        col_before = authed.collection()
        want_ids = {int(r["id"]) for r in want_before}
        col_ids = {int(r["id"]) for r in col_before}

        candidate_release = None
        for rid in release_pool:
            if int(rid) not in want_ids and int(rid) not in col_ids:
                candidate_release = int(rid)
                break
        if candidate_release is None:
            candidate_release = int(banner_release_id)

        authed.add_to_wantlist(candidate_release)
        want_after = authed.wantlist()
        added_want = next((rr for rr in want_after if int(rr["id"]) == candidate_release), None)

        add_task(
            tasks,
            instruction=(
                "Log in as 'demo' (password 'password123'). "
                f"Go to the release page {web_release_url(candidate_release)} and click 'Add to Wantlist'. "
                "Then go to http://localhost:12042/me/wantlist and confirm the release appears there; tell me its title."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "c.login('demo','password123')\n"
                f"c.add_to_wantlist({candidate_release})\n"
                f"[r for r in c.wantlist() if r['id'] == {candidate_release}][0]['title']"
            ),
            result={"release_id": candidate_release, "added_to_wantlist": added_want},
            difficulty="hard",
            judge=judge_url_and_rinfo("/me/wantlist", (added_want or {}).get("title", "")),
        )

        authed.add_to_collection(candidate_release)
        col_after = authed.collection()
        added_col = next((rr for rr in col_after if int(rr["id"]) == candidate_release), None)

        add_task(
            tasks,
            instruction=(
                "Log in as 'demo' (password 'password123'). "
                f"On the release page {web_release_url(candidate_release)}, click 'Add to Collection'. "
                "Then open http://localhost:12042/me/collection and tell me the title of the release you just added."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "c.login('demo','password123')\n"
                f"c.add_to_collection({candidate_release})\n"
                f"[r for r in c.collection() if r['id'] == {candidate_release}][0]['title']"
            ),
            result={"release_id": candidate_release, "added_to_collection": added_col},
            difficulty="hard",
            judge=judge_url_and_rinfo("/me/collection", (added_col or {}).get("title", "")),
        )

        # Make cart empty first
        cart0 = authed.cart()
        for item in cart0.get("items", []):
            authed.cart_remove(int(item["id"]))

        page_for_cart = authed.listings(int(banner_release_id), sort="price_asc", limit=5)
        listing_ids = [int(it["id"]) for it in page_for_cart["items"]]
        listing_a = listing_ids[0]
        listing_b = listing_ids[1] if len(listing_ids) > 1 else listing_ids[0]

        cart1 = authed.cart_add(listing_a, quantity=2)
        add_task(
            tasks,
            instruction=(
                "Log in as 'demo' (password 'password123'), then go to your cart at http://localhost:12042/cart and make sure it's empty. "
                f"Next, open the marketplace page {web_market_url(int(banner_release_id))} and add the cheapest listing to your cart with quantity 2. "
                "Finally, return to the cart page and tell me the cart total in cents."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "c.login('demo','password123')\n"
                f"listing_id = c.listings({int(banner_release_id)}, sort='price_asc', limit=1)['items'][0]['id']\n"
                "cart = c.cart_add(listing_id, quantity=2)\n"
                "cart['total_cents']"
            ),
            result={"added_listing_id": listing_a, "cart": cart1},
            difficulty="hard",
            judge=judge_url_and_rinfo("/cart", str(cart1["total_cents"])),
        )

        cart2 = authed.cart_add(listing_b, quantity=1)
        add_task(
            tasks,
            instruction=(
                "While logged in as 'demo', add a second (different) listing for the same release into your cart from the marketplace page. "
                "Then go to http://localhost:12042/cart and tell me how many line items are in the cart."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "c.login('demo','password123')\n"
                f"items = c.listings({int(banner_release_id)}, sort='price_asc', limit=2)['items']\n"
                "c.cart_add(items[0]['id'], quantity=1)\n"
                "c.cart_add(items[1]['id'], quantity=1)\n"
                "len(c.cart()['items'])"
            ),
            result={"cart_items_count": len(cart2["items"]), "cart": cart2},
            difficulty="hard",
            judge=judge_rinfo(str(len(cart2["items"]))),
        )

        cart_items_now = authed.cart()["items"]
        remove_id = int(cart_items_now[0]["id"])
        authed.cart_remove(remove_id)
        cart_after_remove = authed.cart()
        add_task(
            tasks,
            instruction=(
                "Log in as 'demo' and open http://localhost:12042/cart. "
                "Remove the first cart line item you see. After removing it, how many cart items remain?"
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "c.login('demo','password123')\n"
                "cart = c.cart()\n"
                "c.cart_remove(cart['items'][0]['id'])\n"
                "len(c.cart()['items'])"
            ),
            result={"removed_cart_item_id": remove_id, "remaining_items": len(cart_after_remove["items"])},
            difficulty="hard",
            judge=judge_rinfo(str(len(cart_after_remove["items"]))),
        )

        # Ensure at least one item exists, then checkout
        if not authed.cart()["items"]:
            authed.cart_add(listing_a, quantity=1)
        order = authed.checkout()
        cart_after_checkout = authed.cart()
        add_task(
            tasks,
            instruction=(
                "Log in as 'demo' and add any one marketplace listing to your cart. "
                "Go to http://localhost:12042/cart and click the Checkout button. "
                "After checkout completes, tell me the order status and the order total in cents."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "c.login('demo','password123')\n"
                f"listing_id = c.listings({int(banner_release_id)}, sort='price_asc', limit=1)['items'][0]['id']\n"
                "c.cart_add(listing_id, quantity=1)\n"
                "order = c.checkout()\n"
                "{'status': order['status'], 'total_cents': order['total_cents']}"
            ),
            result={"order": order, "cart_after_checkout": cart_after_checkout},
            difficulty="hard",
            judge=judge_rinfo(order["status"], str(order["total_cents"])),
        )

        add_task(
            tasks,
            instruction=(
                "After completing checkout while logged in as 'demo', go back to http://localhost:12042/cart. "
                "Confirm the cart is empty and return the number of cart items."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                "c.login('demo','password123')\n"
                "len(c.cart()['items'])"
            ),
            result={"cart_items_after_checkout": len(cart_after_checkout.get("items", []))},
            difficulty="hard",
            judge=judge_rinfo(str(len(cart_after_checkout.get("items", [])))),
        )

        # Register + login as a new user (hard)
        username = f"taskuser_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        email = f"{username}@example.com"
        password = "Passw0rd!123"

        newc = DiscogsClient(base_url=BASE_URL)
        reg = newc.register(username=username, email=email, password=password, display_name="Task User")
        newc.login(username, password)
        me_new = newc.me()

        add_task(
            tasks,
            instruction=(
                "Create a new account on http://localhost:12042/login by choosing the Register option. "
                f"Use username '{username}', email '{email}', and password '{password}'. "
                "After registering, log in and tell me the username shown on your account/profile page."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"c.register(username={username!r}, email={email!r}, password={password!r}, display_name='Task User')\n"
                f"c.login({username!r}, {password!r})\n"
                "c.me()['username']"
            ),
            result={"registered": reg, "me": me_new},
            difficulty="hard",
            judge=judge_url_and_rinfo("/me", username),
        )

        newc.add_to_wantlist(int(banner_release_id))
        wl_new = newc.wantlist()
        add_task(
            tasks,
            instruction=(
                f"Log in as '{username}' using password '{password}'. "
                f"Open the release page {web_release_url(int(banner_release_id))} and add it to your wantlist. "
                "Then open http://localhost:12042/me/wantlist and tell me the title of the first item in your wantlist."
            ),
            code=(
                "from discogs_sdk import DiscogsClient\n"
                f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                f"c.login({username!r}, {password!r})\n"
                f"c.add_to_wantlist({int(banner_release_id)})\n"
                "c.wantlist()[0]['title']"
            ),
            result={"username": username, "wantlist_first": wl_new[0] if wl_new else None},
            difficulty="hard",
            judge=judge_url_and_rinfo("/me/wantlist", (wl_new[0]["title"] if wl_new else "")),
        )

        # Finalize count: if short, pad with additional non-auth release tasks; if long, trim.
        idx = 0
        while len(tasks) < 50 and idx < len(release_pool):
            rid = int(release_pool[idx])
            idx += 1
            if rid == int(banner_release_id):
                continue
            rd = c.release(rid)
            add_task(
                tasks,
                instruction=f"Open {web_release_url(rid)} and tell me the country and the release year.",
                code=(
                    "from discogs_sdk import DiscogsClient\n"
                    f"c = DiscogsClient(base_url={BASE_URL!r})\n"
                    f"r = c.release({rid})\n"
                    "{'country': r['country'], 'year': r['year']}"
                ),
                result={"release_id": rid, "country": rd.get("country"), "year": rd.get("year")},
                difficulty="medium",
                judge=judge_url_and_rinfo(f"/release/{rid}", str(rd.get("year") or "")),
            )

        if len(tasks) > 50:
            tasks = tasks[:50]
        if len(tasks) < 50:
            raise RuntimeError(f"Generated {len(tasks)} tasks; expected 50")

        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

        print(f"Wrote {OUT_PATH} with {len(tasks)} tasks")

    finally:
        server.should_exit = True
        thread.join(timeout=5)


if __name__ == "__main__":
    main()


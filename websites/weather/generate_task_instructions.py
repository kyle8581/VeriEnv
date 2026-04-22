import json

from weather_sdk import WeatherPortalClient
from weather_sdk.client import ApiError

BASE_URL = "http://localhost:12142"
OUT_PATH = str(Path(__file__).parent / "task_instructions.json")


def ensure_user(c: WeatherPortalClient, *, email: str, password: str, name: str) -> str:
    """Register if needed, then login. Returns 'registered' or 'logged_in'."""
    try:
        c.register(email=email, password=password, name=name)
        return "registered"
    except ApiError:
        c.login(email=email, password=password)
        return "logged_in"


def safe_round(x, nd=1):
    return None if x is None else round(float(x), nd)


def first_sentence(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    for sep in [". ", ".\n"]:
        if sep in t:
            return t.split(sep, 1)[0].strip() + "."
    return t


def md_first_heading(body_md: str) -> str:
    for line in (body_md or "").splitlines():
        s = line.strip()
        if s.startswith("## "):
            return s[3:].strip()
    return ""


def main() -> int:
    with WeatherPortalClient(BASE_URL) as c:
        # Reference data (real site content)
        categories = c.list_categories()
        cat_names = [x.name for x in categories]
        cat_slugs = [x.slug for x in categories]

        plans = c.list_plans()
        plan_by_name = {p.name: p for p in plans}

        # Common locations
        city_queries = [
            "San Francisco",
            "New York",
            "Miami",
            "Los Angeles",
            "Seattle",
            "Denver",
            "Boston",
            "Chicago",
            "Phoenix",
            "Austin",
            "San Diego",
            "San Antonio",
            "Dallas",
            "Portland",
        ]
        loc_by_city = {q: c.search_locations(q, limit=1)[0] for q in city_queries}

        # Content samples
        top1 = c.list_articles(category="top-stories", limit=1)[0]
        latest1 = c.list_articles(category="latest-news", limit=1)[0]
        editors1 = c.list_articles(category="editors-picks", limit=1)[0]
        safe1 = c.list_articles(category="stay-safe", limit=1)[0]
        rec1 = c.list_articles(category="recommended", limit=1)[0]
        video1 = c.list_articles(kind="video", limit=1)[0]

        photos_default = c.list_photos()  # default limit=24
        deals_default = c.list_deals()  # default limit=24

        # Choose a specific, stable article slug for “open this article” tasks
        specific_article = c.list_articles(limit=10)[3]
        specific_article_detail = c.get_article(specific_article.slug)

        # Deals stats
        priced_deals = [d for d in deals_default if d.price_usd is not None]
        cheapest_deal = min(priced_deals, key=lambda d: d.price_usd)
        priciest_deal = max(priced_deals, key=lambda d: d.price_usd)
        under_50 = [d for d in priced_deals if d.price_usd < 50]
        providers = sorted({d.provider for d in deals_default})
        gooddeals = [d for d in deals_default if d.provider == "GoodDeals"]

        tasks: list[dict] = []

        def add_task(*, instruction, tool_call, result, difficulty, judge):
            tasks.append(
                {
                    "instruction": instruction,
                    "python sdk tool call": tool_call,
                    "tool call result": result,
                    "is_valid": True,
                    "difficulty": difficulty,
                    "judge_for_webagent": judge,
                }
            )

        # --- 1-13 Weather / locations (guest) ---
        for city in ["San Francisco", "New York", "Miami"]:
            loc = loc_by_city[city]
            cur = c.current(loc.slug)
            temp = safe_round(cur.temperature_c, 1)
            label = cur.weather.get("label")
            add_task(
                instruction=(
                    f"Go to the weather page for {city} and tell me the current temperature in °C "
                    "and the condition label shown (e.g., Clear, Cloudy, Rain)."
                ),
                tool_call=(
                    "from weather_sdk import WeatherPortalClient\n"
                    f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                    f"    loc = c.search_locations({city!r}, limit=1)[0]\n"
                    "    cur = c.current(loc.slug)\n"
                    "    result = {'city': loc.name, 'slug': loc.slug, 'temperature_c': cur.temperature_c, 'label': cur.weather.get('label')}\n"
                ),
                result={"city": loc.name, "slug": loc.slug, "temperature_c": temp, "label": label},
                difficulty="easy",
                judge={
                    "approach": "rinfo",
                    "setup_sdk": f"loc=c.search_locations({city!r},limit=1)[0]; cur=c.current(loc.slug)",
                    "checks": [
                        "must_include(answer, str(round(cur.temperature_c, 1)))",
                        "must_include(answer, cur.weather['label'])",
                    ],
                },
            )

        la = loc_by_city["Los Angeles"]
        sea = loc_by_city["Seattle"]
        cur_la = c.current(la.slug)
        cur_sea = c.current(sea.slug)
        la_t = float(cur_la.temperature_c or 0.0)
        sea_t = float(cur_sea.temperature_c or 0.0)
        warmer = la.name if la_t >= sea_t else sea.name
        add_task(
            instruction=(
                "Compare the current temperatures for Los Angeles, CA and Seattle, WA on the site. "
                "Tell me which city is warmer right now, and include both temperatures in °C."
            ),
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    la=c.search_locations('Los Angeles',limit=1)[0]\n"
                "    sea=c.search_locations('Seattle',limit=1)[0]\n"
                "    cla=c.current(la.slug)\n"
                "    csea=c.current(sea.slug)\n"
                "    result={'la_temp_c':cla.temperature_c,'sea_temp_c':csea.temperature_c,'warmer':'Los Angeles' if (cla.temperature_c or 0)>=(csea.temperature_c or 0) else 'Seattle'}\n"
            ),
            result={
                "la_slug": la.slug,
                "sea_slug": sea.slug,
                "la_temp_c": safe_round(cur_la.temperature_c, 1),
                "sea_temp_c": safe_round(cur_sea.temperature_c, 1),
                "warmer": warmer,
            },
            difficulty="medium",
            judge={
                "approach": "rinfo",
                "setup_sdk": "la=c.search_locations('Los Angeles',1)[0]; sea=c.search_locations('Seattle',1)[0]; cla=c.current(la.slug); csea=c.current(sea.slug)",
                "checks": [
                    "must_include(answer, 'Los Angeles')",
                    "must_include(answer, 'Seattle')",
                    "must_include(answer, str(round(cla.temperature_c, 1)))",
                    "must_include(answer, str(round(csea.temperature_c, 1)))",
                    "must_include(answer, 'Los Angeles' if (cla.temperature_c or 0)>=(csea.temperature_c or 0) else 'Seattle')",
                ],
            },
        )

        den = loc_by_city["Denver"]
        daily_den = c.daily(den.slug)[0]
        add_task(
            instruction="Open the 10-day forecast for Denver, CO and tell me today’s high and low temperatures in °C.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    den=c.search_locations('Denver',limit=1)[0]\n"
                "    d=c.daily(den.slug)[0]\n"
                "    result={'date': d.date, 'high_c': d.temp_max_c, 'low_c': d.temp_min_c}\n"
            ),
            result={
                "city": den.name,
                "slug": den.slug,
                "date": daily_den.date,
                "high_c": safe_round(daily_den.temp_max_c, 1),
                "low_c": safe_round(daily_den.temp_min_c, 1),
            },
            difficulty="easy",
            judge={
                "approach": "rinfo",
                "setup_sdk": "den=c.search_locations('Denver',1)[0]; d=c.daily(den.slug)[0]",
                "checks": [
                    "must_include(answer, str(round(d.temp_max_c, 1)))",
                    "must_include(answer, str(round(d.temp_min_c, 1)))",
                ],
            },
        )

        bos = loc_by_city["Boston"]
        daily_bos = c.daily(bos.slug)[0]
        add_task(
            instruction="On the Boston, MA forecast page, find today’s sunrise and sunset times and report both exactly as shown.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    bos=c.search_locations('Boston',limit=1)[0]\n"
                "    d=c.daily(bos.slug)[0]\n"
                "    result={'date': d.date, 'sunrise': d.sunrise, 'sunset': d.sunset}\n"
            ),
            result={"city": bos.name, "slug": bos.slug, "date": daily_bos.date, "sunrise": daily_bos.sunrise, "sunset": daily_bos.sunset},
            difficulty="medium",
            judge={
                "approach": "rinfo",
                "setup_sdk": "bos=c.search_locations('Boston',1)[0]; d=c.daily(bos.slug)[0]",
                "checks": ["must_include(answer, d.sunrise)", "must_include(answer, d.sunset)"],
            },
        )

        chi = loc_by_city["Chicago"]
        h_chi = c.hourly(chi.slug)[0]
        add_task(
            instruction="Check the hourly forecast for Chicago, IL and tell me the precipitation probability for the next hour (as a number).",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    chi=c.search_locations('Chicago',limit=1)[0]\n"
                "    h=c.hourly(chi.slug)[0]\n"
                "    result={'time': h.time, 'precip_prob': h.precipitation_probability}\n"
            ),
            result={"city": chi.name, "slug": chi.slug, "time": h_chi.time, "precipitation_probability": h_chi.precipitation_probability},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "chi=c.search_locations('Chicago',1)[0]; h=c.hourly(chi.slug)[0]", "checks": ["must_include(answer, str(h.precipitation_probability))"]},
        )

        sea_h = c.hourly(sea.slug)[0]
        add_task(
            instruction="Look up the next-hour wind speed for Seattle, WA on the hourly forecast and tell me the wind speed in km/h.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    sea=c.search_locations('Seattle',limit=1)[0]\n"
                "    h=c.hourly(sea.slug)[0]\n"
                "    result={'time': h.time, 'wind_kmh': h.wind_speed_kmh}\n"
            ),
            result={"city": sea.name, "slug": sea.slug, "time": sea_h.time, "wind_speed_kmh": safe_round(sea_h.wind_speed_kmh, 1)},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "sea=c.search_locations('Seattle',1)[0]; h=c.hourly(sea.slug)[0]", "checks": ["must_include(answer, str(round(h.wind_speed_kmh, 1)))"]},
        )

        phx = loc_by_city["Phoenix"]
        d_phx = c.daily(phx.slug)[0]
        add_task(
            instruction="Open Phoenix, AZ and tell me today’s maximum UV index from the daily forecast.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    phx=c.search_locations('Phoenix',limit=1)[0]\n"
                "    d=c.daily(phx.slug)[0]\n"
                "    result={'date': d.date, 'uv_index_max': d.uv_index_max}\n"
            ),
            result={"city": phx.name, "slug": phx.slug, "date": d_phx.date, "uv_index_max": d_phx.uv_index_max},
            difficulty="medium",
            judge={"approach": "rinfo", "setup_sdk": "phx=c.search_locations('Phoenix',1)[0]; d=c.daily(phx.slug)[0]", "checks": ["must_include(answer, str(d.uv_index_max))"]},
        )

        zip_loc = c.search_locations("10001", limit=1)[0]
        add_task(
            instruction="Use the site’s location search to look up ZIP code 10001. Tell me the city and state it matches.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    loc=c.search_locations('10001',limit=1)[0]\n"
                "    result={'name': loc.name, 'state': loc.state, 'zip': loc.zip_code, 'slug': loc.slug}\n"
            ),
            result={"name": zip_loc.name, "state": zip_loc.state, "zip_code": zip_loc.zip_code, "slug": zip_loc.slug},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "loc=c.search_locations('10001',1)[0]", "checks": ["must_include(answer, loc.name)", "must_include(answer, loc.state)"]},
        )

        san_results = c.search_locations("San", limit=5)
        add_task(
            instruction="Search for “San” in the site’s location search. Tell me how many results are returned (up to 5) and list the first three location names in order.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    locs=c.search_locations('San',limit=5)\n"
                "    result={'count': len(locs), 'first_three': [l.name for l in locs[:3]]}\n"
            ),
            result={"count": len(san_results), "first_three": [l.name for l in san_results[:3]]},
            difficulty="medium",
            judge={
                "approach": "rinfo",
                "setup_sdk": "locs=c.search_locations('San',limit=5)",
                "checks": ["must_include(answer, str(len(locs)))", "must_include(answer, locs[0].name)", "must_include(answer, locs[1].name)", "must_include(answer, locs[2].name)"],
            },
        )

        sa = loc_by_city["San Antonio"]
        sa_detail = c.get_location(sa.slug)
        add_task(
            instruction="Open the location details for San Antonio, TX and tell me the timezone shown for that location.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    sa=c.search_locations('San Antonio',limit=1)[0]\n"
                "    loc=c.get_location(sa.slug)\n"
                "    result={'slug': loc.slug, 'timezone': loc.timezone}\n"
            ),
            result={"city": sa_detail.name, "slug": sa_detail.slug, "timezone": sa_detail.timezone},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "sa=c.search_locations('San Antonio',1)[0]; loc=c.get_location(sa.slug)", "checks": ["must_include(answer, loc.timezone)"]},
        )

        aus = loc_by_city["Austin"]
        cur_aus = c.current(aus.slug)
        t = float(cur_aus.temperature_c or 0.0)
        at = float(cur_aus.apparent_temperature_c or 0.0)
        diff = round(at - t, 1)
        add_task(
            instruction="Go to Austin, TX current conditions. Tell me the actual temperature and the ‘feels like’ (apparent) temperature in °C, and compute the difference (feels-like minus actual).",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    aus=c.search_locations('Austin',limit=1)[0]\n"
                "    cur=c.current(aus.slug)\n"
                "    t=float(cur.temperature_c or 0.0); at=float(cur.apparent_temperature_c or 0.0)\n"
                "    result={'temperature_c': cur.temperature_c, 'apparent_temperature_c': cur.apparent_temperature_c, 'difference_c': round(at-t,1)}\n"
            ),
            result={"city": aus.name, "slug": aus.slug, "temperature_c": safe_round(cur_aus.temperature_c, 1), "apparent_temperature_c": safe_round(cur_aus.apparent_temperature_c, 1), "difference_c": diff},
            difficulty="medium",
            judge={
                "approach": "rinfo",
                "setup_sdk": "aus=c.search_locations('Austin',1)[0]; cur=c.current(aus.slug); t=float(cur.temperature_c or 0.0); at=float(cur.apparent_temperature_c or 0.0)",
                "checks": ["must_include(answer, str(round(cur.temperature_c, 1)))", "must_include(answer, str(round(cur.apparent_temperature_c, 1)))", "must_include(answer, str(round(at-t, 1)))"],
            },
        )

        # --- 14-25 Content (news/videos) ---
        add_task(
            instruction="Go to the News section and tell me how many categories are available, then list the category names exactly as shown.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    cats=c.list_categories()\n"
                "    result={'count': len(cats), 'names': [x.name for x in cats], 'slugs': [x.slug for x in cats]}\n"
            ),
            result={"count": len(categories), "names": cat_names, "slugs": cat_slugs},
            difficulty="easy",
            judge={
                "approach": "rinfo",
                "setup_sdk": "cats=c.list_categories()",
                "checks": ["must_include(answer, str(len(cats)))", *[f"must_include(answer, {n!r})" for n in cat_names]],
            },
        )

        add_task(
            instruction="In Top Stories, open the first article and tell me the full title.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    a=c.list_articles(category='top-stories',limit=1)[0]\n"
                "    result={'title': a.title, 'slug': a.slug}\n"
            ),
            result={"slug": top1.slug, "title": top1.title},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "a=c.list_articles(category='top-stories',limit=1)[0]", "checks": ["must_include(answer, a.title)"]},
        )

        add_task(
            instruction="In Latest News, open the first article and tell me its title and the source name.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    a=c.list_articles(category='latest-news',limit=1)[0]\n"
                "    result={'title': a.title, 'source': a.source, 'slug': a.slug}\n"
            ),
            result={"slug": latest1.slug, "title": latest1.title, "source": latest1.source},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "a=c.list_articles(category='latest-news',limit=1)[0]", "checks": ["must_include(answer, a.title)", "must_include(answer, a.source)"]},
        )

        add_task(
            instruction="In Editor’s Picks, open the first article and tell me how many minutes it takes to read.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    a=c.list_articles(category='editors-picks',limit=1)[0]\n"
                "    result={'title': a.title, 'reading_minutes': a.reading_minutes, 'slug': a.slug}\n"
            ),
            result={"slug": editors1.slug, "title": editors1.title, "reading_minutes": editors1.reading_minutes},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "a=c.list_articles(category='editors-picks',limit=1)[0]", "checks": ["must_include(answer, str(a.reading_minutes))"]},
        )

        add_task(
            instruction="In Stay Safe, open the first article and tell me the source and the category name.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    a=c.list_articles(category='stay-safe',limit=1)[0]\n"
                "    result={'title': a.title, 'source': a.source, 'category': a.category.name, 'slug': a.slug}\n"
            ),
            result={"slug": safe1.slug, "title": safe1.title, "source": safe1.source, "category_name": safe1.category.name},
            difficulty="medium",
            judge={"approach": "rinfo", "setup_sdk": "a=c.list_articles(category='stay-safe',limit=1)[0]", "checks": ["must_include(answer, a.source)", "must_include(answer, a.category.name)"]},
        )

        add_task(
            instruction="In Recommended, open the first article and paste its short summary.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    a=c.list_articles(category='recommended',limit=1)[0]\n"
                "    result={'title': a.title, 'summary': a.summary, 'slug': a.slug}\n"
            ),
            result={"slug": rec1.slug, "title": rec1.title, "summary": rec1.summary},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "a=c.list_articles(category='recommended',limit=1)[0]", "checks": ["must_include(answer, a.summary)"]},
        )

        add_task(
            instruction="Go to the Video section and tell me the title of the first video.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    v=c.list_articles(kind='video',limit=1)[0]\n"
                "    result={'title': v.title, 'slug': v.slug, 'category': v.category.slug}\n"
            ),
            result={"slug": video1.slug, "title": video1.title, "category_slug": video1.category.slug},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "v=c.list_articles(kind='video',limit=1)[0]", "checks": ["must_include(answer, v.title)"]},
        )

        add_task(
            instruction=f"Open the news article at `/news/{specific_article.slug}` on the site. Tell me its category name and the first heading inside the article body.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                f"    a=c.get_article({specific_article.slug!r})\n"
                "    heading=''\n"
                "    for line in a.body_md.splitlines():\n"
                "        if line.strip().startswith('## '):\n"
                "            heading=line.strip()[3:].strip(); break\n"
                "    result={'category': a.category.name, 'first_heading': heading, 'title': a.title}\n"
            ),
            result={"slug": specific_article.slug, "title": specific_article_detail.title, "category_name": specific_article_detail.category.name, "first_heading": md_first_heading(specific_article_detail.body_md)},
            difficulty="medium",
            judge={
                "approach": "rinfo",
                "setup_sdk": f"a=c.get_article({specific_article.slug!r})",
                "checks": [
                    "must_include(answer, a.category.name)",
                    "must_include(answer, next(line.strip()[3:].strip() for line in a.body_md.splitlines() if line.strip().startswith('## ')))",
                ],
            },
        )

        a1, a2 = c.list_articles(limit=10)[:2]
        longer = a1.title if a1.reading_minutes >= a2.reading_minutes else a2.title
        add_task(
            instruction="Open the first two articles in the News feed and compare their reading times. Tell me which one is longer to read, and include both reading-minute numbers.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    a1=c.list_articles(limit=10)[0]\n"
                "    a2=c.list_articles(limit=10)[1]\n"
                "    longer=a1.title if a1.reading_minutes>=a2.reading_minutes else a2.title\n"
                "    result={'a1': {'title': a1.title, 'min': a1.reading_minutes}, 'a2': {'title': a2.title, 'min': a2.reading_minutes}, 'longer': longer}\n"
            ),
            result={"a1": {"slug": a1.slug, "title": a1.title, "minutes": a1.reading_minutes}, "a2": {"slug": a2.slug, "title": a2.title, "minutes": a2.reading_minutes}, "longer_title": longer},
            difficulty="hard",
            judge={
                "approach": "rinfo",
                "setup_sdk": "a1=c.list_articles(limit=10)[0]; a2=c.list_articles(limit=10)[1]",
                "checks": [
                    "must_include(answer, a1.title)",
                    "must_include(answer, a2.title)",
                    "must_include(answer, str(a1.reading_minutes))",
                    "must_include(answer, str(a2.reading_minutes))",
                    "must_include(answer, a1.title if a1.reading_minutes>=a2.reading_minutes else a2.title)",
                ],
            },
        )

        newest_top = c.list_articles(category="top-stories", limit=1)[0]
        add_task(
            instruction="In Top Stories, open the newest article and tell me the published date/time shown on the page.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    a=c.list_articles(category='top-stories',limit=1)[0]\n"
                "    result={'title': a.title, 'published_at': a.published_at, 'slug': a.slug}\n"
            ),
            result={"slug": newest_top.slug, "title": newest_top.title, "published_at": newest_top.published_at},
            difficulty="medium",
            judge={"approach": "rinfo", "setup_sdk": "a=c.list_articles(category='top-stories',limit=1)[0]", "checks": ["must_include(answer, a.published_at)"]},
        )

        arts80 = c.list_articles(limit=80)
        ar = next(a for a in arts80 if "Atmospheric River" in a.title)
        add_task(
            instruction="In the News section, find the article titled with “Atmospheric River”. Open it and tell me its full title and published date/time.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    a=next(x for x in c.list_articles(limit=80) if 'Atmospheric River' in x.title)\n"
                "    result={'title': a.title, 'published_at': a.published_at, 'slug': a.slug}\n"
            ),
            result={"slug": ar.slug, "title": ar.title, "published_at": ar.published_at},
            difficulty="hard",
            judge={
                "approach": "rinfo",
                "setup_sdk": "a=next(x for x in c.list_articles(limit=80) if 'Atmospheric River' in x.title)",
                "checks": ["must_include(answer, a.title)", "must_include(answer, a.published_at)"],
            },
        )

        # --- 26-35 Photos & Deals ---
        p0 = photos_default[0]
        add_task(
            instruction="Go to the Photos page, open the first photo card, and tell me the photo’s title.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    p=c.list_photos(limit=1)[0]\n"
                "    result={'id': p.id, 'title': p.title}\n"
            ),
            result={"id": p0.id, "title": p0.title},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "p=c.list_photos(limit=1)[0]", "checks": ["must_include(answer, p.title)"]},
        )

        add_task(
            instruction="On the Photos page, how many photos are shown on the first page before any loading/pagination? Reply with just the number.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    ps=c.list_photos()\n"
                "    result={'count': len(ps)}\n"
            ),
            result={"default_count": len(photos_default)},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "ps=c.list_photos()", "checks": ["exact_match(answer.strip(), str(len(ps)))"]},
        )

        newest_photo = max(photos_default, key=lambda p: p.published_at)
        add_task(
            instruction="In Photos, find the most recently published photo (from the first page) and tell me its title and published date/time.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    ps=c.list_photos()\n"
                "    p=max(ps, key=lambda x: x.published_at)\n"
                "    result={'id': p.id, 'title': p.title, 'published_at': p.published_at}\n"
            ),
            result={"id": newest_photo.id, "title": newest_photo.title, "published_at": newest_photo.published_at},
            difficulty="medium",
            judge={"approach": "rinfo", "setup_sdk": "ps=c.list_photos(); p=max(ps, key=lambda x: x.published_at)", "checks": ["must_include(answer, p.title)", "must_include(answer, p.published_at)"]},
        )

        cap_photo = next(p for p in photos_default if (p.caption or "").strip())
        cap10 = " ".join(cap_photo.caption.split()[:10])
        add_task(
            instruction="Open any photo detail that has a caption and paste the first 10 words of the caption.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    p=next(x for x in c.list_photos() if (x.caption or '').strip())\n"
                "    first10=' '.join(p.caption.split()[:10])\n"
                "    result={'id': p.id, 'first10': first10}\n"
            ),
            result={"id": cap_photo.id, "first10_words": cap10},
            difficulty="medium",
            judge={"approach": "rinfo", "setup_sdk": "p=next(x for x in c.list_photos() if (x.caption or '').strip()); first10=' '.join(p.caption.split()[:10])", "checks": ["must_include(answer, first10)"]},
        )

        add_task(
            instruction="Go to Deals and tell me the cheapest deal on the page, including its title and price in USD.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    ds=[d for d in c.list_deals() if d.price_usd is not None]\n"
                "    d=min(ds, key=lambda x: x.price_usd)\n"
                "    result={'id': d.id, 'title': d.title, 'price_usd': d.price_usd}\n"
            ),
            result={"id": cheapest_deal.id, "title": cheapest_deal.title, "price_usd": cheapest_deal.price_usd},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "ds=[d for d in c.list_deals() if d.price_usd is not None]; d=min(ds, key=lambda x: x.price_usd)", "checks": ["must_include(answer, d.title)", "must_include(answer, str(d.price_usd))"]},
        )

        add_task(
            instruction="On Deals, find the most expensive deal shown (first page) and report its title and price.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    ds=[d for d in c.list_deals() if d.price_usd is not None]\n"
                "    d=max(ds, key=lambda x: x.price_usd)\n"
                "    result={'id': d.id, 'title': d.title, 'price_usd': d.price_usd}\n"
            ),
            result={"id": priciest_deal.id, "title": priciest_deal.title, "price_usd": priciest_deal.price_usd},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "ds=[d for d in c.list_deals() if d.price_usd is not None]; d=max(ds, key=lambda x: x.price_usd)", "checks": ["must_include(answer, d.title)", "must_include(answer, str(d.price_usd))"]},
        )

        add_task(
            instruction="On the Deals page, how many deals (from the first page) are priced under $50? Reply with the number.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    ds=[d for d in c.list_deals() if d.price_usd is not None]\n"
                "    under=[d for d in ds if d.price_usd < 50]\n"
                "    result={'count_under_50': len(under)}\n"
            ),
            result={"count_under_50": len(under_50)},
            difficulty="medium",
            judge={"approach": "rinfo", "setup_sdk": "ds=[d for d in c.list_deals() if d.price_usd is not None]; under=[d for d in ds if d.price_usd < 50]", "checks": ["exact_match(answer.strip(), str(len(under)))"]},
        )

        add_task(
            instruction="On Deals, list all the distinct deal providers you see on the first page.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    ds=c.list_deals()\n"
                "    prov=sorted({d.provider for d in ds})\n"
                "    result={'providers': prov}\n"
            ),
            result={"providers": providers},
            difficulty="medium",
            judge={"approach": "rinfo", "setup_sdk": "ds=c.list_deals(); prov=sorted({d.provider for d in ds})", "checks": [*[f"must_include(answer, {p!r})" for p in providers]]},
        )

        some_deal = deals_default[0]
        add_task(
            instruction="Open the first deal card and copy the full ‘Shop now’ link URL.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    d=c.list_deals(limit=1)[0]\n"
                "    result={'id': d.id, 'cta_url': d.cta_url}\n"
            ),
            result={"id": some_deal.id, "cta_url": some_deal.cta_url},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "d=c.list_deals(limit=1)[0]", "checks": ["must_include(answer, d.cta_url)"]},
        )

        gd2 = gooddeals[:2]
        add_task(
            instruction="Filter the Deals list to provider ‘GoodDeals’ and tell me the titles of the first two items.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    ds=[d for d in c.list_deals() if d.provider=='GoodDeals']\n"
                "    result={'first_two_titles': [d.title for d in ds[:2]]}\n"
            ),
            result={"first_two_titles": [d.title for d in gd2]},
            difficulty="hard",
            judge={"approach": "rinfo", "setup_sdk": "ds=[d for d in c.list_deals() if d.provider=='GoodDeals']", "checks": ["must_include(answer, ds[0].title)", "must_include(answer, ds[1].title)"]},
        )

        # --- 36-46 Auth / account / saved locations / subscription ---
        with WeatherPortalClient(BASE_URL) as a:
            a.login(email="demo1@example.com", password="Password123!")
            me1 = a.me()
        add_task(
            instruction="Sign in with email demo1@example.com and password Password123!. On the account page, tell me the email shown and whether the account is marked as admin.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    c.login(email='demo1@example.com', password='Password123!')\n"
                "    me=c.me()\n"
                "    result={'email': me.email, 'is_admin': me.is_admin}\n"
            ),
            result={"email": me1.email, "is_admin": me1.is_admin},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "c.login(email='demo1@example.com',password='Password123!'); me=c.me()", "checks": ["must_include(answer, me.email)", "must_include(answer, 'true' if me.is_admin else 'false')"]},
        )

        with WeatherPortalClient(BASE_URL) as a:
            a.login(email="demo2@example.com", password="Password123!")
            saved2 = a.list_saved_locations()
        add_task(
            instruction="Log in as demo2@example.com with Password123! and go to Saved Locations. How many saved locations are listed? Reply with just the number.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    c.login(email='demo2@example.com', password='Password123!')\n"
                "    locs=c.list_saved_locations()\n"
                "    result={'count': len(locs)}\n"
            ),
            result={"saved_locations_count": len(saved2)},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "c.login(email='demo2@example.com',password='Password123!'); locs=c.list_saved_locations()", "checks": ["exact_match(answer.strip(), str(len(locs)))"]},
        )

        with WeatherPortalClient(BASE_URL) as a:
            a.login(email="demo3@example.com", password="Password123!")
            sub3 = a.get_subscription()
        add_task(
            instruction="Sign in as demo3@example.com with Password123! and check the Subscription section. Tell me whether the subscription is active, and the plan name.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    c.login(email='demo3@example.com', password='Password123!')\n"
                "    sub=c.get_subscription()\n"
                "    result=None if sub is None else {'status': sub.status, 'plan': sub.plan.name}\n"
            ),
            result=None if sub3 is None else {"status": sub3.status, "plan": sub3.plan.name},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "c.login(email='demo3@example.com',password='Password123!'); sub=c.get_subscription()", "checks": ["must_include(answer, sub.status)", "must_include(answer, sub.plan.name)"]},
        )

        user_loc_email = "taskgen_locations_20260103@example.com"
        user_loc_pw = "TaskPass123!"
        with WeatherPortalClient(BASE_URL) as u:
            state = ensure_user(u, email=user_loc_email, password=user_loc_pw, name="TaskGen Locations")
            me_u = u.me()
        add_task(
            instruction=f"Create an account with email {user_loc_email} and password {user_loc_pw}, then sign in. After you land on the account page, confirm the email shown matches exactly.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                "from weather_sdk.client import ApiError\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                f"    email={user_loc_email!r}; pw={user_loc_pw!r}\n"
                "    try: c.register(email=email, password=pw, name='TaskGen Locations')\n"
                "    except ApiError: c.login(email=email, password=pw)\n"
                "    me=c.me(); result={'email': me.email}\n"
            ),
            result={"state": state, "email": me_u.email},
            difficulty="hard",
            judge={"approach": "rinfo", "setup_sdk": f"# user signs up/in with {user_loc_email}; then API me()", "checks": [f"exact_match(answer.strip(), {user_loc_email!r})"]},
        )

        la_slug = loc_by_city["Los Angeles"].slug
        sd_slug = loc_by_city["San Diego"].slug
        with WeatherPortalClient(BASE_URL) as u:
            u.login(email=user_loc_email, password=user_loc_pw)
            existing = {x.slug for x in u.list_saved_locations()}
            for s in [la_slug, sd_slug]:
                if s in existing:
                    u.remove_saved_location(s)
            u.save_location(la_slug)
            saved_after = [x.slug for x in u.list_saved_locations()]
        add_task(
            instruction=f"Sign in with {user_loc_email} / {user_loc_pw}. Add Los Angeles, CA to your saved locations, then go to Saved Locations and make sure it appears in the list.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                f"    c.login(email={user_loc_email!r}, password={user_loc_pw!r})\n"
                "    la=c.search_locations('Los Angeles',limit=1)[0]\n"
                "    if la.slug in {x.slug for x in c.list_saved_locations()}:\n"
                "        c.remove_saved_location(la.slug)\n"
                "    c.save_location(la.slug)\n"
                "    result={'saved_slugs': [x.slug for x in c.list_saved_locations()]}\n"
            ),
            result={"expected_saved_contains": la_slug, "saved_slugs": saved_after},
            difficulty="medium",
            judge={"approach": "rprog", "setup_sdk": f"c.login(email={user_loc_email!r},password={user_loc_pw!r}); la=c.search_locations('Los Angeles',1)[0]", "checks": ["assert la.slug in {x.slug for x in c.list_saved_locations()}"]},
        )

        with WeatherPortalClient(BASE_URL) as u:
            u.login(email=user_loc_email, password=user_loc_pw)
            u.save_location(sd_slug)
            saved_now = sorted([x.slug for x in u.list_saved_locations()])
        add_task(
            instruction=f"While signed in as {user_loc_email}, add San Diego, CA as another saved location. Then tell me the two saved location names you see.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                f"    c.login(email={user_loc_email!r}, password={user_loc_pw!r})\n"
                "    sd=c.search_locations('San Diego',limit=1)[0]\n"
                "    c.save_location(sd.slug)\n"
                "    locs=c.list_saved_locations()\n"
                "    result={'names': [l.name for l in locs], 'slugs': [l.slug for l in locs]}\n"
            ),
            result={"saved_slugs_sorted": saved_now},
            difficulty="medium",
            judge={"approach": "rprog", "setup_sdk": f"c.login(email={user_loc_email!r},password={user_loc_pw!r})", "checks": [f"assert {la_slug!r} in {{x.slug for x in c.list_saved_locations()}}", f"assert {sd_slug!r} in {{x.slug for x in c.list_saved_locations()}}"]},
        )

        with WeatherPortalClient(BASE_URL) as u:
            u.login(email=user_loc_email, password=user_loc_pw)
            u.remove_saved_location(la_slug)
            saved_left = [x.slug for x in u.list_saved_locations()]
        add_task(
            instruction=f"Still signed in as {user_loc_email}, remove Los Angeles, CA from your saved locations. Then confirm San Diego is still saved.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                f"    c.login(email={user_loc_email!r}, password={user_loc_pw!r})\n"
                "    la=c.search_locations('Los Angeles',limit=1)[0]\n"
                "    c.remove_saved_location(la.slug)\n"
                "    result={'saved_slugs': [x.slug for x in c.list_saved_locations()]}\n"
            ),
            result={"saved_slugs": saved_left},
            difficulty="medium",
            judge={"approach": "rprog", "setup_sdk": f"c.login(email={user_loc_email!r},password={user_loc_pw!r})", "checks": [f"assert {la_slug!r} not in {{x.slug for x in c.list_saved_locations()}}", f"assert {sd_slug!r} in {{x.slug for x in c.list_saved_locations()}}"]},
        )

        user_sub_email = "taskgen_subscriber_20260103@example.com"
        user_sub_pw = "TaskPass123!"
        premium = plan_by_name["Premium Bundle"]
        basic = plan_by_name["Basic"]
        with WeatherPortalClient(BASE_URL) as u:
            state = ensure_user(u, email=user_sub_email, password=user_sub_pw, name="TaskGen Subscriber")
            sub = u.get_subscription()
            if sub is not None and sub.status == "active":
                u.cancel_subscription()
            sub_after = u.subscribe(premium.id)
        add_task(
            instruction=f"Sign in with {user_sub_email} / {user_sub_pw}. Go to Subscribe and subscribe to the Premium Bundle plan. Then confirm your subscription status is active and the plan name is Premium Bundle.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                "from weather_sdk.client import ApiError\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                f"    email={user_sub_email!r}; pw={user_sub_pw!r}\n"
                "    try: c.register(email=email, password=pw, name='TaskGen Subscriber')\n"
                "    except ApiError: c.login(email=email, password=pw)\n"
                "    plans=c.list_plans(); prem=[p for p in plans if p.name=='Premium Bundle'][0]\n"
                "    sub=c.get_subscription()\n"
                "    if sub is not None and sub.status=='active': c.cancel_subscription()\n"
                "    sub=c.subscribe(prem.id)\n"
                "    result={'status': sub.status, 'plan': sub.plan.name}\n"
            ),
            result={"state": state, "status": sub_after.status, "plan": sub_after.plan.name},
            difficulty="hard",
            judge={
                "approach": "rprog",
                "setup_sdk": f"c.login(email={user_sub_email!r},password={user_sub_pw!r})",
                "checks": ["sub=c.get_subscription(); assert sub is not None", "assert sub.status=='active'", "assert sub.plan.name=='Premium Bundle'"],
            },
        )

        with WeatherPortalClient(BASE_URL) as u:
            u.login(email=user_sub_email, password=user_sub_pw)
            u.cancel_subscription()
            after_cancel = u.get_subscription()
        add_task(
            instruction=f"While signed in as {user_sub_email}, cancel your subscription from the account/subscription settings. Then confirm it shows as canceled.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                f"    c.login(email={user_sub_email!r}, password={user_sub_pw!r})\n"
                "    c.cancel_subscription()\n"
                "    sub=c.get_subscription()\n"
                "    result={'status': None if sub is None else sub.status}\n"
            ),
            result=None if after_cancel is None else {"status": after_cancel.status, "plan": after_cancel.plan.name, "ends_at": after_cancel.ends_at},
            difficulty="medium",
            judge={"approach": "rprog", "setup_sdk": f"c.login(email={user_sub_email!r},password={user_sub_pw!r})", "checks": ["sub=c.get_subscription(); assert sub is not None", "assert sub.status=='canceled'"]},
        )

        with WeatherPortalClient(BASE_URL) as u:
            u.login(email=user_sub_email, password=user_sub_pw)
            sub_basic = u.subscribe(basic.id)
        add_task(
            instruction=f"Still signed in as {user_sub_email}, subscribe to the Basic plan. Then confirm your subscription is active and the plan name says Basic.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                f"    c.login(email={user_sub_email!r}, password={user_sub_pw!r})\n"
                "    basic=[p for p in c.list_plans() if p.name=='Basic'][0]\n"
                "    sub=c.subscribe(basic.id)\n"
                "    result={'status': sub.status, 'plan': sub.plan.name}\n"
            ),
            result={"status": sub_basic.status, "plan": sub_basic.plan.name},
            difficulty="medium",
            judge={
                "approach": "rprog",
                "setup_sdk": f"c.login(email={user_sub_email!r},password={user_sub_pw!r})",
                "checks": ["sub=c.get_subscription(); assert sub is not None", "assert sub.status=='active'", "assert sub.plan.name=='Basic'"],
            },
        )

        with WeatherPortalClient(BASE_URL) as u:
            u.login(email=user_sub_email, password=user_sub_pw)
            u.logout()
            err = None
            try:
                u.me()
            except Exception as e:
                err = str(e)
        add_task(
            instruction=f"Sign in with {user_sub_email} / {user_sub_pw}, then log out. After logging out, try to open the Account page again and confirm you’re no longer authenticated (it should behave like you’re signed out).",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                f"    c.login(email={user_sub_email!r}, password={user_sub_pw!r})\n"
                "    c.logout()\n"
                "    try:\n"
                "        c.me()\n"
                "        result='unexpectedly_authenticated'\n"
                "    except Exception as e:\n"
                "        result=str(e)\n"
            ),
            result={"me_after_logout_error": err},
            difficulty="hard",
            judge={"approach": "rprog", "setup_sdk": "Use API /me without Authorization", "checks": ["assert_unauthorized('/me')"]},
        )

        # --- 47-50 Mixed / harder reasoning ---
        user_multi_email = "taskgen_multi_20260103@example.com"
        user_multi_pw = "TaskPass123!"
        three = [loc_by_city["Dallas"], loc_by_city["Portland"], loc_by_city["Miami"]]
        with WeatherPortalClient(BASE_URL) as u:
            ensure_user(u, email=user_multi_email, password=user_multi_pw, name="TaskGen Multi")
            cur_saved = {x.slug for x in u.list_saved_locations()}
            for loc in three:
                if loc.slug in cur_saved:
                    u.remove_saved_location(loc.slug)
            for loc in three:
                u.save_location(loc.slug)
            names_sorted = sorted([loc.name for loc in u.list_saved_locations()])
        add_task(
            instruction=f"Create an account with {user_multi_email} / {user_multi_pw} (or sign in if it already exists). Save Dallas, Portland, and Miami as saved locations, then list the saved location names in alphabetical order.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                "from weather_sdk.client import ApiError\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                f"    email={user_multi_email!r}; pw={user_multi_pw!r}\n"
                "    try: c.register(email=email, password=pw, name='TaskGen Multi')\n"
                "    except ApiError: c.login(email=email, password=pw)\n"
                "    targets=[c.search_locations('Dallas',1)[0], c.search_locations('Portland',1)[0], c.search_locations('Miami',1)[0]]\n"
                "    saved={x.slug for x in c.list_saved_locations()}\n"
                "    for t in targets:\n"
                "        if t.slug in saved: c.remove_saved_location(t.slug)\n"
                "    for t in targets: c.save_location(t.slug)\n"
                "    names=sorted([x.name for x in c.list_saved_locations()])\n"
                "    result={'names_sorted': names}\n"
            ),
            result={"names_sorted": names_sorted},
            difficulty="hard",
            judge={"approach": "rinfo", "setup_sdk": f"c.login(email={user_multi_email!r},password={user_multi_pw!r}); names=sorted([x.name for x in c.list_saved_locations()])", "checks": ['exact_match(answer.strip(), "\\n".join(names))  # or compare list order if judge parses lines']},
        )

        ny = loc_by_city["New York"]
        mi = loc_by_city["Miami"]
        cur_ny = c.current(ny.slug)
        cur_mi = c.current(mi.slug)
        h_ny = float(cur_ny.humidity_percent or 0.0)
        h_mi = float(cur_mi.humidity_percent or 0.0)
        more_humid = ny.name if h_ny >= h_mi else mi.name
        add_task(
            instruction="Compare the current humidity for New York, NY and Miami, FL on the site. Tell me which one is more humid right now, and include both humidity percentages.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    ny=c.search_locations('New York',1)[0]; mi=c.search_locations('Miami',1)[0]\n"
                "    cny=c.current(ny.slug); cmi=c.current(mi.slug)\n"
                "    hny=float(cny.humidity_percent or 0.0); hmi=float(cmi.humidity_percent or 0.0)\n"
                "    result={'ny_humidity': cny.humidity_percent, 'mi_humidity': cmi.humidity_percent, 'more_humid': 'New York' if hny>=hmi else 'Miami'}\n"
            ),
            result={"ny_humidity_percent": cur_ny.humidity_percent, "mi_humidity_percent": cur_mi.humidity_percent, "more_humid": more_humid},
            difficulty="medium",
            judge={
                "approach": "rinfo",
                "setup_sdk": "ny=c.search_locations('New York',1)[0]; mi=c.search_locations('Miami',1)[0]; cny=c.current(ny.slug); cmi=c.current(mi.slug)",
                "checks": [
                    "must_include(answer, str(cny.humidity_percent))",
                    "must_include(answer, str(cmi.humidity_percent))",
                    "must_include(answer, 'New York' if float(cny.humidity_percent or 0)>=float(cmi.humidity_percent or 0) else 'Miami')",
                ],
            },
        )

        prem = plan_by_name["Premium Bundle"]
        add_task(
            instruction="On the Subscribe page, check the Premium Bundle plan features. Does it include “Premium radar layers”? Answer yes/no and quote the feature text exactly.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    prem=[p for p in c.list_plans() if p.name=='Premium Bundle'][0]\n"
                "    result={'has_feature': 'Premium radar layers' in prem.features, 'features': prem.features}\n"
            ),
            result={"has_feature": ("Premium radar layers" in prem.features), "features": prem.features},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "prem=[p for p in c.list_plans() if p.name=='Premium Bundle'][0]", "checks": ["must_include(answer.lower(), 'yes' if 'Premium radar layers' in prem.features else 'no')", "must_include(answer, 'Premium radar layers')"]},
        )

        add_task(
            instruction="On the Subscribe page, tell me the monthly price (USD) of the Premium Bundle plan.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    prem=[p for p in c.list_plans() if p.name=='Premium Bundle'][0]\n"
                "    result={'price_monthly_usd': prem.price_monthly_usd}\n"
            ),
            result={"plan": prem.name, "price_monthly_usd": prem.price_monthly_usd},
            difficulty="easy",
            judge={"approach": "rinfo", "setup_sdk": "prem=[p for p in c.list_plans() if p.name=='Premium Bundle'][0]", "checks": ["must_include(answer, str(prem.price_monthly_usd))"]},
        )

        sd = loc_by_city["San Diego"]
        d_sd = c.daily(sd.slug)[1]
        add_task(
            instruction="Open the 10-day forecast for San Diego, CA and tell me tomorrow’s high and low in °C.",
            tool_call=(
                "from weather_sdk import WeatherPortalClient\n"
                f"with WeatherPortalClient({BASE_URL!r}) as c:\n"
                "    sd=c.search_locations('San Diego',1)[0]\n"
                "    d=c.daily(sd.slug)[1]\n"
                "    result={'date': d.date, 'high_c': d.temp_max_c, 'low_c': d.temp_min_c}\n"
            ),
            result={"city": sd.name, "date": d_sd.date, "high_c": safe_round(d_sd.temp_max_c, 1), "low_c": safe_round(d_sd.temp_min_c, 1)},
            difficulty="medium",
            judge={"approach": "rinfo", "setup_sdk": "sd=c.search_locations('San Diego',1)[0]; d=c.daily(sd.slug)[1]", "checks": ["must_include(answer, str(round(d.temp_max_c, 1)))", "must_include(answer, str(round(d.temp_min_c, 1)))"]},
        )

        if len(tasks) != 50:
            raise SystemExit(f"Expected 50 tasks, got {len(tasks)}")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

    print("Wrote", OUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


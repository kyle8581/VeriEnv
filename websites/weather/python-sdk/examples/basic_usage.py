from __future__ import annotations

from weather_sdk import WeatherPortalClient


def main() -> None:
    api = "http://localhost:12142"

    with WeatherPortalClient(api) as c:
        print("health:", c.health())

        c.login(email="demo1@example.com", password="Password123!")
        print("me:", c.me().email)

        loc = c.search_locations("Los", limit=1)[0]
        print("location:", loc.name, loc.state, loc.slug)

        cur = c.current(loc.slug)
        print("current:", cur.temperature_c, cur.weather.get("label"))

        arts = c.list_articles(category="top-stories", limit=3)
        print("top stories:", [a.slug for a in arts])

        plans = c.list_plans()
        print("plans:", [p.name for p in plans])


if __name__ == "__main__":
    main()


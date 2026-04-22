# Weather Portal SDK

Install for development:

```bash
pip install -e .
```

## Quickstart

```python
from weather_sdk import WeatherPortalClient

with WeatherPortalClient("http://localhost:12142") as c:
    c.login(email="demo1@example.com", password="Password123!")
    la = c.search_locations("Los", limit=1)[0]
    print(c.current(la.slug))
```

## Features
- Authentication helpers (register/login/refresh/logout)
- Typed clients for locations, content, weather, saved locations, subscriptions
- Example: `examples/basic_usage.py`


# discogs-sdk

Python SDK for the Discogs clone API.

## Install (editable)

From the repository root:

```bash
pip install -e sdk/python
```

## Usage

By default, the SDK targets the **public API proxy** served by the web app:

- `http://localhost:12042/api/backend`

```python
from discogs_sdk import DiscogsClient

client = DiscogsClient()

# Public endpoints
home = client.home()
genres = client.genres()
rock = client.genre_overview("rock")

# Auth (seeded demo user)
client.login("demo", "password123")

cart = client.cart()
```


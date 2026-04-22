# apartments-sdk

Python SDK for the Apartments clone API (auth + listings search + favorites + saved searches + contact requests).

## Install (editable)

From the repo root:

```bash
pip install -e ./sdk
```

## Quick start

```python
from apartments_sdk import ApartmentsClient

client = ApartmentsClient(base_url="http://127.0.0.1:19001")

# Create account + sign in
client.register(email="you@example.com", password="change-me-please", full_name="You")
client.login(email="you@example.com", password="change-me-please")

# Search
results = client.search_listings(q="Boston, MA", min_beds=2, sort="price_asc", limit=5)
print(results.total, [l.name for l in results.items])

# Favorite
client.add_favorite(results.items[0].id)

# Contact (Email CTA)
client.create_contact_request(
    listing_id=results.items[0].id,
    contact_email="you@example.com",
    contact_name="You",
    message="Hi! Is this unit still available?",
)
```


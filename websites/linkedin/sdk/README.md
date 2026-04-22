# linkedin-clone-sdk

Python SDK for this repository’s LinkedIn clone backend API.

## Install (editable)

From the repo root:

```bash
python3 -m pip install -e ./sdk
```

## Quickstart

```python
from linkedin_clone_sdk import LinkedInCloneClient

client = LinkedInCloneClient(base_url="http://127.0.0.1:12079")
client.login("jane.doe@example.com", "password123")

me = client.me()
print(me["email"])

feed = client.feed(limit=5)
print(len(feed["items"]))
```

## Local DB helper (optional)

If you are running the backend locally with SQLite, you can also open the DB file directly:

```python
from linkedin_clone_sdk import LocalSqliteDb

db = LocalSqliteDb("../backend/var/app.db")
print(db.scalar("select count(*) from users"))
```


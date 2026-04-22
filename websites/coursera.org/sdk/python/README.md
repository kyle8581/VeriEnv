# coursera-sdk

Python SDK for the clone API.

## Install (editable)

```bash
python -m pip install -e .
```

## Quickstart

```python
from coursera_sdk import CourseraClient

client = CourseraClient(base_url="http://127.0.0.1:12038")
client.login(email="learner@example.com", password="learner1234")

courses = client.list_courses(limit=5)
print(courses["total"], courses["items"][0]["title"])
```


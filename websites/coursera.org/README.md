# coursera.org (clone-coding)

This workspace implements a production-style clone of the reference screenshots (Coursera for Campus marketing site + “Job Skills of 2023 Report” ebook lead form), backed by a real API, database with realistic seed data, and a Python SDK.

## What’s included

- **Frontend**: Next.js app in `frontend/`
- **Backend**: FastAPI app in `backend/`
- **DB**: SQLite at `backend/data/app.db` (seeded with realistic data)
- **Python SDK**: `sdk/python` (`coursera_sdk.CourseraClient`)
- **Docs**:
  - `website_description.md` (structured spec derived from screenshots)
  - `docs/implementation_log.md` (detailed implementation log)
  - `todo.md` (Linear-style progress tracking)

## Run locally

Start:

```bash
./start_servers.sh
```

Stop / reset DB back to initial seed:

```bash
./reset_servers.sh reset
```

Stop only:

```bash
./reset_servers.sh stop
```

Ports are based on `ports.json`:

- **Backend**: `PORT` (default `12038`)
- **Frontend**: `PORT + 1` (default `12039`)

Backend OpenAPI docs: `http://127.0.0.1:12038/docs`

## Seeded accounts

- **Admin**: `admin@example.com` / `adminadmin`
- **Learner**: `learner@example.com` / `learner1234`


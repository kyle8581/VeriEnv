# Discogs Clone (Full-Stack)

This project is a production-oriented Discogs-like clone implemented from the provided screenshots.

## Stack

- **Frontend**: Next.js (App Router) + Tailwind
- **Backend**: FastAPI
- **DB**: Postgres (via `docker compose`)
- **SDK**: Python client library for the API

## Ports

- **Frontend**: `12042`
- **Backend (internal)**: `12160` (FastAPI; proxied through the frontend)

## Quick start (local)

1) Copy env file:

```bash
cp .env.example .env
```

2) Reset/seed the local DB (SQLite):

```bash
./reset_servers.sh
```

3) Start servers:

```bash
./start_servers.sh
```

## Progress tracking

- `todo.md` is the canonical task list.
- Optional Linear sync:
  - Set `LINEAR_API_KEY` and `LINEAR_TEAM_ID`
  - Run `python scripts/linear_sync.py`

## API access

The externally reachable API is served via the Next.js app:

- Base URL: `http://localhost:12042/api/backend`

This path proxies to the internal FastAPI server.


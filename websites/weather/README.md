# Weather Portal (Production-ready clone)

This repository implements a Weather.com-style portal with:
- **Frontend**: Next.js (UI matching screenshots)
- **Backend API**: FastAPI + SQLite (auth, content, locations, weather, subscriptions)
- **Python SDK**: first-party client for the API (auth + typed endpoints)

## Local development

### Prereqs
- Node.js 20+
- Python 3.11+

### Ports
The website should be available on:
- Frontend: `http://localhost:12141` (from `ports.json`)
- Backend API: `http://localhost:12142`

### One-command start

```bash
./start_servers.sh
```

### Reset DB/server state

```bash
./reset_servers.sh
```

## Project layout
- `frontend/` Next.js app
- `backend/` FastAPI service
- `python-sdk/` installable SDK package
- `website_description.md` spec derived from screenshots
- `implementation_log.md` detailed build log
- `todo.md` Linear-style progress tracking


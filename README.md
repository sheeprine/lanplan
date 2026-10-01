# LAN Plan

Self-hosted LAN party planner: a calendar for who's showing up and when,
what games are scheduled, and a per-person inventory of what everyone's
bringing.

Python backend (FastAPI), server-rendered pages (Jinja2 + HTMX), SQLite
storage. Everything runs in one container so it works fine on a LAN with
no internet access.

## Running it

```bash
cp .env.example .env
# edit .env: set PARTY_PASSWORD and SECRET_KEY

docker compose up -d --build
```

Then visit `http://<host>:8000`. Everyone enters the shared `PARTY_PASSWORD`,
then picks (or creates) their own name — no individual accounts needed.

Data persists in `./data/lanplan.db` (SQLite file on a bind-mounted volume).

## Features

- **Calendar** (`/calendar`) — a 7-day grid. Each person marks when they'll
  be arriving/leaving; scheduled game sessions show up on the same grid.
- **Games** (`/games`) — add games, schedule sessions (start/end time +
  notes), and join/leave sessions.
- **Inventory** (`/inventory`) — each person manages their own list of
  what they're bringing (name, category, quantity, notes); everyone can see
  everyone else's list.

## Development (without Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PARTY_PASSWORD=dev PARTY_NAME=Dev SECRET_KEY=dev-secret DATABASE_PATH=./data/lanplan.db
mkdir -p data
uvicorn app.main:app --reload
```

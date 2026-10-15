# Option A — Single Agent

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
```

## Run

```bash
python app/app.py
```

Serves on http://localhost:5001 — check http://localhost:5001/health.

## Architecture

One Flask process, one agent. The three upcoming capabilities (task CRUD,
due-date urgency surfacing, cost tracking) are plain functions called
directly in-process — no inter-process messaging, no orchestrator. This is
locked in before any capability code exists; see first commit message.

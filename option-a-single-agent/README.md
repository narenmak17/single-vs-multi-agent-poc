# Option A — Task Tracker (single agent, multi-skill)

A small shared to-do list: add a task, give it an optional due date, tick it off.
Anything due within 24 hours (or already overdue) and not done is flagged and pinned to the top.
It is one half of a comparison: this version was built by a single Claude Code agent using
several skills; Option B builds the same [SPEC.md](SPEC.md) with multiple orchestrated agents.

## Requirements

- Python 3.12 (3.10+ works; the code uses `X | None` type hints)
- Flask 3.0.3 and pytest 9.1.1, pinned in `requirements.txt`
- Git
- Optional, only for the build telemetry and guardrail 4: Docker Desktop

## Setup

```bash
git clone <repo-url> option-a-single-agent
cd option-a-single-agent

python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
sh hooks/install.sh             # installs the pre-push guardrail hook

python app/app.py
```

Open http://127.0.0.1:5001. Tasks are stored in `app/tasks.db` (created on first run, git-ignored).

## Using it

1. **Create a task**: type a title, optionally pick a due date and time, press **Add**.
   A date with no time means the end of that day.
2. **Mark done**: tick the checkbox. Untick to reopen.
3. **Due-soon reminder**: open tasks due within 24 hours, including overdue ones, move to
   **Due within 24 hours** at the top, tagged **Overdue** or **Due soon**. The browser tab shows
   the count, e.g. `(2) Tasks`, and the page re-checks every minute.

The same three capabilities are available as a JSON API:

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/api/tasks` | — | `[Task, ...]`, each with a computed `reminder` boolean |
| POST | `/api/tasks` | `{"title": "...", "due_at": "2026-10-18" or "2026-10-18T09:30" or null}` | `201` `Task` |
| PATCH | `/api/tasks/<id>` | `{"done": true}` | `Task` |

## Build cost and telemetry

The token usage, cost and tool accept/reject data for **building** this app lives in this
option's Grafana dashboard, not in the app:

**http://localhost:3000/d/claude-code-overview**

The build session was started with `start-claude.cmd`, which points Claude Code's
OpenTelemetry export at the local stack in `observability/` (Grafana, Loki, Mimir, Tempo
and an OTel Collector). To bring the stack up and check it:

```bash
cd observability && docker compose up -d && cd ..
pwsh -File observability/check-telemetry.ps1
```

See [observability/README.md](observability/README.md) for details.

## More

Architecture, guardrails, and how to extend it: [DEVELOPER-GUIDE.md](DEVELOPER-GUIDE.md).

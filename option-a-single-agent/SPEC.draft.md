# Team To-Do — Spec (Option A draft)

Single shared to-do list. Jot a task, optionally give it a due date, tick it off.
Anything overdue or due soon and still open is shown first, without searching.

Architecture (locked in `cf895d3`): one Flask process, one agent. Capabilities are
plain functions called in-process. No inter-process messaging, no orchestrator.

## 1. Capabilities

1. **Task store** — create, list, edit, toggle done, delete; SQLite persistence.
   *Separable:* pure data CRUD, no knowledge of dates-vs-today or cost.
2. **Urgency** — classify each task from `due_date` vs today; sort attention-first.
   *Separable:* pure function of (task, today, window); no I/O, testable alone.
3. **Observability** — structured request logs + `/metrics` endpoint for the app;
   build cost of this session tracked via Claude Code OTel → Grafana :3000 and
   `scripts/session-cost.ps1`.
   *Separable:* cross-cutting; reads state, never changes task behaviour.

## 2. Data model

`Task` (SQLite table `tasks`)

| Field | Type | Rules |
|---|---|---|
| `id` | integer | PK, autoincrement |
| `title` | text | required, trimmed, 1–200 chars |
| `due_date` | text `YYYY-MM-DD` \| null | optional, valid ISO date |
| `done` | boolean | default `false` |
| `created_at` | text ISO-8601 UTC | set on create |
| `completed_at` | text ISO-8601 UTC \| null | set when `done` → true, cleared when → false |

Derived, never stored: `urgency` ∈ `overdue` · `due_today` · `due_soon` · `later` · `no_date` · `done`.

- `done` if `done` is true (overrides everything)
- `overdue` if `due_date < today`
- `due_today` if `due_date == today`
- `due_soon` if `today < due_date ≤ today + SOON_DAYS` (default `SOON_DAYS=2`, env-configurable)
- `later` if further out; `no_date` if `due_date` is null
- "today" = server local date.

Sort order: overdue (oldest first) → due_today → due_soon (soonest first) → later → no_date (newest first) → done (most recently completed first).

## 3. API contract

All JSON. Errors: `{"error": "<message>"}`.

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| GET | `/health` | — | `200 {"status":"ok"}` | — |
| GET | `/api/tasks` | — | `200 [Task+urgency]` sorted as above | — |
| POST | `/api/tasks` | `{"title": str, "due_date"?: "YYYY-MM-DD"\|null}` | `201 Task+urgency` | `400` bad title/date |
| PATCH | `/api/tasks/<id>` | any of `title`, `due_date`, `done` | `200 Task+urgency` | `400` invalid, `404` unknown id |
| DELETE | `/api/tasks/<id>` | — | `204` | `404` |
| GET | `/metrics` | — | `200` JSON, see §5 | — |
| GET | `/` | — | `200` HTML page | — |

## 4. UI

Single server-rendered page at `/`, no build step.

- **Needs attention** block at top: overdue (red, shows "N days overdue"), due today (amber), due soon (yellow, "due in N days"). Hidden-not-absent: shows "Nothing urgent" when empty.
- Add form: title + optional date picker.
- Remaining open tasks below (later, no date), then a collapsed **Done** section.
- Each row: checkbox to toggle done, inline edit, delete.
- Count of urgent tasks in the page `<title>` so it's visible from a tab.

## 5. Observability

- **Logs:** one structured JSON line per request: `ts`, `method`, `path`, `status`, `duration_ms`. Task mutations also log `event` (`task_created|task_updated|task_completed|task_deleted`) + `task_id`. No task titles in logs.
- **`/metrics`** returns:
  ```json
  {"tasks_total": 0, "tasks_open": 0, "tasks_done": 0,
   "tasks_overdue": 0, "tasks_due_today": 0, "tasks_due_soon": 0,
   "requests_total": 0, "uptime_seconds": 0}
  ```
- **Build cost:** Claude Code telemetry (logs/metrics/traces) to Grafana :3000 via `start-claude.cmd`. `scripts/session-cost.ps1` reports tokens, cost, API calls per prompt for a session ID — the A-vs-B comparison number.

## 6. Guardrails

Each checkable by `scripts/validate.ps1`; any failure → non-zero exit.

1. **Tests pass** — `pytest` exits 0.
2. **API shape** — boots the app on a temp DB, hits every route in §3, asserts status codes and required keys.
3. **Metrics present** — `/metrics` returns every key in §5 with integer values.
4. **No debug leftovers** — no `print(`, `breakpoint(`, `pdb`, `debug=True`, `console.log` in `app/`.
5. **No secrets** — no matches for key/token/password patterns (`sk-`, `AKIA`, `ghp_`, `-----BEGIN`, `password\s*=`) in tracked files; `.env` not tracked.
6. **Port** — app binds `5001`.
7. **Dependencies pinned** — every line in `requirements.txt` uses `==`.

## 7. Validation script + pre-push hook

- `scripts/validate.ps1` runs guardrails 1–7, prints `[PASS]/[FAIL] <n> <name>` per check, exits non-zero on any failure.
- `hooks/pre-push` calls it; installed via `git config core.hooksPath hooks`. Push is blocked on failure.

## 8. Out of scope

Auth, users, teams, assignees, notifications/email, recurring tasks, priorities, tags,
search, multi-list, time-of-day due times, timezones beyond server local, deployment,
in-app hosting-cost tracking.

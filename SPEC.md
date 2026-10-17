# Shared Spec — Task Tracker POC

Both options build this exact spec. Architecture is the only variable. Read this before either prompt.

## Capabilities (3)

1. **Create task** — title (required), optional due date.
2. **Mark done** — toggle a task's `done` state.
3. **Due-soon reminder** — any task due within 24h and not done is flagged `reminder: true` in the API response. (Deliberately separable: different trigger — time, not a click — and a different failure mode — a missed flag is silent, not a 500.)

## Data model

```
Task: { id, title, due_at (nullable ISO date), done (bool), created_at }
```

## API contract (both options expose exactly this)

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/api/tasks` | — | `[Task, ...]` each with computed `reminder` field |
| POST | `/api/tasks` | `{title, due_at?}` | `Task` |
| PATCH | `/api/tasks/<id>` | `{done: bool}` | `Task` |

## UI (both options)

Single page: add-task form, task list with done-checkbox, due-soon tasks visibly flagged. Plain HTML/CSS, no framework needed.

## Observability (both options, required)

Real telemetry from the build-time Claude Code session, not a simulated figure inside the app. Each option runs its own local Grafana LGTM stack (Mimir + Tempo + Loki + Grafana, fronted by an OTel Collector) and points its Claude Code session at it for the entire build, so token usage, cost, tool-decision accept/reject, and session data are actual numbers, not illustrative placeholders.

Copy the stack from `D:\PERSONAL\AI_TIPS\teaching\hands_demo\03\demos\after\docker` into each option's own `observability/` folder, with Option B's ports remapped so both stacks can run at the same time:

| Service | Option A port | Option B port |
|---|---|---|
| Grafana UI | `3000` | `3001` |
| OTel Collector (gRPC) | `4317` | `4327` |
| OTel Collector (HTTP) | `4318` | `4328` |
| OTel Collector internal metrics | `8888` | `8889` |

Give Option B's `docker-compose.yml` its own container names, volume names, and network name (suffix `-b` or similar) so both stacks can run simultaneously without colliding, even with ports remapped.

Before starting each option's build session, export the OTel env vars pointing at that option's own collector (gRPC endpoint, the usual `CLAUDE_CODE_ENABLE_TELEMETRY=1` set), per the stack's own README. At the end of the build, each option's Grafana dashboard (`http://localhost:3000` / `:3001`) is the real metrics comparison point — not an app-level `/api/metrics` endpoint.

## Ports (run both simultaneously)

- Option A app (single agent, multi-skill): **port 5001**. Observability stack: Grafana `3000`, collector `4317`/`4318`/`8888`.
- Option B app (multi-agent, orchestrated): **port 5002**. Observability stack: Grafana `3001`, collector `4327`/`4328`/`8889`.

## Out of scope

User auth, persistence beyond SQLite/JSON file, deployment, styling polish beyond "clean and legible."

## Guardrails (both options, required)

These are the acceptance gates for this spec — not suggestions. Each one must be checked by an automated script before the work is considered done, and that script is wired into a git `pre-push` hook so a violation is caught locally, before code reaches GitHub, not after.

1. **API contract match** — `GET /api/tasks`, `POST /api/tasks`, `PATCH /api/tasks/<id>` exist with exactly the request/response shapes in the API contract table above. No extra required fields, no renamed fields.
2. **Tests pass** — the test suite written in the follow-up test-case prompt must pass (`pytest`, exit code 0) before a push is allowed.
3. **No debug leftovers** — no `print(`, `pdb.set_trace(`, or `debug=True` left in anything that isn't the local dev entrypoint guard (`if __name__ == "__main__":`).
4. **Observability stack reachable** — that option's Grafana (`:3000` or `:3001`) and OTel Collector respond, and the Claude Code session building this option is actually configured to export telemetry to it (the `OTEL_EXPORTER_OTLP_ENDPOINT` env var is set to that option's collector).
5. **No secrets** — no API keys, tokens, or credentials committed in any tracked file.

### Validation script

Each option implements this as a single script, `scripts/validate.py` (or `.sh` — pick one, be consistent), that checks all five guardrails and exits non-zero with a clear, numbered reason if any fail. It must be runnable two ways:

- Directly: `python scripts/validate.py` — for a developer checking locally before committing.
- Via a git hook: `.git/hooks/pre-push` calls the same script and blocks the push on failure.

### Hook wiring

Add a tracked `hooks/pre-push` file (git hooks themselves live outside version control under `.git/hooks/`, so the tracked copy is the source of truth) plus a one-line `hooks/install.sh` that copies it into `.git/hooks/pre-push` and `chmod +x`'s it. Document this install step in `DEVELOPER-GUIDE.md` — a hook that's never installed teaches nothing on camera.

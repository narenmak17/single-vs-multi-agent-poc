# Developer Guide — Option A

For anyone extending or maintaining this app. For running it, see [README.md](README.md).
The spec of record is [SPEC.md](SPEC.md), a verbatim copy of the shared `../SPEC.md` that
both options build against.

## Architecture

One Flask process. The three capabilities are plain Python functions in
`app/capabilities.py`, and the route handlers in `app/app.py` call them directly:

```
browser ──HTTP──▶ app.py (routes) ──call──▶ capabilities.py ──SQL──▶ SQLite (app/tasks.db)
                                              create_task
                                              mark_done
                                              due_soon_reminder
```

There are no services, no queues and no orchestrator. That is the variable this
comparison measures: Option B builds the same spec with multiple orchestrated agents.
The decision was locked in the first commit (`cf895d3`), before any capability code existed.

Why plain functions and not services:

- **Each capability is tiny.** A create, an update, and a date comparison. A process
  boundary would cost more code than the capability itself.
- **They share one table.** Splitting them would mean either a shared database (still
  coupled) or copies kept in sync (a new failure mode the spec never asked for).
- **They stay separable without being separate.** `due_soon_reminder` is a pure function
  of `(task, now)` with no I/O, so it can be tested with a fixed clock. That is the
  separation SPEC.md cares about: a missed reminder fails silently, so it must be
  testable on its own.

## File map

| Path | What it is |
|---|---|
| `app/app.py` | `create_app(db_path)` factory: routes for `/`, `/health` and the three `/api/tasks` endpoints. Validates request bodies and maps errors to `400`/`404`. Run directly, it serves on port 5001. |
| `app/capabilities.py` | The three capabilities: `create_task`, `mark_done`, `due_soon_reminder`, plus `parse_due_at`. |
| `app/models.py` | `Task` dataclass, the SQLite schema, `connect()` (commits and **closes**) and `init_db()`. `TASKS_DB` env var overrides the DB path. |
| `app/templates/index.html` | The single page: plain HTML, CSS and JS, no framework. Talks to the JSON API. |
| `scripts/validate.py` | Checks the five guardrails and exits non-zero with numbered reasons. |
| `hooks/pre-push` | Tracked copy of the git hook. Runs `validate.py` and blocks the push on failure. |
| `hooks/install.sh` | Copies `hooks/pre-push` into `.git/hooks/` and makes it executable. |
| `.gitattributes` | Keeps hook scripts LF, so `sh` can run them on Windows clones. |
| `tests/` | The pytest suite (added in Prompt 8). |
| `start-claude.cmd` | Launches Claude Code with telemetry pointed at this option's collector (`localhost:4317`). |
| `observability/` | Local Grafana + Loki + Mimir + Tempo + OTel Collector stack, and `check-telemetry.ps1`. |
| `SPEC.md` | Spec of record. |
| `SPEC.draft.md` | Untracked. The pre-comparison draft, kept only for the write-up. |

## How it was built: the spec-driven workflow

1. **Business requirement**: a plain-language ask ("tasks slip past their date and nobody
   notices"), restated with its entities, implied needs and ambiguities named before any code.
2. **Spec**: turned into a written contract (data model, API table, UI, observability,
   guardrails), compared against the ratified `../SPEC.md`, and the ratified version adopted.
3. **Task-by-task build**, with a checkpoint after each task where the work was summarised,
   checked against a named spec section, and the next task started only on approval:
   1. Data model → `models.py`
   2. API endpoints → `app.py`
   3. Capability functions → `capabilities.py` (this resolved the open decisions: overdue counts
      as due soon, a date-only `due_at` means end of day)
   4. UI → `templates/index.html`
4. **Guardrail validation**: `scripts/validate.py` was written and run against the build.
   Its first run caught a real bug: SQLite connections were never closed.
5. **Hook**: `hooks/pre-push` was installed, then proven by committing a stray `print()`,
   watching the push get blocked with the violation named, fixing it, and pushing clean.

## Guardrails

Run them directly any time:

```bash
python scripts/validate.py          # with the venv active
```

Each check prints `[PASS]`, `[FAIL]` (with the reasons underneath) or `[SKIP]`. The exit code is
`1` if any check fails.

| # | Check | What it verifies |
|---|---|---|
| 1 | API contract match | Boots the app on a throwaway DB. The three routes exist. `POST` and `PATCH` return exactly `id, title, due_at, done, created_at`, and `GET` items have those fields plus a boolean `reminder`. |
| 2 | Tests pass | `pytest tests/` exits 0. **Skips** (passes with a note) while `tests/` has no test files. |
| 3 | No debug leftovers | Parses every committable `.py` file (AST, not grep) for `print(`, `breakpoint(`, `pdb.set_trace(`, `debug=True`. Allowed inside `if __name__ == "__main__":`. |
| 4 | Observability stack reachable | Grafana `localhost:3000/api/health` is healthy, the collector's `localhost:8888/metrics` responds, ports 4317/4318 accept connections, and `start-claude.cmd` sets `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317`. |
| 5 | No secrets | No `.env` files, and no API key, token, private key or hard-coded credential patterns in any tracked or committable file. |

Check 4 reads the launcher, not `$OTEL_EXPORTER_OTLP_ENDPOINT`, because Claude Code strips
`OTEL_*` variables from the subprocesses it runs, and a hook run from a plain terminal
wouldn't have them either.

### Reinstalling the hook on a fresh clone

Git does not clone hooks. After every fresh clone:

```bash
sh hooks/install.sh
```

If you edit `hooks/pre-push`, run it again: the installed copy in `.git/hooks/` does not update
by itself. To bypass the hook in an emergency, use `git push --no-verify`, and fix it after.

## Adding a fourth capability

1. **Spec first.** Add it to `SPEC.md` with its API row and a one-line reason it is separable.
   Both options build the same spec, so a change here is a change for Option B too.
2. **Write the function** in `capabilities.py`. Keep it a plain function. Prefer a pure function
   over `Task` and an injected `now`, and take a `conn` only if it must touch the DB.
3. **Don't change existing response shapes.** Guardrail 1 asserts the exact field list for
   `Task`. If the new capability is a computed field like `reminder`, add it to the `GET` item
   only and update `TASK_FIELDS`/the `GET` check in `validate.py` in the same commit.
4. **Schema changes need a migration.** `init_db` runs `CREATE TABLE IF NOT EXISTS`, which
   never alters an existing `tasks.db`. Add a nullable column with an explicit `ALTER TABLE`
   path, or existing databases will crash on the new column.
5. **Add a route** in `app.py` that validates input, calls the function and maps `ValueError`
   to `400`. No business logic in the route.
6. **Add tests**, including the boundary cases, and run `python scripts/validate.py` before pushing.
   The hook will run it anyway.

## Known limitations

- **No auth, one shared list.** Out of scope by spec.
- **Flask development server.** Fine for a local POC, not for deployment.
- **Time zones.** Times without a zone, and date-only due dates, are interpreted in the
  server's local time. The overdue/due-soon tag text is computed in the browser from its
  clock; the `reminder` flag itself always comes from the server.
- **The reminder only shows on the page.** Nothing notifies anyone who isn't looking at it.
- **No schema migrations** (see step 4 above).
- **The hook validates the working tree, not the exact commits being pushed.** Uncommitted
  changes are what get checked. Commit or stash before pushing for an accurate result.
- **Guardrail 4 needs Docker running.** With the stack down, pushes are blocked by design.
- **Guardrail 2 skips until tests exist**, so it is a no-op until the test suite lands.
- **The secret scan is pattern-based.** It catches common key formats, not every secret.
- **The debug check is Python-only.** It doesn't look for `console.log` in the template.
- **The page loads fonts from Google Fonts**; offline it falls back to system fonts.
- **No remote is configured.** The hook was proven against a throwaway local bare repo.

# Prompt 4 of 8 — Build, One Task at a Time

**Project folder:** `D:/PERSONAL/AI_TIPS/career/linkedin-hub/posts/2026-10-single-vs-multi-agent/poc/option-a-single-agent`

`../SPEC.md` is the spec of record. Build against it, nothing more.

---

> Build the three capabilities against `../SPEC.md`, one task at a time, on top of the skeleton from Prompt 1. One Flask app, one process — the three capabilities as plain functions called directly, no orchestrator.
>
> **Ground rules:**
> - One task at a time. Don't start task N+1 until I confirm task N.
> - After each task: summarize what you built, which spec section it was checked against, and what's left. Wait for my go-ahead before continuing.
> - Use fable-mode to scope each task against the spec before coding it, and to verify the result before calling it done.
> - Use `rtk` for file reads, greps, and git/test output throughout. Save `rtk gain` for Prompt 8.
> - Use frontend-design for the UI task.
>
> **Tasks:**
> 1. Data model — the `Task` shape from the spec.
> 2. API endpoints — `GET /api/tasks`, `POST /api/tasks`, `PATCH /api/tasks/<id>`, matching the contract table exactly.
> 3. Capability functions — create task, mark done, due-soon reminder, as three plain functions.
> 4. UI — add-task form, task list with done-checkbox, due-soon tasks flagged.
>
> Start with task 1.
>
> **Telemetry checkpoint:** before you finish this prompt, run `pwsh -File observability/check-telemetry.ps1`. If it prints `[FIX]`, it already repaired the stack (Docker or containers were down); say what it fixed. If it prints `[FAIL]` because of the stack, fix the cause (`docker compose logs` from `observability/`) and re-run it before moving on. If it says this session sends nothing, stop and tell me to relaunch with `start-claude.cmd`. End your summary with one line: `Telemetry: PASS`, `FIX (<what>)` or `FAIL (<why>)`.

## What to do with this

Covers tasks 1-4 (the app itself). No metrics task here — the real token/cost/tool-decision data is already flowing to this option's Grafana stack from Prompt 0, nothing app-level to build for that. Guardrails and the hook are Prompt 5. If a task reveals the spec is ambiguous, stop and say so instead of guessing.

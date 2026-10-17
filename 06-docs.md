# Prompt 6 of 8 — Documentation

**Project folder:** `D:/PERSONAL/AI_TIPS/career/linkedin-hub/posts/2026-10-single-vs-multi-agent/poc/option-a-single-agent`

Two documents, two different readers.

---

> Write two docs now that the app and its guardrail both work:
>
> **`README.md`** — for someone who found this repo and wants to run it:
> - What this is, in 2-3 sentences
> - Requirements (Python version, dependencies)
> - Setup: clone, install, run — exact commands, in order
> - How to use it: the three capabilities, briefly
> - Where the token/cost/tool-decision data for this build lives (the Grafana dashboard at `localhost:3000`, not an in-app panel)
> - Link to `DEVELOPER-GUIDE.md`
>
> **`DEVELOPER-GUIDE.md`** — for a developer extending or maintaining this:
> - Architecture: the single-process design, why the three capabilities are plain functions and not services
> - File-by-file map
> - The spec-driven workflow used to build this: business requirement → spec → task-by-task build with a checkpoint after each task → guardrail validation → hook
> - The guardrail system: what each check verifies, how to run `scripts/validate.py` directly, how to reinstall the `pre-push` hook on a fresh clone
> - How to add a fourth capability without breaking the other three
> - Known limitations
>
> **Telemetry checkpoint:** before you finish this prompt, run `pwsh -File observability/check-telemetry.ps1`. If it prints `[FIX]`, it already repaired the stack (Docker or containers were down); say what it fixed. If it prints `[FAIL]` because of the stack, fix the cause (`docker compose logs` from `observability/`) and re-run it before moving on. If it says this session sends nothing, stop and tell me to relaunch with `start-claude.cmd`. End your summary with one line: `Telemetry: PASS`, `FIX (<what>)` or `FAIL (<why>)`.

## What to do with this

Stop once both docs exist and read correctly. The code-review skill is Prompt 7, a separate task from the app build.

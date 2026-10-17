# Prompt 8 of 8 — Tests + Final Check

**Project folder:** `D:/PERSONAL/AI_TIPS/career/linkedin-hub/posts/2026-10-single-vs-multi-agent/poc/option-a-single-agent`

---

> Write test cases for this app — one for each capability (create task, mark done, due-soon reminder). Plain `pytest` against the Flask test client, no mocking. Each test checks one behavior: a task created via POST appears in GET; a PATCH to done=true flips it; a task due within 24h shows `reminder: true`.
>
> Run them, show the output.
>
> Re-run `scripts/validate.py` to confirm all five guardrails still pass with tests in place.
>
> Open this option's Grafana dashboard (`localhost:3000`) and show the real token/cost/tool-decision numbers for this build. Then run `rtk gain` and `headroom perf` (or `headroom dashboard`), and compare both against what Grafana shows — three different views of the same session's token usage.
>
> **Telemetry checkpoint:** before you finish this prompt, run `pwsh -File observability/check-telemetry.ps1`. If it prints `[FIX]`, it already repaired the stack (Docker or containers were down); say what it fixed. If it prints `[FAIL]` because of the stack, fix the cause (`docker compose logs` from `observability/`) and re-run it before moving on. If it says this session sends nothing, stop and tell me to relaunch with `start-claude.cmd`. End your summary with one line: `Telemetry: PASS`, `FIX (<what>)` or `FAIL (<why>)`.

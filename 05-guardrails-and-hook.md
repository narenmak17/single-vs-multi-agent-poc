# Prompt 5 of 8 — Guardrails + the pre-push Hook

**Project folder:** `D:/PERSONAL/AI_TIPS/career/linkedin-hub/posts/2026-10-single-vs-multi-agent/poc/option-a-single-agent`

---

> Implement `scripts/validate.py`, checking all five guardrails from `../SPEC.md`: API contract match, tests pass, no debug leftovers, the observability stack reachable (Grafana + collector respond on their configured ports), no secrets committed. Exit non-zero with a clear, numbered reason on failure. Runnable directly: `python scripts/validate.py`.
>
> Run it against what's built so far and fix anything it flags.
>
> Wire it into git: a tracked `hooks/pre-push` file that calls the validation script, plus `hooks/install.sh` that copies it into `.git/hooks/pre-push` and makes it executable. Run the install script.
>
> Prove it works: introduce one guardrail violation (e.g. a stray `print()`), attempt `git push`, confirm the hook blocks it with the violation named, then fix it and push clean.
>
> **Telemetry checkpoint:** before you finish this prompt, run `pwsh -File observability/check-telemetry.ps1`. If it prints `[FIX]`, it already repaired the stack (Docker or containers were down); say what it fixed. If it prints `[FAIL]` because of the stack, fix the cause (`docker compose logs` from `observability/`) and re-run it before moving on. If it says this session sends nothing, stop and tell me to relaunch with `start-claude.cmd`. End your summary with one line: `Telemetry: PASS`, `FIX (<what>)` or `FAIL (<why>)`.

## What to do with this

Stop once the hook has been proven to both block and pass. Docs are Prompt 6.

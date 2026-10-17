# Prompt 3 of 8 — Writing the Spec

**Project folder:** `D:/PERSONAL/AI_TIPS/career/linkedin-hub/posts/2026-10-single-vs-multi-agent/poc/option-a-single-agent`

Turn the business requirement into a written contract before implementing anything. This is requirements-and-design made literal: a durable document to build against, not a memory of a conversation.

---

> Take the business requirement and your response to it, and turn it into a formal spec: data model, API contract, UI shape, an observability requirement, and a set of guardrails — automated, checkable rules that must hold before this reaches GitHub.
>
> Write it as `SPEC.md`:
> - Capabilities (numbered, each with a one-line reason it's separable from the others)
> - Data model
> - API contract (method, path, body, response — as a table)
> - UI (what the single page needs to show)
> - Observability (what gets logged, what the metrics endpoint returns)
> - Guardrails (numbered, each checkable by a script — API shape, tests passing, no debug leftovers, metrics present, no secrets)
> - A validation script + git pre-push hook requirement
> - Out of scope
>
> Compare your draft against `../SPEC.md` — the ratified version of this spec for this comparison. Flag where it differs on substance, not just wording. Then adopt `../SPEC.md` as the spec of record for every prompt from here on.
>
> **Telemetry checkpoint:** before you finish this prompt, run `pwsh -File observability/check-telemetry.ps1`. If it prints `[FIX]`, it already repaired the stack (Docker or containers were down); say what it fixed. If it prints `[FAIL]` because of the stack, fix the cause (`docker compose logs` from `observability/`) and re-run it before moving on. If it says this session sends nothing, stop and tell me to relaunch with `start-claude.cmd`. End your summary with one line: `Telemetry: PASS`, `FIX (<what>)` or `FAIL (<why>)`.

## What to do with this

Stop once `../SPEC.md` is adopted as the spec of record. No capability code yet — that's Prompt 4.

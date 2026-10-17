# Prompt 7 of 8 — Build a Code-Review Skill

**Project folder:** `D:/PERSONAL/AI_TIPS/career/linkedin-hub/posts/2026-10-single-vs-multi-agent/poc/option-a-single-agent`

A separate capability from the app build: giving an agent a reusable, scoped skill. Build it from scratch, not copied from an existing one.

---

> Build a new Claude Code skill: a code-review skill scoped to this project — it checks a diff against `../SPEC.md`'s API contract and Guardrails section, not a generic linter wrapper.
>
> 1. Define its scope first: what it checks, what it deliberately doesn't (that's `scripts/validate.py`'s job).
> 2. Write its `SKILL.md` — name, description, the checks it performs, how it's invoked. Use `.claude/skills/rtk/SKILL.md` as a reference for frontmatter shape only, not content.
> 3. Invoke it once against this option's own code. Show what it catches, or confirms is clean.
>
> **Telemetry checkpoint:** before you finish this prompt, run `pwsh -File observability/check-telemetry.ps1`. If it prints `[FIX]`, it already repaired the stack (Docker or containers were down); say what it fixed. If it prints `[FAIL]` because of the stack, fix the cause (`docker compose logs` from `observability/`) and re-run it before moving on. If it says this session sends nothing, stop and tell me to relaunch with `start-claude.cmd`. End your summary with one line: `Telemetry: PASS`, `FIX (<what>)` or `FAIL (<why>)`.

## What to do with this

Stop once the skill has been invoked and its output shown. Tests are Prompt 8, the last step.

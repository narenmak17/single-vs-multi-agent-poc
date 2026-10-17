---
name: spec-review
description: Review a git diff of this task-tracker project against SPEC.md's API contract, data model, capabilities and Guardrails — the judgment calls scripts/validate.py cannot make (contract drift, weakened guardrails, architecture creep, reminder semantics). Use when the user says "spec review", "review this diff against the spec", "/spec-review", or before pushing a change that touches app/, scripts/ or hooks/. Not a generic linter.
metadata:
  context: code-review, spec, api-contract, guardrails, option-a
  auto-trigger: false
  scope: option-a-single-agent
---
# Spec Review

Reviews a diff against **SPEC.md** (this folder's verbatim copy of `../SPEC.md`, the spec of
record). It reads code the way a reviewer who knows the spec would. It does not run anything
`scripts/validate.py` already runs.

## Scope

**Checks (judgment, needs reading the diff in context):**

| ID | Spec section | What to look for |
|---|---|---|
| C1 | API contract | Endpoints added, removed or renamed vs the 3-row table. Request bodies that *require* a field the spec doesn't list, or ignore one it does (`title`, `due_at`, `done`). Response fields renamed, dropped, or added to `POST`/`PATCH`. Change in the meaning of a field (e.g. `due_at` format accepted). |
| C2 | Data model | `Task` fields vs `{ id, title, due_at, done, created_at }`. Schema changes without a migration path (`CREATE TABLE IF NOT EXISTS` never alters an existing DB). |
| C3 | Capability 3 semantics | `reminder` logic: 24h window, excludes `done`, null `due_at` never flags, overdue handling, date-only vs datetime, timezone. Off-by-one at the boundary. Any change here that has no matching test. |
| C4 | Architecture | Anything that breaks "one Flask process, three plain functions called directly": new services, HTTP calls between capabilities, queues, threads, subprocess workers, an orchestrator layer. Business logic leaking into route handlers. |
| C5 | Guardrails, weakened | Edits to `scripts/validate.py`, `hooks/pre-push` or `hooks/install.sh` that loosen a check: narrowed file sets, new skips or allow-lists, swallowed exceptions, exit code forced to 0, `--no-verify` anywhere, hook no longer blocking on failure. |
| C6 | Guardrails, intent | Things the guardrail *means* but the regex/AST misses: debug output via `logging` at DEBUG/`sys.stdout.write` in app code, `console.log`/`debugger` in templates, secrets in non-obvious shapes (URLs with tokens, base64 blobs, `.env` contents pasted into config), `start-claude.cmd` endpoint changed. |
| C7 | Out of scope creep | Auth, extra persistence, deployment config, framework-heavy UI: anything SPEC.md lists as out of scope. |

**Deliberately does not check** (that's `scripts/validate.py`, run it instead):

- Whether tests pass (guardrail 2).
- Literal `print(` / `pdb.set_trace(` / `breakpoint(` / `debug=True` in Python (guardrail 3, AST).
- Whether Grafana and the collector are up (guardrail 4).
- Regex secret patterns across all files (guardrail 5).
- Live API shape against a running app (guardrail 1). This skill reviews the *code* for
  contract drift; validate.py proves the *behaviour*.

Also out: style, formatting, naming, performance, generic lint. Do not report them.

## Invocation

```
/spec-review              # diff of working tree + index vs HEAD; if empty, HEAD~1..HEAD
/spec-review <base>       # diff <base>..working tree, e.g. /spec-review main, /spec-review cf895d3
```

## Procedure

1. Read `SPEC.md` in full. It is the source of truth. Don't review from memory of it.
2. Get the diff: `git diff <base> -- app scripts hooks start-claude.cmd requirements.txt`
   (plus `git diff --cached` when no base was given). List changed files with `git diff --stat`.
3. For each changed file, read the **whole file**, not just the hunk. Contract drift often lives
   in the unchanged half (a route still returning the old shape).
4. Run C1–C7. For each candidate finding, confirm it against the file and SPEC.md before
   reporting. If you can't point to a line and a spec sentence, drop it.
5. Do **not** edit code. Report only.

## Output

```
SPEC REVIEW  <base>..<target>   files: <n>

[C1] <BLOCK|WARN|NOTE> app/app.py:42
     Spec: "<quoted SPEC.md sentence>"
     Found: <what the code does>
     Fix: <one line>

...

Clean: C2 C4 C7          # checks run with no findings
Not checked here: tests, literal debug calls, stack, regex secrets -> python scripts/validate.py
VERDICT: CLEAN | <n> BLOCK, <n> WARN, <n> NOTE
```

Severity: **BLOCK** breaks the contract or weakens a guardrail; **WARN** is a spec ambiguity
the code resolved silently, or a risk with no test; **NOTE** is worth knowing, no action needed.

# Single Agent vs Multi-Agent — the same app, built twice

> 🎥 **Part 1 — Single agent:** https://youtu.be/oK5-Gl8bQv8
> 📖 **Write-up (analogy, decision matrix, checklist, sources):** https://cloudtoailearn.dev/posts/ai/skills-vs-agents-single-vs-multi-agent-architecture/
> 🔜 **Part 2 — Multi-agent:** coming soon. `option-b-multi-agent/` lands here with it.

| Folder | Status |
|---|---|
| [`option-a-single-agent/`](option-a-single-agent/) | ✅ Available (Part 1) |
| `option-b-multi-agent/` | 🔜 Part 2 |

---

The same task tracker, built twice from the same spec. Option A uses one agent with several skills; Option B uses several agents behind an orchestrator. Same spec, same API, same UI. Architecture is the only variable.

Each option was built from an empty folder by running a numbered sequence of prompts, in order. The prompts are included, so you can reproduce either build yourself.

**This POC is not primarily about token counts.** The token/cost comparison is a side data point. The main point is a repeatable, *spec-driven* development workflow:

- a business requirement turned into a written spec with explicit guardrails
- a build broken into one task at a time, with a validation checkpoint after each
- an automated guardrail check wired into a git `pre-push` hook, so nothing broken reaches GitHub
- production-grade docs
- a reusable code-review skill, built from scratch

## Folder structure

```
.
├── SPEC.md                           ← shared spec + guardrails, adopted in prompt 3 of each build
├── README.md                         ← this file
├── option-a-single-agent/
│   ├── 00-preflight.md               ← preflight: stack up, launch, telemetry check
│   ├── 01-project-setup.md           ← the 8-prompt build sequence, run in order
│   ├── 02-business-requirement.md
│   ├── 03-spec-driven.md
│   ├── 04-build-tasks.md
│   ├── 05-guardrails-and-hook.md
│   ├── 06-docs.md
│   ├── 07-code-review-skill.md
│   ├── 08-tests.md
│   ├── app/ · tests/ · scripts/ · hooks/   ← what the build produced
│   ├── README.md · DEVELOPER-GUIDE.md      ← generated in prompt 6
│   ├── observability/                ← Grafana/OTel stack, ports 3000/4317/4318/8888
│   └── .claude/skills/
│       ├── rtk/                      ← token-optimization skill
│       └── spec-review/              ← code-review skill built in prompt 7
└── option-b-multi-agent/             ← Part 2: same sequence, adapted for the orchestrator build
```

## The build sequence

Each option runs its numbered prompts in order, 0 through 8.

**Prompt 0 — preflight** (`00-preflight.md`): from a terminal in the option's folder, start the observability stack, then start Claude Code with `.\start-claude.cmd headroom` rather than plain `claude`. The launcher sets the telemetry environment for that option's own collector (A → `:4317` / Grafana `:3000`, B → `:4327` / Grafana `:3001`) and gives each option its own headroom proxy port (A `8787`, B `8797`), so both can run side by side. Claude Code ignores telemetry keys in a project's `.claude/settings*.json`, so a session started any other way exports nothing. The preflight then runs `observability/check-telemetry.ps1` to confirm telemetry is flowing.

1. **Project setup** — a clean skeleton, then confirm the option's Grafana/OTel stack is up and the session's telemetry is reaching it.
2. **Business requirement** — a plain-language stakeholder ask, no spec yet.
3. **Spec-driven design** — the business ask becomes `SPEC.md`, guardrails included. This is the requirements-and-design step, not a formality.
4. **Build, one task at a time.** After each task, Claude stops and summarizes what was built, which spec section it was checked against, and what's left, then waits for a go-ahead before the next task. Drift gets caught at task N, not after the whole app is built.
5. **Guardrails + the pre-push hook.** `scripts/validate.py` runs the checks; the hook blocks a deliberately broken push, then lets it through once fixed. Option A's git history includes that blocked commit.
6. **Docs.** A real `README.md` and `DEVELOPER-GUIDE.md`.
7. **Code-review skill, from scratch.** Scope it, write its `SKILL.md`, run it once against the option's own code.
8. **Tests**, then the token-usage comparison: the option's Grafana dashboard, `rtk gain`, and `headroom perf`. These are three views of the same build session's real token usage, not a simulated number.

## Observability

Each option has its own Grafana/OTel stack under `observability/`. Bring it up with `docker compose up -d` from that folder. Prompt 1 also documents the from-scratch setup steps.

| | Option A | Option B |
|---|---|---|
| Grafana | `localhost:3000` | `localhost:3001` |
| OTel Collector (gRPC) | `4317` | `4327` |
| OTel Collector (HTTP) | `4318` | `4328` |

## Ports

Both apps can run at once for a side-by-side comparison: Option A on `:5001`, Option B on `:5002`. Their Grafana/OTel stacks can run at the same time too, on the ports above.

## What this POC is not

Not a benchmark, and not primarily a token-cost demo. The point is to make the *shape* of the cost difference visible (one process vs. orchestrator round-trips) using real build-time telemetry, and, more importantly, to show a repeatable spec-driven workflow with real guardrails. It doesn't try to produce one citable token number. The research numbers and sources are in the [blog post](https://cloudtoailearn.dev/posts/ai/skills-vs-agents-single-vs-multi-agent-architecture/#references).

# Single Agent vs Multi-Agent — the same app, built twice

> 🎥 **Part 1 — Single agent:** https://youtu.be/oK5-Gl8bQv8
> 📖 **Write-up (analogy, decision matrix, checklist, sources):** https://cloudtoailearn.dev/posts/ai/skills-vs-agents-single-vs-multi-agent-architecture/
> 🔜 **Part 2 — Multi-agent:** coming soon. `option-b-multi-agent/` lands here with it.

| Folder | Status |
|---|---|
| [`option-a-single-agent/`](option-a-single-agent/) | ✅ Built on camera in Part 1 |
| `option-b-multi-agent/` | 🔜 Part 2 |

---

# POC — Skills vs. Agents Task Tracker

Built live, on camera, two separate recordings — one per folder. Same spec, same app, different architecture. Nothing in `option-a-*` or `option-b-*` is pre-built; both start empty and get built during the recording by reading each numbered prompt aloud and pasting it in.

**This POC is not primarily about token counts.** The token/cost comparison is a side data point, shown at the end via each option's Grafana dashboard plus `rtk gain` and `headroom perf`. The actual teaching point is a systematic, *spec-driven* development methodology: a business requirement turned into a written spec with explicit guardrails, a build broken into one task at a time with a validation checkpoint after each, an automated guardrail check wired into a git `pre-push` hook so nothing broken reaches GitHub, production-grade docs, and — as a second, separate lesson — building a reusable code-review skill from scratch on camera.

## Folder structure

```
poc/
├── SPEC.md                           ← shared spec + guardrails, adopted during Prompt 3 of each build
├── README.md                         ← this file
├── option-a-single-agent/
│   ├── 00-preflight.md               ← on-camera preflight: stack up, launch, telemetry proof
│   ├── 01-project-setup.md           ← then the 8-prompt recording sequence, read on camera in order
│   ├── 02-business-requirement.md
│   ├── 03-spec-driven.md
│   ├── 04-build-tasks.md
│   ├── 05-guardrails-and-hook.md
│   ├── 06-docs.md
│   ├── 07-code-review-skill.md
│   ├── 08-tests.md
│   ├── observability/                ← Grafana/OTel stack, ports 3000/4317/4318/8888
│   └── .claude/skills/rtk/            ← token-optimization skill, copied in for this build
│       └── SKILL.md
└── option-b-multi-agent/
    ├── 00-preflight.md               ← same preflight, B's ports
    ├── 01-project-setup.md           ← same 8-prompt sequence, adapted for the orchestrator build
    ├── ...
    ├── 08-tests.md
    ├── observability/                ← same stack, remapped to ports 3001/4327/4328/8889
    └── .claude/skills/rtk/
        └── SKILL.md
```

After each recording, the folder will additionally contain whatever Claude built: `app.py`, templates, `test_app.py`, `scripts/validate.py`, `hooks/pre-push`, `hooks/install.sh`, `README.md`, `DEVELOPER-GUIDE.md`, and a new code-review skill under `.claude/skills/` — not pre-created, so the build is genuinely visible start to finish.

## Recording flow (both videos)

Each option runs through its own numbered prompt, in order, 0 through 8.

**Prompt 0 — preflight** (`00-preflight.md`): in a VS Code terminal in the option's folder, start the stack, then start the session with `.\start-claude.cmd headroom`, not with `claude` or the IDE's Claude panel. The launcher sets the telemetry env for that option's own collector (A → `:4317`/Grafana `:3000`, B → `:4327`/Grafana `:3001`) and gives each option its own headroom proxy port (A `8787`, B `8797`), so both recordings can run side by side. Claude Code ignores telemetry keys in a project's `.claude/settings*.json`, so a session started any other way exports nothing. Part 2 of the preflight runs `observability/check-telemetry.ps1` inside the new session to prove it. A and B can run in two VS Code terminals side by side.

1. **Project setup** — a clean skeleton, then confirm this option's Grafana/OTel stack is up and this session's own telemetry is reaching it.
2. **Business requirement** — a plain-language stakeholder ask, no spec. Read it aloud, paste it in.
3. **Spec-driven design** — the business ask becomes `SPEC.md`, including guardrails. Narrate this as the requirements-and-design step, not a formality.
4. **Build, one task at a time.** After each task, Claude stops and summarizes (what was built, which spec section it checked against, what's left) — give an explicit go-ahead before the next task starts. This is the validation checkpoint moment: drift gets caught at task N, not after the whole app is built.
5. **Guardrails + the pre-push hook.** Show `scripts/validate.py` running, then show the hook actually installed and actually blocking a deliberately-broken push, then passing once fixed. Don't skip proving the block.
6. **Docs.** Show the generated `README.md` and `DEVELOPER-GUIDE.md`.
7. **Build the code-review skill live, from scratch.** A separate teaching beat from the app build — scope it, write its `SKILL.md`, run it once against this option's own code.
8. **Tests**, then the token-usage comparison: this option's Grafana dashboard, `rtk gain`, and `headroom perf` — three different views of the same build session's actual token usage, not a simulated number.

Close on "spec in, guardrail validated, docs generated, reusable skill built, real telemetry end to end" — the token numbers are the side note, not the headline.

## Observability

Each option has its own Grafana/OTel stack under `observability/`, copied from `D:\PERSONAL\AI_TIPS\teaching\hands_demo\03\demos\after\docker`. Both are already running before recording starts, so Prompt 0 and Prompt 1 just confirm this instead of spending camera time on `docker compose up -d` — Prompt 1 in each option also documents the from-scratch steps for anyone following along without a pre-built stack.

| | Option A | Option B |
|---|---|---|
| Grafana | `localhost:3000` | `localhost:3001` |
| OTel Collector (gRPC) | `4317` | `4327` |
| OTel Collector (HTTP) | `4318` | `4328` |

## Ports

Run both apps at once for the side-by-side comparison shot: Option A on `:5001`, Option B on `:5002`. Their Grafana/OTel stacks run simultaneously too, on the ports above.

## What this POC is not

Not a benchmark, and not primarily a token-cost demo. The point is to make the *shape* of the cost difference visible (one process vs. orchestrator round-trips) using real build-time telemetry, and, more importantly, to show a repeatable spec-driven workflow with real guardrails — not to produce a single citable token number. The actual research numbers live in `../design-plan.html`.

# Prompt 2 of 8 — Business Requirement

**Project folder:** `D:/PERSONAL/AI_TIPS/career/linkedin-hub/posts/2026-10-single-vs-multi-agent/poc/option-a-single-agent`

Paste this in as-is. No spec yet.

---

> We keep losing track of small to-dos across the team. Nothing fancy — somewhere to jot a task down, give it a due date if it matters, and tick it off when it's done. The real problem is tasks quietly slipping past their date and nobody noticing until it's too late, so anything coming up soon and not done needs to be obvious immediately, not something I have to go hunting for.
>
> No logins or teams for now — just get the core loop right. I also want to see roughly what this costs to run, so build in whatever tracking makes sense for that.
>
> Tell me back what you're planning to build before writing any code.

## Skills to use

- **fable-mode** — scope the requirement properly before responding: what's explicit, what's implied, what's ambiguous.
- **caveman** — keep responses compressed and direct throughout this build.
- **headroom** — already wrapping this session: it was launched with `.\start-claude.cmd headroom` in Prompt 0, which also set the telemetry env for this option's Grafana (`:3000`), so token usage has been tracked in both since then. Note that `rtk` is also installed in this project for the same purpose — both get compared at the end, not stacked silently.

## What to do with this

Don't start coding. Restate the requirement in your own words, name the entities involved, flag anything genuinely ambiguous, and propose what you'd build — in plain language, not code. This becomes the input to the next prompt, where it turns into a spec.

Don't reference `../SPEC.md` yet — treat it as if it doesn't exist.

# Prompt 1 of 8 — Project Setup

**Project folder:** `D:/PERSONAL/AI_TIPS/career/linkedin-hub/posts/2026-10-single-vs-multi-agent/poc/option-a-single-agent`

**Reference:** http://127.0.0.1:7600/posts/2026-10-single-vs-multi-agent/poc/

Scaffold before any feature code — and before the business requirement, so the shell and the telemetry proof come first. If the skeleton commit already exists, verify it against this list instead of recreating it.

---

> Set up a fresh project skeleton — no feature code yet, just the shell:
>
> - Initialize git.
> - Folder structure: app code, tests, placeholder `scripts/` and `hooks/` directories.
> - Dependency setup: virtual env instructions, `requirements.txt` with just Flask for now.
> - An empty `app.py` that runs on **port 5001** — enough to prove the skeleton works.
> - First commit: the empty skeleton, nothing else.
>
> Architecture decision to lock in now, before any capability code exists: **one Flask process, one agent** — the three upcoming capabilities as plain functions it calls directly, no inter-process messaging, no orchestrator. Note it in the commit message.
>
> Run the skeleton, confirm it responds on :5001, then stop.
>
> Then check this option's observability stack: `observability/` already has a Grafana/OTel setup copied from `D:\PERSONAL\AI_TIPS\teaching\hands_demo\03\demos\after\docker`, on Grafana `3000` and collector `4317`/`4318`/`8888`. Check if it's already running (`docker compose ps` from that folder) — if it is, skip setup and just confirm Grafana loads at `localhost:3000`. If `docker` can't reach the daemon, start Docker Desktop first (`Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"`) and poll `docker info` until it succeeds. If the stack isn't running, start it with `docker compose up -d` from `observability/`, then confirm all five containers are `Up` and `localhost:3000/api/health` returns ok.
>
> Then prove **this session** is exporting its telemetry to this option's stack. Telemetry has to be switched on with real environment variables **before** Claude starts. Claude Code ignores these keys in a project's `.claude/settings*.json`, and nothing set during a running session takes effect. This folder's `start-claude.cmd` sets them. These are the exact values for Option A:
>
> ```
> CLAUDE_CODE_ENABLE_TELEMETRY=1
> CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1
> OTEL_METRICS_EXPORTER=otlp
> OTEL_LOGS_EXPORTER=otlp
> OTEL_TRACES_EXPORTER=otlp
> OTEL_EXPORTER_OTLP_PROTOCOL=grpc
> OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
> OTEL_METRIC_EXPORT_INTERVAL=10000
> OTEL_LOGS_EXPORT_INTERVAL=5000
> HEADROOM_PORT=8787
> ```
>
> The endpoint is `http://localhost:4317`.
>
> 1. Check that `start-claude.cmd` exists in this folder and sets exactly those values. If it's missing or any value differs, (re)create it: it should `cd` to its own folder, `set` each variable above, then run `headroom wrap claude` when its first argument is `headroom` and `claude %*` otherwise.
> 2. Don't check the variables by reading `OTEL_*` from your shell, because Claude Code removes them from tool subprocesses. Grafana is the only real proof. Read this session's ID from `CLAUDE_CODE_SESSION_ID` (`$env:CLAUDE_CODE_SESSION_ID` in PowerShell).
> 3. Query this option's Grafana (`localhost:3000`, via its datasource proxy API) for that session. Look for:
>    - log events in Loki (`{service_name="claude-code"} | session_id="<id>"`)
>    - `claude_code_token_usage` / `claude_code_cost_usage` in Mimir
>    - spans in Tempo (TraceQL `{ .session.id = "<id>" }`: the session ID is a span attribute, not a resource attribute)
>
>    Metrics export every 10s, so if Mimir is empty, wait 15s and retry once. A turn's `claude_code.interaction` span is only exported once that turn ends. So expect Prompt 0's interaction trace to be there, and this turn's to show up as "root span not yet received", which is normal. Report what each one returned. If a signal is missing, say which one. Don't paper over it.
> 4. If nothing at all arrived for this session, stop: it wasn't started with `start-claude.cmd`. Tell me to `/exit`, then run `.\start-claude.cmd headroom` in this folder's terminal and paste Prompt 0 again. Don't work around it with a child run.
> 5. If it arrived, point me at `http://localhost:3000/d/claude-code-overview`. Sessions, Total Tokens, Total Cost and the Recent Claude Code Traces panel should already include this session.
>
> (No stack pre-copied in? Copy it from `D:\PERSONAL\AI_TIPS\teaching\hands_demo\03\demos\after\docker` into `observability/`, ports as-is — Option B uses remapped ports instead.)

## What to do with this

Stop once the skeleton runs, the observability stack is confirmed running, and this session's own logs, metrics and traces show up in the `:3000` Grafana. Because the session was started with `start-claude.cmd`, it has been captured since Prompt 0, so there's nothing to relaunch. The business requirement is next (Prompt 2), then the spec.

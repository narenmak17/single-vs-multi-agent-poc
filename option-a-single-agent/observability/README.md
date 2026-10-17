# Claude Code Observability Stack

A local Grafana LGTM stack for collecting Claude Code **metrics, logs and traces**
over OpenTelemetry.

```
Claude Code ──OTLP──▶ OTEL Collector ──┬─▶ Mimir  (metrics)
                                        ├─▶ Tempo  (traces)
                                        └─▶ Loki   (logs)
                                                ▲
                                    Grafana ────┘
```

## Start it

```bash
cd observability
docker compose up -d
```

Then open Grafana at **http://localhost:3000** (anonymous admin access, no login needed).
The Mimir, Tempo and Loki datasources are pre-provisioned and ready to query.

## Point Claude Code at it

Export these before launching `claude` (gRPC, the default protocol):

```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1   # required for traces to reach Tempo
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_TRACES_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

> Telemetry is configured once at startup. Setting these inside an already
> running session has no effect, so restart `claude` or use a headless run (below).

### Headless run (no restart needed)

Set the variables inline for a single `claude -p` call. Only that child process
gets them, and the short export intervals make it flush before it exits:

```bash
CLAUDE_CODE_ENABLE_TELEMETRY=1 CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1 \
OTEL_METRICS_EXPORTER=otlp OTEL_LOGS_EXPORTER=otlp OTEL_TRACES_EXPORTER=otlp \
OTEL_EXPORTER_OTLP_PROTOCOL=grpc OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
OTEL_METRIC_EXPORT_INTERVAL=5000 OTEL_LOGS_EXPORT_INTERVAL=2000 \
claude -p "Read app/app.py and summarise it in one sentence." --output-format json --allowedTools Read
```

PowerShell equivalent (the variables last only for the current shell):

```powershell
$env:CLAUDE_CODE_ENABLE_TELEMETRY='1'; $env:CLAUDE_CODE_ENHANCED_TELEMETRY_BETA='1'
$env:OTEL_METRICS_EXPORTER='otlp'; $env:OTEL_LOGS_EXPORTER='otlp'; $env:OTEL_TRACES_EXPORTER='otlp'
$env:OTEL_EXPORTER_OTLP_PROTOCOL='grpc'; $env:OTEL_EXPORTER_OTLP_ENDPOINT='http://localhost:4317'
$env:OTEL_METRIC_EXPORT_INTERVAL='5000'; $env:OTEL_LOGS_EXPORT_INTERVAL='2000'
claude -p "Read app/app.py and summarise it in one sentence." --output-format json --allowedTools Read
```

The JSON output includes `session_id`. Use it to filter in Grafana (see
[Verify it's working](#verify-its-working)).

### Make it permanent for this project

Start Claude with `start-claude.cmd` in the project folder (`start-claude.cmd headroom` to wrap it with
headroom). It sets the variables above before `claude` starts, from whichever folder you run it in.

> Don't put these keys in `.claude/settings.local.json`. Claude Code ignores `CLAUDE_CODE_ENABLE_TELEMETRY`
> and `OTEL_*` in project-scoped settings (it logs a warning and exports nothing). They only work as real
> environment variables, or in `~/.claude/settings.json`, which would apply to every project on the machine.

Prefer HTTP? Use the other port instead:

```bash
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

To make telemetry export faster while testing, you can also shorten the intervals:

```bash
export OTEL_METRIC_EXPORT_INTERVAL=10000   # 10s
export OTEL_LOGS_EXPORT_INTERVAL=5000      # 5s
```

## Ports

| Service         | URL / port              | Purpose                          |
| --------------- | ----------------------- | -------------------------------- |
| Grafana         | http://localhost:3000   | UI / dashboards                  |
| OTEL Collector  | localhost:4317 (gRPC)   | **Point Claude Code here**       |
| OTEL Collector  | localhost:4318 (HTTP)   | OTLP HTTP alternative            |
| OTEL Collector  | localhost:8888          | Collector's own metrics          |

Mimir, Tempo and Loki are only reachable on the internal `observability` network —
all signals flow through the collector.

## Dashboards

A starter **Claude Code — Overview** dashboard is auto-provisioned into Grafana
(left nav → **Dashboards** → **Claude Code** folder). It shows sessions, token
usage, cost, lines changed, commits, PRs, tool-decision accept/reject, total
active time, and tails recent logs from Loki. Use the **Model** dropdown at the
top to filter the token/cost panels by model.

> The collector sets `add_metric_suffixes: false`, so metric names map 1:1 from
> Claude Code's OTel names (dots → underscores). Key series:
> `claude_code_session_count`, `claude_code_token_usage` (label `type`),
> `claude_code_cost_usage` (label `model`), `claude_code_lines_of_code_count`,
> `claude_code_commit_count`, `claude_code_pull_request_count`,
> `claude_code_code_edit_tool_decision` (label `decision`),
> `claude_code_active_time_total`.

Panels show "No data" until a real Claude Code session sends telemetry — that's
expected on a fresh stack.

## Verify it's working

In Grafana → **Explore**:
- **Mimir**: query `claude_code_token_usage` or run `{__name__=~"claude_code.*"}`.
- **Loki**: query `{service_name="claude-code"}`. For one session, add
  `| session_id="<id>"`. Event fields are structured metadata, not stream labels.
- **Tempo**: search recent traces. Look for root spans `claude_code.interaction`
  and `claude_code.llm_request`.

## Tear down

```bash
docker compose down          # keep data
docker compose down -v       # also wipe stored metrics/logs/traces
```

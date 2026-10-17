@echo off
:: Start Claude Code with telemetry wired to Option A's own collector (Grafana :3000).
:: Claude Code ignores CLAUDE_CODE_ENABLE_TELEMETRY / OTEL_* in project .claude/settings*.json,
:: so they have to be real environment variables, set before claude starts.
:: Usage: start-claude.cmd [claude args]   or   start-claude.cmd headroom   (wraps it with headroom)
:: "headroom" mode is the full preflight: stack up, clean-slate warning, then Claude opens and
:: runs the telemetry check as its first message. Wait for READY FOR RECORDING.
cd /d "%~dp0"
set CLAUDE_CODE_ENABLE_TELEMETRY=1
set CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1
set OTEL_METRICS_EXPORTER=otlp
set OTEL_LOGS_EXPORTER=otlp
set OTEL_TRACES_EXPORTER=otlp
set OTEL_EXPORTER_OTLP_PROTOCOL=grpc
set OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
set OTEL_METRIC_EXPORT_INTERVAL=10000
set OTEL_LOGS_EXPORT_INTERVAL=5000
:: Own headroom proxy port per option, so A and B can run side by side with separate stats.
set HEADROOM_PORT=8787
if /i not "%~1"=="headroom" (
  echo Option A telemetry -^> %OTEL_EXPORTER_OTLP_ENDPOINT%  ^(Grafana http://localhost:3000^)
  claude %*
  exit /b
)

:: Stack must be up before Claude starts, or the first turn's telemetry is lost.
pwsh -NoProfile -File observability\check-telemetry.ps1 -StackOnly
if errorlevel 1 (
  echo Option A stack is not ready - fix the FAIL above, then re-run start-claude.cmd headroom
  exit /b 1
)
set DIRTY=
for /f %%i in ('git status --porcelain -- app') do set DIRTY=1
if defined DIRTY (
  echo [WARN] Leftover changes in app\ - not a clean slate. Before recording run:
  echo        git stash push -u -m "pre-recording leftovers" -- app
)

set "PREFLIGHT=Preflight only, do not touch any code. Run pwsh -File observability/check-telemetry.ps1 and show its output verbatim, then this session's ID from $env:CLAUDE_CODE_SESSION_ID. If it ends in PASS, reply READY FOR RECORDING and tell me to refresh http://localhost:3000/d/claude-code-overview. If it FAILs, reply NOT READY, name the missing signal and stop: no workarounds, no child runs, no env vars set mid-session."
echo Option A telemetry -^> %OTEL_EXPORTER_OTLP_ENDPOINT%  (Grafana http://localhost:3000)
headroom wrap claude "%PREFLIGHT%"

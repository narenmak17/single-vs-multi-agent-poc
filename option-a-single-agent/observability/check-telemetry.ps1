# Telemetry checkpoint for Option A: is this Claude Code session's telemetry reaching Grafana :3000?
# Repairs what can be repaired in-session (Docker daemon down, stack containers stopped);
# reports what can't (session not started via start-claude.cmd -> must relaunch).
# Usage (from a Claude Code tool shell): pwsh -File observability/check-telemetry.ps1
#        or for another session:         pwsh -File observability/check-telemetry.ps1 -SessionId <id>
#        or before Claude starts:        pwsh -File observability/check-telemetry.ps1 -StackOnly   (steps 1-3 only)
param([string]$SessionId = $env:CLAUDE_CODE_SESSION_ID, [switch]$StackOnly)

$Option = 'A'; $Grafana = 'http://localhost:3000'; $Containers = 5
$ComposeDir = $PSScriptRoot
$fail = $false
function Say($status, $msg) { Write-Output ("[{0}] {1}" -f $status, $msg) }

# Real Docker CLI. Resolved explicitly: an npm package also named "docker" (a doc generator) can
# shadow it on PATH, and Docker Desktop may live per-user or under Program Files.
$docker = (Get-Command docker.exe -CommandType Application -All -ErrorAction SilentlyContinue | Where-Object Source -like '*Docker*' | Select-Object -First 1).Source
if (-not $docker) { $docker = @("$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe", 'C:\Program Files\Docker\Docker\resources\bin\docker.exe') | Where-Object { Test-Path $_ } | Select-Object -First 1 }
if (-not $docker) { Say 'FAIL' 'Docker CLI (docker.exe) not found - is Docker Desktop installed?'; exit 1 }
$env:PATH = (Split-Path $docker) + ';' + $env:PATH   # compose needs docker-credential-desktop from the same folder
$dockerDesktop = @("$env:LOCALAPPDATA\Programs\DockerDesktop\Docker Desktop.exe", 'C:\Program Files\Docker\Docker\Docker Desktop.exe') | Where-Object { Test-Path $_ } | Select-Object -First 1
# 1. Docker daemon (probed in a job with a timeout: a wedged daemon makes `docker info` hang forever)
function Test-Docker {
    $j = Start-Job { & $using:docker info *> $null; $LASTEXITCODE }
    $r = if (Wait-Job $j -Timeout 20) { Receive-Job $j } else { 'hung' }
    Remove-Job $j -Force; $r
}
$d = Test-Docker
if ($d -eq 'hung') { Say 'FAIL' 'Docker daemon not responding (docker info hung 20s) - quit Docker Desktop from the tray, start it again, then re-run'; exit 1 }
if ($d -ne 0) {
    Say 'FIX' 'Docker daemon not reachable - starting Docker Desktop'
    Start-Process $dockerDesktop
    for ($i = 0; $i -lt 40; $i++) { Start-Sleep 3; $d = Test-Docker; if ($d -eq 0) { break } }
    if ($d -ne 0) { Say 'FAIL' 'Docker daemon still down after 120s'; exit 1 }
}
Say 'OK' 'Docker daemon up'

# 2. Stack containers
$running = @(& $docker compose --project-directory $ComposeDir ps --status running -q).Count
if ($running -lt $Containers) {
    Say 'FIX' "$running/$Containers stack containers running - docker compose up -d"
    & $docker compose --project-directory $ComposeDir up -d *> $null
    Start-Sleep 10
    $running = @(& $docker compose --project-directory $ComposeDir ps --status running -q).Count
    if ($running -lt $Containers) { Say 'FAIL' "only $running/$Containers containers running after restart - check 'docker compose logs'"; exit 1 }
    $restarted = $true
}
Say 'OK' "$running/$Containers stack containers running"

# 3. Grafana
$healthy = $false
for ($i = 0; $i -lt 20 -and -not $healthy; $i++) {
    try { $healthy = (Invoke-RestMethod "$Grafana/api/health" -TimeoutSec 3).database -eq 'ok' } catch { Start-Sleep 3 }
}
if (-not $healthy) { Say 'FAIL' "Grafana $Grafana not healthy"; exit 1 }
Say 'OK' "Grafana $Grafana healthy"
if ($StackOnly) { exit 0 }

# 4. This session's signals
if (-not $SessionId) { Say 'FAIL' 'No session id (CLAUDE_CODE_SESSION_ID unset) - run this from inside the Claude Code session, or pass -SessionId'; exit 1 }
function Query-Signals {
    $now = [DateTimeOffset]::UtcNow
    $ns = { param($t) $t.ToUnixTimeMilliseconds() * 1000000 }
    $q = [uri]::EscapeDataString("{service_name=`"claude-code`"} | session_id=`"$SessionId`"")
    $logs = (Invoke-RestMethod "$Grafana/api/datasources/proxy/uid/loki/loki/api/v1/query_range?query=$q&start=$(& $ns $now.AddMinutes(-10))&end=$(& $ns $now)&limit=1000").data.result |
        ForEach-Object { $_.values.Count } | Measure-Object -Sum | Select-Object -ExpandProperty Sum
    $q = [uri]::EscapeDataString("sum(max_over_time(claude_code_token_usage{session_id=`"$SessionId`"}[6h]))")
    $tok = (Invoke-RestMethod "$Grafana/api/datasources/proxy/uid/mimir/api/v1/query?query=$q").data.result
    $q = [uri]::EscapeDataString("sum(max_over_time(claude_code_cost_usage{session_id=`"$SessionId`"}[6h]))")
    $cost = (Invoke-RestMethod "$Grafana/api/datasources/proxy/uid/mimir/api/v1/query?query=$q").data.result
    $q = [uri]::EscapeDataString("{ .session.id = `"$SessionId`" }")
    $spans = (Invoke-RestMethod "$Grafana/api/datasources/proxy/uid/tempo/api/search?q=$q&start=$($now.AddHours(-6).ToUnixTimeSeconds())&end=$($now.ToUnixTimeSeconds())&limit=100").traces.Count
    [pscustomobject]@{ Logs = [int]$logs; Tokens = $(if ($tok) { [double]$tok[0].value[1] } else { 0 }); Cost = $(if ($cost) { [double]$cost[0].value[1] } else { 0 }); Traces = $spans }
}
$s = Query-Signals
if ($s.Logs -eq 0 -or $s.Tokens -eq 0) { Start-Sleep 15; $s = Query-Signals }

if ($s.Logs -gt 0) { Say 'OK' "Loki: $($s.Logs) log events for this session in the last 10 min" }
else { Say 'FAIL' 'Loki: no log events for this session in the last 10 min'; $fail = $true }
if ($s.Tokens -gt 0) { Say 'OK' ("Mimir: {0:N0} tokens, `${1:N4} cost for this session" -f $s.Tokens, $s.Cost) }
else { Say 'FAIL' 'Mimir: no token metrics for this session'; $fail = $true }
if ($s.Traces -gt 0) { Say 'OK' "Tempo: $($s.Traces) traces for this session" }
else { Say 'WARN' "Tempo: no traces yet (a turn's root span is only exported when the turn ends)" }

if ($fail) {
    if ($restarted) {
        Say 'FAIL' 'Stack was just restarted; anything sent while it was down is lost. Re-run this check after the next prompt - new data should arrive.'
    } elseif ($s.Logs -eq 0 -and $s.Tokens -eq 0) {
        Say 'FAIL' "Stack is healthy but this session sends nothing: it was not started with start-claude.cmd. /exit, run '.\start-claude.cmd headroom' in this option's folder, then paste the current prompt again."
    }
    exit 1
}
Say 'PASS' "Option $Option telemetry is reaching Grafana $Grafana/d/claude-code-overview"
exit 0

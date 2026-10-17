# Prompt 0 of 8 — Preflight (before recording)

**Project folder:** `D:/PERSONAL/AI_TIPS/career/linkedin-hub/posts/2026-10-single-vs-multi-agent/poc/option-a-single-agent`

Do this before you hit record, with Option B's preflight running beside it. One command per option: it brings the stack up, flags leftover code, launches Claude with telemetry, and Claude runs the telemetry check as its first message. Nothing to paste.

| Option A | Value |
|---|---|
| Grafana | http://localhost:3000/d/claude-code-overview |
| OTel collector | `4317` gRPC · `4318` HTTP · `8888` internal |
| headroom proxy | `8787` |
| Containers | `grafana` `loki` `mimir` `tempo` `otel-collector` |

> **Never use the VS Code Claude side panel for this build.** It starts Claude without the `OTEL_*` variables, so the check fails with "this session sends nothing", and it can't give A and B their different ports. Claude must be started from a terminal with `start-claude.cmd`.

---

## Setup: A and B side by side, one VS Code window

1. Close the Claude side panel if it's open.
2. **Terminal → New Terminal** (PowerShell), rename it `A`. Split it (**Ctrl+Shift+5**) and rename the second one `B`.
3. In terminal **A**:
   ```powershell
   cd D:\PERSONAL\AI_TIPS\career\linkedin-hub\posts\2026-10-single-vs-multi-agent\poc\option-a-single-agent
   .\start-claude.cmd headroom
   ```
4. In terminal **B**, the same with Option B's folder (see Option B's `00-preflight.md`).

What `start-claude.cmd headroom` does, in order:

| Step | You see | If it goes wrong |
|---|---|---|
| Docker + stack + Grafana | `[OK] Docker daemon up` · `[OK] 5/5 stack containers running` · `[OK] Grafana ... healthy` | Starts Docker Desktop / `docker compose up -d` itself. A hung daemon fails in 20s: quit Docker Desktop from the tray, start it again, re-run. Claude does not open until this passes. |
| Clean slate | nothing | `[WARN] Leftover changes in app\` → run the `git stash` line it prints, then `/exit` and re-run. |
| Launch | `Option A telemetry -> http://localhost:4317  (Grafana http://localhost:3000)` | Line missing → you're not in this launcher. |
| First message (automatic) | Claude runs `check-telemetry.ps1`, shows output + session ID | See below. |

## Ready check

Wait for Claude to reply **READY FOR RECORDING**. Then refresh http://localhost:3000/d/claude-code-overview: Sessions / Total Tokens / Total Cost show this session. `WARN` on Tempo is fine (the turn's root span exports when the turn ends).

- **NOT READY** with "this session sends nothing" → `/exit`, re-run `.\start-claude.cmd headroom` in terminal A.
- **NOT READY** with any other signal → it names the missing one (Loki logs / Mimir tokens). Fix that before recording.

When **both** A and B say READY FOR RECORDING, start recording and paste Prompt 1 into **this same session**. Every token from here on is counted.

## Re-check by hand (optional)

To re-run the check mid-session, paste:

> Preflight only, do not touch any code. Run `pwsh -File observability/check-telemetry.ps1`, show its output verbatim and this session's ID (`$env:CLAUDE_CODE_SESSION_ID`). PASS → READY FOR RECORDING. FAIL → NOT READY, name the missing signal, and stop: no workarounds, no child runs, no env vars set mid-session.

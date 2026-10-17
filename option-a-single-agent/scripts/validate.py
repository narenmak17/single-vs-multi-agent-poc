"""Check the five guardrails from SPEC.md. Exits non-zero with numbered reasons on failure.

Usage: python scripts/validate.py      (also run by hooks/pre-push)
"""
import ast
import re
import socket
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"

GRAFANA_HEALTH = "http://localhost:3000/api/health"
COLLECTOR_METRICS = "http://localhost:8888/metrics"
COLLECTOR_PORTS = (4317, 4318)
OTEL_ENDPOINT = "http://localhost:4317"

TASK_FIELDS = ["id", "title", "due_at", "done", "created_at"]

SECRET_PATTERNS = {
    "Anthropic/OpenAI key": re.compile(r"sk-(ant-)?[A-Za-z0-9_-]{20,}"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "Slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "hard-coded credential": re.compile(
        r"""(?i)\b(password|passwd|secret|api_key|apikey|token)\b\s*[:=]\s*["'][^"'\s]{8,}["']"""
    ),
}


def out(line: str = "") -> None:
    sys.stdout.write(line + "\n")


def git_files() -> list[Path]:
    """Tracked files plus untracked, non-ignored ones: everything that could be committed."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    return [ROOT / p for p in result.stdout.splitlines() if (ROOT / p).is_file()]


# 1 ---------------------------------------------------------------------------
def check_api_contract() -> list[str]:
    sys.path.insert(0, str(APP_DIR))
    from app import create_app  # noqa: E402  (app/ is not a package)

    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        app = create_app(str(Path(tmp) / "validate.db"))
        routes = {(r.rule, m) for r in app.url_map.iter_rules() for m in r.methods}
        for rule, method in [("/api/tasks", "GET"), ("/api/tasks", "POST"),
                             ("/api/tasks/<int:task_id>", "PATCH")]:
            if (rule, method) not in routes:
                problems.append(f"missing route {method} {rule}")
        client = app.test_client()

        r = client.post("/api/tasks", json={"title": "validate"})
        if r.status_code not in (200, 201) or list(r.get_json() or {}) != TASK_FIELDS:
            problems.append(f"POST /api/tasks {{title}} -> {r.status_code} {r.get_json()}, want Task {TASK_FIELDS}")
        r = client.post("/api/tasks", json={"title": "validate", "due_at": "2030-01-01"})
        if r.status_code not in (200, 201) or (r.get_json() or {}).get("due_at") != "2030-01-01":
            problems.append(f"POST /api/tasks {{title, due_at}} -> {r.status_code} {r.get_json()}")

        r = client.patch("/api/tasks/1", json={"done": True})
        body = r.get_json() or {}
        if r.status_code != 200 or list(body) != TASK_FIELDS or body.get("done") is not True:
            problems.append(f"PATCH /api/tasks/1 {{done}} -> {r.status_code} {body}, want Task with done=true")

        r = client.get("/api/tasks")
        tasks = r.get_json()
        if r.status_code != 200 or not isinstance(tasks, list) or len(tasks) != 2:
            problems.append(f"GET /api/tasks -> {r.status_code} {tasks}, want list of 2 tasks")
        else:
            for t in tasks:
                if list(t) != TASK_FIELDS + ["reminder"] or not isinstance(t["reminder"], bool):
                    problems.append(f"GET /api/tasks item {t} - want {TASK_FIELDS} + boolean reminder")
    return problems


# 2 ---------------------------------------------------------------------------
def check_tests() -> tuple[list[str], str | None]:
    tests = list((ROOT / "tests").glob("**/test_*.py")) + list((ROOT / "tests").glob("**/*_test.py"))
    if not tests:
        return [], "no test files in tests/ yet (suite arrives in Prompt 8) - nothing to run"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")],
        cwd=ROOT, capture_output=True, text=True,
    )
    if result.returncode != 0:
        tail = (result.stdout + result.stderr).strip().splitlines()[-1:] or ["(no output)"]
        return [f"pytest exited {result.returncode}: {tail[0]}"], None
    return [], None


# 3 ---------------------------------------------------------------------------
def _is_main_guard(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__"
        and any(isinstance(c, ast.Constant) and c.value == "__main__" for c in node.test.comparators)
    )


def _debug_calls(tree: ast.AST):
    """Yield (lineno, what) for debug leftovers outside `if __name__ == "__main__":`."""
    def walk(node, in_guard):
        for child in ast.iter_child_nodes(node):
            guarded = in_guard or _is_main_guard(child)
            if isinstance(child, ast.Call) and not guarded:
                f = child.func
                if isinstance(f, ast.Name) and f.id in ("print", "breakpoint"):
                    yield child.lineno, f"{f.id}("
                if isinstance(f, ast.Attribute) and f.attr == "set_trace":
                    yield child.lineno, "pdb.set_trace("
                for kw in child.keywords:
                    if kw.arg == "debug" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        yield child.lineno, "debug=True"
            yield from walk(child, guarded)
    yield from walk(tree, False)


def check_debug_leftovers() -> list[str]:
    problems = []
    for path in git_files():
        if path.suffix != ".py":
            continue
        rel = path.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError as exc:
            problems.append(f"{rel}:{exc.lineno} does not parse: {exc.msg}")
            continue
        problems += [f"{rel}:{line} {what}" for line, what in _debug_calls(tree)]
    return problems


# 4 ---------------------------------------------------------------------------
def check_observability() -> list[str]:
    problems = []
    try:
        with urllib.request.urlopen(GRAFANA_HEALTH, timeout=3) as r:
            if b'"database"' not in r.read() or r.status != 200:
                problems.append(f"Grafana {GRAFANA_HEALTH} unhealthy (HTTP {r.status})")
    except OSError as exc:
        problems.append(f"Grafana {GRAFANA_HEALTH} unreachable: {exc}")
    try:
        with urllib.request.urlopen(COLLECTOR_METRICS, timeout=3) as r:
            if r.status != 200:
                problems.append(f"OTel Collector {COLLECTOR_METRICS} -> HTTP {r.status}")
    except OSError as exc:
        problems.append(f"OTel Collector {COLLECTOR_METRICS} unreachable: {exc}")
    for port in COLLECTOR_PORTS:
        try:
            socket.create_connection(("localhost", port), timeout=3).close()
        except OSError as exc:
            problems.append(f"OTel Collector port {port} not accepting connections: {exc}")
    # OTEL_* vars are stripped from tool subprocesses, so check the launcher that sets them.
    launcher = ROOT / "start-claude.cmd"
    if not launcher.is_file():
        problems.append("start-claude.cmd missing - the session cannot export telemetry")
    elif f"OTEL_EXPORTER_OTLP_ENDPOINT={OTEL_ENDPOINT}" not in launcher.read_text(encoding="utf-8"):
        problems.append(f"start-claude.cmd does not set OTEL_EXPORTER_OTLP_ENDPOINT={OTEL_ENDPOINT}")
    return problems


# 5 ---------------------------------------------------------------------------
def check_secrets() -> list[str]:
    problems = []
    for path in git_files():
        rel = path.relative_to(ROOT).as_posix()
        if path.name == ".env" or path.name.startswith(".env."):
            problems.append(f"{rel} would be committed")
            continue
        if path == Path(__file__).resolve():
            continue  # the patterns above would match themselves
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, pattern in SECRET_PATTERNS.items():
                if pattern.search(line):
                    problems.append(f"{rel}:{lineno} looks like a {name}")
    return problems


def main() -> int:
    failures = 0
    checks = [
        (1, "API contract match", lambda: (check_api_contract(), None)),
        (2, "Tests pass", check_tests),
        (3, "No debug leftovers", lambda: (check_debug_leftovers(), None)),
        (4, "Observability stack reachable", lambda: (check_observability(), None)),
        (5, "No secrets", lambda: (check_secrets(), None)),
    ]
    for number, name, check in checks:
        try:
            problems, note = check()
        except Exception as exc:  # a crashing check is a failing check
            problems, note = [f"check crashed: {type(exc).__name__}: {exc}"], None
        if problems:
            failures += 1
            out(f"[FAIL] {number}. {name}")
            for p in problems:
                out(f"         - {p}")
        elif note:
            out(f"[SKIP] {number}. {name}: {note}")
        else:
            out(f"[PASS] {number}. {name}")
    out()
    if failures:
        out(f"validate: {failures} guardrail(s) failed")
        return 1
    out("validate: all guardrails pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())

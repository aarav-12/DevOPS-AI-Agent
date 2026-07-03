import re
from datetime import datetime, timedelta
from pathlib import Path

# Fixed, resolved log directory. log_file/service is never trusted as a
# raw path — see _resolve_log_path. Loophole closed: without this a log
# reader is one "search logs at ../../.env" away from becoming an
# arbitrary-file-exfiltration tool.
LOGS_DIR = (Path(__file__).resolve().parent.parent / "demo_logs").resolve()

MAX_MATCHES = 50
DEFAULT_SERVICE = "payments-service"

_TIMESTAMP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})")


def _resolve_log_path(service: str) -> Path | None:
    name = (service or DEFAULT_SERVICE).strip()
    # Path(...).name strips every directory component — "../../.env"
    # collapses to ".env.log". This alone should be enough.
    filename = Path(f"{name}.log").name
    candidate = (LOGS_DIR / filename).resolve()
    # Defense in depth: verify the resolved path is still inside LOGS_DIR.
    # Catches anything clever the strip above might miss (symlinks, odd
    # unicode). Two locks on one door, deliberately.
    if not candidate.is_relative_to(LOGS_DIR):
        return None
    if not candidate.is_file():
        return None
    return candidate


def _read_lines(service: str) -> list[str] | None:
    path = _resolve_log_path(service)
    if path is None:
        return None
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _parse_ts(line: str):
    m = _TIMESTAMP_RE.match(line)
    if not m:
        return None
    try:
        return datetime.fromisoformat(m.group(1))
    except ValueError:
        return None


def search_logs_impl(query: str, service: str = "", since_minutes: int = 60) -> str:
    lines = _read_lines(service)
    if lines is None:
        return f"No log file found for service '{service or DEFAULT_SERVICE}'."

    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error as e:
        return f"Invalid search pattern: {e}"

    # windowing is relative to the log's own latest timestamp, not wall
    # clock — a static demo fixture stays demoable no matter when it runs.
    timestamps = [t for t in (_parse_ts(l) for l in lines) if t]
    reference = max(timestamps) if timestamps else None
    cutoff = reference - timedelta(minutes=since_minutes) if reference else None

    matches = []
    for line in lines:
        if not pattern.search(line):
            continue
        if cutoff:
            ts = _parse_ts(line)
            if ts and ts < cutoff:
                continue
        matches.append(line)

    matches = matches[-MAX_MATCHES:]

    svc_tag = f"[{service}] " if service else ""
    header = f"Log search: '{query}' {svc_tag}(last {since_minutes}m)"
    if not matches:
        return f"{header}\nNo matches found."

    return f"{header}\n" + "\n".join(matches) + f"\n{len(matches)} matches found."


def get_error_rate_impl(service: str, window_minutes: int = 5) -> str:
    lines = _read_lines(service)
    if lines is None:
        return f"No log file found for service '{service}'."

    timestamps = [t for t in (_parse_ts(l) for l in lines) if t]
    reference = max(timestamps) if timestamps else None
    cutoff = reference - timedelta(minutes=window_minutes) if reference else None

    window_lines = lines
    if cutoff:
        window_lines = [l for l in lines if (_parse_ts(l) or reference) >= cutoff]

    total = len(window_lines)
    if total == 0:
        return f"{service} error rate (last {window_minutes}m): 0.0% (no log lines in window)"

    errors = sum(1 for l in window_lines if " ERROR " in l or " FATAL " in l)
    rate = errors / total * 100

    return f"{service} error rate (last {window_minutes}m): {rate:.1f}% ({errors}/{total} lines)"

import json
from datetime import datetime, timezone
from pathlib import Path


AUDIT_LOG_PATH = Path("audit.jsonl")

# Redact at the logging layer — one place that covers every current and
# future tool, instead of trusting every future tool author to remember.
_SENSITIVE_SUBSTRINGS = {"token", "password", "secret", "key", "credential", "auth"}


def _redact_params(params: dict) -> dict:
    return {
        k: "[REDACTED]" if any(s in k.lower() for s in _SENSITIVE_SUBSTRINGS) else v
        for k, v in params.items()
    }


def log_tool_call(
    tool_name: str,
    params: dict,
    result: str,
    level: str,
    approved_by: str = "auto"
):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "params": _redact_params(params),
        "result_preview": result[:200],
        "permission_level": level,
        "approved_by": approved_by,
    }

    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
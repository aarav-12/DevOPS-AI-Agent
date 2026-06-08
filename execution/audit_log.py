import json
from datetime import datetime, timezone
from pathlib import Path


AUDIT_LOG_PATH = Path("audit.jsonl")


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
        "params": params,
        "result_preview": result[:200],
        "permission_level": level,
        "approved_by": approved_by,
    }

    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
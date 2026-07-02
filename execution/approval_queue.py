import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock


QUEUE_PATH = Path("approval_queue.json")
# Correctness over cleverness: a queue of destructive actions must never lose writes.
_LOCK = FileLock(str(QUEUE_PATH) + ".lock")


def _load() -> list:
    if not QUEUE_PATH.exists():
        return []
    return json.loads(QUEUE_PATH.read_text())


def _save(queue: list):
    QUEUE_PATH.write_text(json.dumps(queue, indent=2))


def submit(tool_name: str, params: dict, context: str) -> str:
    with _LOCK:
        queue = _load()
        request_id = str(uuid.uuid4())[:8]
        queue.append({
            "id": request_id,
            "tool": tool_name,
            "params": params,
            "context": context,
            "status": "pending",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        })
        _save(queue)
    return request_id


def approve(request_id: str) -> dict | None:
    with _LOCK:
        queue = _load()
        for item in queue:
            if item["id"] == request_id and item["status"] == "pending":
                item["status"] = "approved"
                item["approved_at"] = datetime.now(timezone.utc).isoformat()
                _save(queue)
                return item
    return None


def deny(request_id: str) -> bool:
    with _LOCK:
        queue = _load()
        for item in queue:
            if item["id"] == request_id and item["status"] == "pending":
                item["status"] = "denied"
                _save(queue)
                return True
    return False


def mark_executed(request_id: str, result: str) -> None:
    with _LOCK:
        queue = _load()
        for item in queue:
            if item["id"] == request_id:
                item["status"] = "executed"
                item["result"] = result
                item["executed_at"] = datetime.now(timezone.utc).isoformat()
                _save(queue)
                return


def mark_failed(request_id: str, error: str) -> None:
    with _LOCK:
        queue = _load()
        for item in queue:
            if item["id"] == request_id:
                item["status"] = "failed"
                item["error"] = error
                item["failed_at"] = datetime.now(timezone.utc).isoformat()
                _save(queue)
                return


def get_pending() -> list:
    with _LOCK:
        return [i for i in _load() if i["status"] == "pending"]

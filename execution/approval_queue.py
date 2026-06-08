import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


QUEUE_PATH = Path("approval_queue.json")


def _load() -> list:
    if not QUEUE_PATH.exists():
        return []

    return json.loads(QUEUE_PATH.read_text())


def _save(queue: list):
    QUEUE_PATH.write_text(
        json.dumps(queue, indent=2)
    )


def submit(
    tool_name: str,
    params: dict,
    context: str
) -> str:
    queue = _load()

    request_id = str(uuid.uuid4())[:8]

    queue.append({
        "id": request_id,
        "tool": tool_name,
        "params": params,
        "context": context,
        "status": "pending",
        "submitted_at": datetime.now(
            timezone.utc
        ).isoformat(),
    })

    _save(queue)

    return request_id


def approve(request_id: str) -> dict | None:
    queue = _load()

    for item in queue:
        if (
            item["id"] == request_id
            and item["status"] == "pending"
        ):
            item["status"] = "approved"
            item["approved_at"] = datetime.now(
                timezone.utc
            ).isoformat()

            _save(queue)
            return item

    return None


def deny(request_id: str) -> bool:
    queue = _load()

    for item in queue:
        if (
            item["id"] == request_id
            and item["status"] == "pending"
        ):
            item["status"] = "denied"
            _save(queue)
            return True

    return False


def get_pending() -> list:
    return [
        i for i in _load()
        if i["status"] == "pending"
    ]
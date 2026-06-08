from execution.permission_engine import (
    check_permission,
)
from execution.audit_log import (
    log_tool_call,
)
from execution.approval_queue import (
    submit,
)


def execute_tool(
    tool_name: str,
    params: dict,
    action_fn,
    context: str = "",
) -> str:

    result = check_permission(
        tool_name
    )

    if not result.allowed:
        request_id = submit(
            tool_name,
            params,
            context,
        )

        return (
            f"ACTION BLOCKED: '{tool_name}' "
            f"requires human approval "
            f"(EXEC level).\n"
            f"Request ID: {request_id}\n"
            f"To approve, run: "
            f"python approve.py approve "
            f"{request_id}\n"
            f"To deny, run: "
            f"python approve.py deny "
            f"{request_id}"
        )

    output = action_fn()

    log_tool_call(
        tool_name,
        params,
        str(output),
        result.level.value,
    )

    return str(output)
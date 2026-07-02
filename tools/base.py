from execution.permission_engine import check_permission
from execution.audit_log import log_tool_call
from execution.approval_queue import submit
from execution.constants import APPROVE_CMD_TEMPLATE, DENY_CMD_TEMPLATE, LIST_CMD


def execute_tool(
    tool_name: str,
    params: dict,
    action_fn,
    context: str = "",
) -> str:

    result = check_permission(tool_name)

    if not result.allowed:
        request_id = submit(tool_name, params, context)
        # guard: without this entry the audit log shows an approved execution
        # with no prior attempt — an auditor cannot distinguish "Claude requested
        # this and a human approved it" from "this entry appeared from nowhere."
        log_tool_call(
            tool_name,
            params,
            f"blocked — queued as {request_id}",
            result.level.value,
            approved_by="pending",
        )
        return (
            f"ACTION BLOCKED: '{tool_name}' requires human approval (EXEC level).\n"
            f"Request ID: {request_id}\n"
            f"To approve: {APPROVE_CMD_TEMPLATE.format(request_id=request_id)}\n"
            f"To deny:    {DENY_CMD_TEMPLATE.format(request_id=request_id)}\n"
            f"To list pending: {LIST_CMD}"
        )

    output = action_fn()

    log_tool_call(
        tool_name,
        params,
        str(output),
        result.level.value,
    )

    return str(output)

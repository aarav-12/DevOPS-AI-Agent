from enum import Enum
from typing import NamedTuple


class PermissionLevel(Enum):
    READ = "read"
    WRITE = "write"
    EXEC = "exec"


class PermissionResult(NamedTuple):
    allowed: bool
    level: PermissionLevel
    reason: str


TOOL_REGISTRY: dict[str, PermissionLevel] = {
    "get_system_status": PermissionLevel.READ,
    "list_pods": PermissionLevel.READ,
    "get_pod_logs": PermissionLevel.READ,
    "get_deployment_status": PermissionLevel.READ,
    "get_recent_commits": PermissionLevel.READ,
    "get_pr_status": PermissionLevel.READ,
    "get_workflow_run": PermissionLevel.READ,
    "search_logs": PermissionLevel.READ,
    "get_error_rate": PermissionLevel.READ,
    "get_ticket_status": PermissionLevel.READ,

    "create_jira_ticket": PermissionLevel.WRITE,
    "add_jira_comment": PermissionLevel.WRITE,
    "post_slack_message": PermissionLevel.WRITE,
    "post_incident_alert": PermissionLevel.WRITE,

    "rollback_deployment": PermissionLevel.EXEC,
    "restart_pod": PermissionLevel.EXEC,
    "scale_deployment": PermissionLevel.EXEC,
    "delete_pod": PermissionLevel.EXEC,
    "run_shell_command": PermissionLevel.EXEC,
}


def check_permission(tool_name: str) -> PermissionResult:
    level = TOOL_REGISTRY.get(tool_name, PermissionLevel.EXEC)

    if level == PermissionLevel.EXEC:
        return PermissionResult(
            allowed=False,
            level=level,
            reason=f"'{tool_name}' is an EXEC-level operation and requires human approval."
        )

    return PermissionResult(
        allowed=True,
        level=level,
        reason=f"Allowed at {level.value} level"
    )
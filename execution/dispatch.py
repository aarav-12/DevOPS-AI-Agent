from typing import Callable

from tools.k8s_tools import (
    rollback_deployment_impl,
    restart_pod_impl,
    scale_deployment_impl,
    delete_pod_impl,
)


def run_shell_command_impl(command: str, **_) -> str:
    # guard: run_shell_command has no domain home — kept here to prevent
    # it from being treated as safe enough to live in a tools/ file.
    # Production: subprocess.run with strict allowlist validation.
    return f"[STUB] Would run shell command: {command}"


DISPATCH: dict[str, Callable] = {
    "rollback_deployment": rollback_deployment_impl,
    "restart_pod":         restart_pod_impl,
    "scale_deployment":    scale_deployment_impl,
    "delete_pod":          delete_pod_impl,
    "run_shell_command":   run_shell_command_impl,
}

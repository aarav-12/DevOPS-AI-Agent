def list_pods_impl(namespace: str = "default") -> str:
    return (
        f"Pods in {namespace}:\n"
        "  payments-pod-7f4b  CrashLoopBackOff  12 restarts  2m ago\n"
        "  orders-pod-3a1c    Running            0 restarts   14h ago\n"
        "  auth-pod-9d2e      Running            0 restarts   14h ago"
    )


def get_pod_logs_impl(pod: str, namespace: str = "default", tail: int = 50) -> str:
    return (
        f"[{namespace}/{pod}] Last {tail} lines:\n"
        "2026-07-02T14:01:12Z ERROR connection refused: postgres://payments-db:5432\n"
        "2026-07-02T14:01:12Z FATAL failed to acquire db connection after 3 retries\n"
        "2026-07-02T14:01:12Z INFO  pod terminating"
    )


def get_deployment_status_impl(deployment: str, namespace: str = "default") -> str:
    return (
        f"Deployment: {deployment} ({namespace})\n"
        "Desired:    3\n"
        "Ready:      1\n"
        "Available:  1\n"
        "Image:      payments-service:v2.4.1\n"
        "Last rollout: 2026-07-02T13:58:00Z  FAILED — 2 of 3 pods not ready"
    )


# ── EXEC implementations ──────────────────────────────────────────────────
# These are called by approve.py via DISPATCH after human approval.
# They are never called from the MCP server path — execute_tool blocks
# EXEC tools before action_fn is ever invoked.

def rollback_deployment_impl(deployment: str, namespace: str = "default", **_) -> str:
    # Production: kubectl rollout undo deployment/<deployment> -n <namespace>
    return f"[STUB] Rolled back deployment '{deployment}' in namespace '{namespace}'"


def restart_pod_impl(pod: str, namespace: str = "default", **_) -> str:
    # Production: kubectl delete pod <pod> -n <namespace>  (k8s recreates it)
    return f"[STUB] Restarted pod '{pod}' in namespace '{namespace}'"


def scale_deployment_impl(
    deployment: str, replicas: int, namespace: str = "default", **_
) -> str:
    # Production: kubectl scale deployment/<deployment> --replicas=<n> -n <namespace>
    return (
        f"[STUB] Scaled deployment '{deployment}' "
        f"to {replicas} replicas in namespace '{namespace}'"
    )


def delete_pod_impl(pod: str, namespace: str = "default", **_) -> str:
    # Production: kubectl delete pod <pod> --force -n <namespace>
    return f"[STUB] Force-deleted pod '{pod}' in namespace '{namespace}'"

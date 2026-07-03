from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

MAX_TAIL_LINES = 200

_core_v1 = None
_apps_v1 = None


def get_k8s_clients():
    # try local/dev kubeconfig (laptop, minikube) first, fall back to the
    # in-cluster service account config used when actually running inside
    # a pod. Without this fallback the project only ever works on one
    # machine, which undercuts the "forward deployed" framing entirely.
    global _core_v1, _apps_v1

    if _core_v1 is None:
        try:
            config.load_kube_config()
        except config.ConfigException:
            config.load_incluster_config()
        _core_v1 = client.CoreV1Api()
        _apps_v1 = client.AppsV1Api()

    return _core_v1, _apps_v1


def list_pods_impl(namespace: str = "default") -> str:
    try:
        core_v1, _ = get_k8s_clients()
        pods = core_v1.list_namespaced_pod(namespace=namespace)
    except config.ConfigException as e:
        return f"Could not reach a Kubernetes cluster: {e}"
    except ApiException as e:
        return f"Kubernetes API error listing pods in '{namespace}': {e.status} {e.reason}"

    if not pods.items:
        return f"No pods found in namespace '{namespace}'."

    lines = [f"Pods in {namespace}:"]
    for pod in pods.items:
        restarts = sum(
            cs.restart_count for cs in (pod.status.container_statuses or [])
        )
        # restart count is the cheapest crash signal in k8s — a pod
        # "Running" with 47 restarts is lying about being fine.
        lines.append(f"  {pod.metadata.name:<28} {pod.status.phase:<12} {restarts} restarts")

    return "\n".join(lines)


def get_pod_logs_impl(pod: str, namespace: str = "default", tail_lines: int = 30) -> str:
    tail_lines = max(1, min(tail_lines, MAX_TAIL_LINES))

    try:
        core_v1, _ = get_k8s_clients()
        logs = core_v1.read_namespaced_pod_log(
            name=pod, namespace=namespace, tail_lines=tail_lines
        )
    except config.ConfigException as e:
        return f"Could not reach a Kubernetes cluster: {e}"
    except ApiException as e:
        return f"Kubernetes API error fetching logs for '{pod}' in '{namespace}': {e.status} {e.reason}"

    return f"[{namespace}/{pod}] Last {tail_lines} lines:\n{logs}"


def get_deployment_status_impl(deployment: str, namespace: str = "default") -> str:
    try:
        _, apps_v1 = get_k8s_clients()
        dep = apps_v1.read_namespaced_deployment(name=deployment, namespace=namespace)
    except config.ConfigException as e:
        return f"Could not reach a Kubernetes cluster: {e}"
    except ApiException as e:
        if e.status == 404:
            return f"Deployment '{deployment}' not found in namespace '{namespace}'."
        return f"Kubernetes API error reading deployment '{deployment}': {e.status} {e.reason}"

    status = dep.status
    image = dep.spec.template.spec.containers[0].image if dep.spec.template.spec.containers else "unknown"

    return (
        f"Deployment: {deployment} ({namespace})\n"
        f"Desired:    {dep.spec.replicas}\n"
        f"Ready:      {status.ready_replicas or 0}\n"
        f"Available:  {status.available_replicas or 0}\n"
        f"Image:      {image}"
    )


# ── EXEC implementations ──────────────────────────────────────────────────
# SIMULATED. These do not call the Kubernetes API — building real
# kubectl-rollout-undo/scale/delete plumbing is not the point of this
# project; the approval gate in front of them is. Every return string is
# tagged [SIMULATED] so the demo discloses this on its own, before anyone
# has to ask "wait, did that actually touch the cluster?"
# They are called by approve.py via DISPATCH after human approval, and
# are never called from the MCP server path — execute_tool blocks EXEC
# tools before action_fn is ever invoked.

def rollback_deployment_impl(deployment: str, namespace: str = "default", **_) -> str:
    # SIMULATED — see module banner above. Production: kubectl rollout
    # undo deployment/<deployment> -n <namespace>
    return f"[SIMULATED] Rolled back deployment '{deployment}' in namespace '{namespace}'"


def restart_pod_impl(pod: str, namespace: str = "default", **_) -> str:
    # SIMULATED — see module banner above. Production: kubectl delete
    # pod <pod> -n <namespace> (k8s recreates it)
    return f"[SIMULATED] Restarted pod '{pod}' in namespace '{namespace}'"


def scale_deployment_impl(
    deployment: str, replicas: int, namespace: str = "default", **_
) -> str:
    # SIMULATED — see module banner above. Production: kubectl scale
    # deployment/<deployment> --replicas=<n> -n <namespace>
    return (
        f"[SIMULATED] Scaled deployment '{deployment}' "
        f"to {replicas} replicas in namespace '{namespace}'"
    )


def delete_pod_impl(pod: str, namespace: str = "default", **_) -> str:
    # SIMULATED — see module banner above. Production: kubectl delete
    # pod <pod> --force -n <namespace>
    return f"[SIMULATED] Force-deleted pod '{pod}' in namespace '{namespace}'"

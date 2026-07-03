from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from tools.base import execute_tool
from tools.github_tools import (
    get_recent_commits_impl,
    get_pr_status_impl,
    get_workflow_run_impl,
)
from tools.k8s_tools import (
    list_pods_impl,
    get_pod_logs_impl,
    get_deployment_status_impl,
)
from tools.logs_tools import (
    search_logs_impl,
    get_error_rate_impl,
)
from tools.jira_slack_tools import (
    get_ticket_status_impl,
    create_jira_ticket_impl,
    add_jira_comment_impl,
    post_slack_message_impl,
    post_incident_alert_impl,
)

load_dotenv()
mcp = FastMCP("devops-demo")


# ── READ tools ────────────────────────────────────────────────────────────
# Every tool routes through execute_tool regardless of permission level.
# guard: bypassing execute_tool for "harmless" tools breaks the audit log
# completeness guarantee — an incomplete audit is the same as no audit.

@mcp.tool()
def get_system_status() -> str:
    """Get the current status of all production services.
    Use this to assess overall system health before investigating further."""
    return execute_tool(
        "get_system_status",
        {},
        lambda: (
            "payments-service: DEGRADED (high error rate)\n"
            "orders-service:   OK\n"
            "auth-service:     OK"
        ),
    )


@mcp.tool()
def list_pods(namespace: str = "default") -> str:
    """List all Kubernetes pods in a namespace with their current status.
    Use when checking whether a service is healthy — restart count is the
    cheapest signal that a "Running" pod is actually crash-looping."""
    return execute_tool(
        "list_pods",
        {"namespace": namespace},
        lambda: list_pods_impl(namespace),
    )


@mcp.tool()
def get_pod_logs(pod: str, namespace: str = "default", tail_lines: int = 30) -> str:
    """Fetch the most recent log lines from a specific pod (capped at 200 lines).
    Use when diagnosing crashes or restarts."""
    return execute_tool(
        "get_pod_logs",
        {"pod": pod, "namespace": namespace, "tail_lines": tail_lines},
        lambda: get_pod_logs_impl(pod, namespace, tail_lines),
    )


@mcp.tool()
def get_deployment_status(deployment: str, namespace: str = "default") -> str:
    """Get the rollout status and replica health of a Kubernetes deployment.
    Use to confirm whether a rollout is stuck before deciding to roll it back."""
    return execute_tool(
        "get_deployment_status",
        {"deployment": deployment, "namespace": namespace},
        lambda: get_deployment_status_impl(deployment, namespace),
    )


@mcp.tool()
def get_recent_commits(repo: str, branch: str = "main", n: int = 5) -> str:
    """Get the most recent commits on a GitHub repository branch (capped at 20).
    Use when triaging an incident to answer "what changed?"."""
    return execute_tool(
        "get_recent_commits",
        {"repo": repo, "branch": branch, "n": n},
        lambda: get_recent_commits_impl(repo, branch, n),
    )


@mcp.tool()
def get_pr_status(repo: str, pr_number: int) -> str:
    """Get the title, state, CI checks, and mergeability of a GitHub pull request.
    Use when a suspect commit traces back to a PR and you need to know if it
    passed CI before it merged."""
    return execute_tool(
        "get_pr_status",
        {"repo": repo, "pr_number": pr_number},
        lambda: get_pr_status_impl(repo, pr_number),
    )


@mcp.tool()
def get_workflow_run(repo: str, run_id: int) -> str:
    """Get the status and conclusion of a specific GitHub Actions workflow run.
    Use to check whether a deploy pipeline actually succeeded before assuming
    the running image matches the merged code."""
    return execute_tool(
        "get_workflow_run",
        {"repo": repo, "run_id": run_id},
        lambda: get_workflow_run_impl(repo, run_id),
    )


@mcp.tool()
def search_logs(query: str, service: str = "", since_minutes: int = 60) -> str:
    """Search production logs for a query string, optionally filtered to one service.
    Use this first, before paging anyone or calling an external API — it's the
    cheapest, fastest triage signal."""
    return execute_tool(
        "search_logs",
        {"query": query, "service": service, "since_minutes": since_minutes},
        lambda: search_logs_impl(query, service, since_minutes),
    )


@mcp.tool()
def get_error_rate(service: str, window_minutes: int = 5) -> str:
    """Get the current error rate percentage for a named service.
    Use to quantify how bad an incident is or confirm a fix actually worked."""
    return execute_tool(
        "get_error_rate",
        {"service": service, "window_minutes": window_minutes},
        lambda: get_error_rate_impl(service, window_minutes),
    )


@mcp.tool()
def get_ticket_status(ticket_id: str) -> str:
    """Get the current status, assignee, and priority of a Jira ticket.
    Use to check whether an incident already has an open ticket before
    creating a duplicate."""
    return execute_tool(
        "get_ticket_status",
        {"ticket_id": ticket_id},
        lambda: get_ticket_status_impl(ticket_id),
    )


# ── WRITE tools ───────────────────────────────────────────────────────────
# WRITE tools run immediately (no approval gate) but are fully audit-logged.
# They affect external systems — Jira, Slack — so the audit trail is the
# primary accountability mechanism.

@mcp.tool()
def create_jira_ticket(
    project: str, summary: str, description: str, priority: str = "High"
) -> str:
    """Create a new Jira ticket in the given project.
    Use once you've confirmed an incident is real and needs a paper trail —
    not for every anomaly you check and rule out."""
    return execute_tool(
        "create_jira_ticket",
        {"project": project, "summary": summary, "description": description, "priority": priority},
        lambda: create_jira_ticket_impl(project, summary, description, priority),
    )


@mcp.tool()
def add_jira_comment(ticket_id: str, comment: str) -> str:
    """Append a comment to an existing Jira ticket.
    Use to post findings or status updates to a ticket that already exists."""
    return execute_tool(
        "add_jira_comment",
        {"ticket_id": ticket_id, "comment": comment},
        lambda: add_jira_comment_impl(ticket_id, comment),
    )


@mcp.tool()
def post_slack_message(channel: str, message: str) -> str:
    """Post a message to a Slack channel.
    Use for routine updates that don't warrant a full incident alert."""
    return execute_tool(
        "post_slack_message",
        {"channel": channel, "message": message},
        lambda: post_slack_message_impl(channel, message),
    )


@mcp.tool()
def post_incident_alert(service: str, severity: str, message: str) -> str:
    """Fire a P0/P1 incident alert to #incidents and PagerDuty.
    severity should be P0 or P1."""
    return execute_tool(
        "post_incident_alert",
        {"service": service, "severity": severity, "message": message},
        lambda: post_incident_alert_impl(service, severity, message),
    )


# ── EXEC tools ────────────────────────────────────────────────────────────
# execute_tool blocks these before action_fn is ever called — the lambda
# bodies below are unreachable from the MCP server path.
# The real implementations live in execution/dispatch.py and are invoked
# only after a human approves via approve.py.

@mcp.tool()
def rollback_deployment(
    deployment: str, namespace: str = "default", context: str = ""
) -> str:
    """Roll back a Kubernetes deployment to its previous image.
    REQUIRES HUMAN APPROVAL — triggers a production change.
    context: explain why you are requesting this rollback."""
    return execute_tool(
        "rollback_deployment",
        {"deployment": deployment, "namespace": namespace},
        lambda: "[unreachable — EXEC tools are dispatched via approve.py]",
        context,
    )


@mcp.tool()
def restart_pod(pod: str, namespace: str = "default", context: str = "") -> str:
    """Delete a pod so Kubernetes recreates it from the current image.
    REQUIRES HUMAN APPROVAL — disrupts live traffic for that pod.
    context: explain why you are requesting this restart."""
    return execute_tool(
        "restart_pod",
        {"pod": pod, "namespace": namespace},
        lambda: "[unreachable — EXEC tools are dispatched via approve.py]",
        context,
    )


@mcp.tool()
def scale_deployment(
    deployment: str, replicas: int, namespace: str = "default", context: str = ""
) -> str:
    """Scale a Kubernetes deployment to a specific replica count.
    REQUIRES HUMAN APPROVAL — affects capacity and cost.
    context: explain why you are requesting this scale change."""
    return execute_tool(
        "scale_deployment",
        {"deployment": deployment, "replicas": replicas, "namespace": namespace},
        lambda: "[unreachable — EXEC tools are dispatched via approve.py]",
        context,
    )


@mcp.tool()
def delete_pod(pod: str, namespace: str = "default", context: str = "") -> str:
    """Forcefully delete a pod.
    REQUIRES HUMAN APPROVAL — prefer restart_pod for graceful cycling.
    context: explain why you are requesting this deletion."""
    return execute_tool(
        "delete_pod",
        {"pod": pod, "namespace": namespace},
        lambda: "[unreachable — EXEC tools are dispatched via approve.py]",
        context,
    )


if __name__ == "__main__":
    mcp.run()

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from tools.base import execute_tool
from tools.github_tools import (
    get_recent_commits_impl,
    get_pr_status_impl
)

mcp = FastMCP("devops-demo")

load_dotenv()


@mcp.tool()
def get_system_status() -> str:
    """Get the current status of all production services.
    Use this when the user asks about system health or production issues."""
    return "payments-service: DEGRADED (high error rate). orders-service: OK. auth-service: OK."


@mcp.tool()
def list_pods(namespace: str = "default") -> str:
    """List all Kubernetes pods in a given namespace.
    Use this when the user asks about running services or pods."""
    return f"Pods in {namespace}: payments-pod-7f4b (CrashLoopBackOff, 12 restarts), orders-pod-3a1c (Running)"


@mcp.tool()
def get_recent_commits(
    repo: str,
    branch: str = "main"
) -> str:

    return execute_tool(
        "get_recent_commits",
        {
            "repo": repo,
            "branch": branch
        },
        lambda: get_recent_commits_impl(
            repo,
            branch
        )
    )


@mcp.tool()
def get_pr_status(
    repo: str,
    pr_number: int
) -> str:

    return execute_tool(
        "get_pr_status",
        {
            "repo": repo,
            "pr_number": pr_number
        },
        lambda: get_pr_status_impl(
            repo,
            pr_number
        )
    )


if __name__ == "__main__":
    mcp.run()
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("devops-demo")

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

if __name__ == "__main__":
    mcp.run()
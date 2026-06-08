from tools.base import execute_tool


print(
    execute_tool(
        "get_system_status",
        {},
        lambda: "all good",
        "testing"
    )
)

print()

print(
    execute_tool(
        "rollback_deployment",
        {"name": "payments"},
        lambda: "rolled back",
        "testing"
    )
)
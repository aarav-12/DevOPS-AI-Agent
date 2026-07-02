from tools.base import execute_tool
from execution.constants import APPROVE_CMD_TEMPLATE, DENY_CMD_TEMPLATE, LIST_CMD
from execution.audit_log import _redact_params


# --- original smoke tests ---

print(
    execute_tool(
        "get_system_status",
        {},
        lambda: "all good",
        "testing"
    )
)

print()

blocked = execute_tool(
    "rollback_deployment",
    {"deployment": "payments"},
    lambda: "rolled back",
    "testing"
)
print(blocked)


# --- Fix 2: drift-prevention ---
# If the CLI format ever changes, one side updating without the other
# will fail this assertion immediately.

def _extract_request_id_from_blocked(message: str) -> str:
    for line in message.splitlines():
        if line.startswith("Request ID: "):
            return line.split("Request ID: ")[1].strip()
    raise AssertionError("No 'Request ID:' line found in blocked message")

request_id = _extract_request_id_from_blocked(blocked)

assert f"python approve.py {request_id}" in blocked, (
    "Blocked message does not match APPROVE_CMD_TEMPLATE — CLI and message have drifted"
)
assert f"python approve.py --deny {request_id}" in blocked, (
    "Blocked message does not match DENY_CMD_TEMPLATE — CLI and message have drifted"
)
assert "python approve.py --list" in blocked, (
    "Blocked message does not contain LIST_CMD — CLI and message have drifted"
)

print()
print("PASS: blocked message matches CLI constants")


# --- Fix 3: param redaction ---

sensitive_cases = {
    "github_token": "ghp_abc123",
    "api_key": "sk-xyz",
    "db_password": "hunter2",
    "AUTH_HEADER": "Bearer token",
    "webhook_secret": "s3cr3t",
    "api_credential": "cred_value",
}
redacted = _redact_params(sensitive_cases)
for k, v in redacted.items():
    assert v == "[REDACTED]", f"Expected [REDACTED] for key '{k}', got '{v}'"

safe_cases = {"deployment": "payments", "namespace": "default", "replicas": 3}
safe_redacted = _redact_params(safe_cases)
assert safe_redacted == safe_cases, "Safe params were incorrectly redacted"

print("PASS: sensitive params are redacted; safe params are preserved")

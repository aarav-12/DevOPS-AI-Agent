import argparse
import getpass
import sys

from execution.approval_queue import approve, deny, get_pending, mark_executed, mark_failed
from execution.audit_log import log_tool_call
from execution.constants import APPROVE_CMD_TEMPLATE, DENY_CMD_TEMPLATE, LIST_CMD
from execution.dispatch import DISPATCH
from execution.permission_engine import PermissionLevel


def _run_approved(item: dict, approver: str) -> None:
    tool_name = item["tool"]
    params = item["params"]
    request_id = item["id"]

    impl = DISPATCH.get(tool_name)
    if impl is None:
        error = f"no dispatch entry for '{tool_name}'"
        mark_failed(request_id, error)
        print(f"FAILED: {error}")
        return

    try:
        result = impl(**params)
    except Exception as exc:
        error = str(exc)
        mark_failed(request_id, error)
        log_tool_call(
            tool_name,
            params,
            f"ERROR: {error}",
            PermissionLevel.EXEC.value,
            approved_by=approver,
        )
        print(f"FAILED during execution: {error}")
        return

    mark_executed(request_id, str(result))
    log_tool_call(
        tool_name,
        params,
        str(result),
        PermissionLevel.EXEC.value,
        approved_by=approver,
    )
    print(f"Executed: {tool_name}")
    print(f"Result:   {result}")


def _list_pending() -> None:
    pending = get_pending()
    if not pending:
        print("No pending requests.")
        return
    print(f"{'ID':<10} {'TOOL':<25} {'SUBMITTED':<32} CONTEXT")
    print("-" * 85)
    for item in pending:
        print(
            f"{item['id']:<10} "
            f"{item['tool']:<25} "
            f"{item['submitted_at']:<32} "
            f"{item.get('context', '')}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Approve or deny queued EXEC-level tool requests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            f"  {APPROVE_CMD_TEMPLATE.format(request_id='<id>')}\n"
            f"  {DENY_CMD_TEMPLATE.format(request_id='<id>')}\n"
            f"  {LIST_CMD}"
        ),
    )
    parser.add_argument(
        "request_id",
        nargs="?",
        help="Request ID to approve.",
    )
    parser.add_argument(
        "--deny",
        metavar="REQUEST_ID",
        help="Deny a pending request.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all pending requests.",
    )
    parser.add_argument(
        "--approver",
        default=getpass.getuser(),
        help="Name of the person approving (default: OS username).",
    )

    args = parser.parse_args()

    if args.list:
        _list_pending()
        sys.exit(0)

    if args.deny:
        if deny(args.deny):
            print(f"Denied request {args.deny}")
        else:
            print(f"Request {args.deny} not found or already processed.")
        sys.exit(0)

    if not args.request_id:
        parser.print_help()
        sys.exit(1)

    item = approve(args.request_id)
    if item is None:
        print(f"Request {args.request_id} not found or already processed.")
        sys.exit(1)

    _run_approved(item, approver=args.approver)

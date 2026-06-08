import sys

from execution.approval_queue import (
    approve,
    deny,
)


if __name__ == "__main__":

    action = sys.argv[1]
    request_id = sys.argv[2]

    if action == "approve":
        item = approve(request_id)

        if item:
            print(
                f"Approved: "
                f"{item['tool']} "
                f"with params "
                f"{item['params']}"
            )

            # TODO:
            # execute tool here

        else:
            print(
                f"Request "
                f"{request_id} "
                f"not found "
                f"or already processed"
            )

    elif action == "deny":

        if deny(request_id):
            print(
                f"Denied request "
                f"{request_id}"
            )
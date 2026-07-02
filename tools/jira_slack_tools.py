import uuid


def get_ticket_status_impl(ticket_id: str) -> str:
    return (
        f"Ticket {ticket_id}\n"
        "Summary:  payments-service CrashLoopBackOff — prod incident\n"
        "Status:   In Progress\n"
        "Assignee: on-call engineer\n"
        "Priority: P1"
    )


def create_jira_ticket_impl(
    project: str, summary: str, description: str, priority: str = "High"
) -> str:
    ticket_id = f"{project}-{uuid.uuid4().hex[:4].upper()}"
    return f"Created {ticket_id}: '{summary}' [{priority}] in project {project}"


def add_jira_comment_impl(ticket_id: str, comment: str) -> str:
    preview = comment[:80] + ("..." if len(comment) > 80 else "")
    return f"Added comment to {ticket_id}: '{preview}'"


def post_slack_message_impl(channel: str, message: str) -> str:
    return f"[STUB] Posted to #{channel}: {message[:120]}"


def post_incident_alert_impl(service: str, severity: str, message: str) -> str:
    return (
        f"[STUB] Incident alert fired — "
        f"{severity.upper()} | {service} | {message[:80]}"
    )

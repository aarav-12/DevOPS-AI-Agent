import json
import os
import time
from pathlib import Path

from jira import JIRA
from jira.exceptions import JIRAError
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

_jira_client = None
_slack_client = None

DEDUPE_PATH = (Path(__file__).resolve().parent.parent / "alert_dedupe.json")
DEDUPE_WINDOW_SECONDS = 300
INCIDENTS_CHANNEL = "#incidents"


def get_jira_client():
    global _jira_client

    if _jira_client is None:
        server = os.environ.get("JIRA_SERVER")
        email = os.environ.get("JIRA_EMAIL")
        token = os.environ.get("JIRA_API_TOKEN")
        if not all([server, email, token]):
            raise RuntimeError(
                "Jira is not configured — set JIRA_SERVER, JIRA_EMAIL, "
                "JIRA_API_TOKEN in .env"
            )
        _jira_client = JIRA(server=server, basic_auth=(email, token))

    return _jira_client


def get_slack_client():
    global _slack_client

    if _slack_client is None:
        token = os.environ.get("SLACK_BOT_TOKEN")
        if not token:
            raise RuntimeError("Slack is not configured — set SLACK_BOT_TOKEN in .env")
        _slack_client = WebClient(token=token)

    return _slack_client


def get_ticket_status_impl(ticket_id: str) -> str:
    try:
        issue = get_jira_client().issue(ticket_id)
    except RuntimeError as e:
        return str(e)
    except JIRAError as e:
        if e.status_code == 404:
            return f"Ticket {ticket_id} not found."
        return f"Jira rejected the request: {e.status_code} {e.text}"

    fields = issue.fields
    return (
        f"Ticket {ticket_id}\n"
        f"Summary:  {fields.summary}\n"
        f"Status:   {fields.status.name}\n"
        f"Assignee: {fields.assignee.displayName if fields.assignee else 'unassigned'}\n"
        f"Priority: {fields.priority.name if fields.priority else 'none'}"
    )


def create_jira_ticket_impl(
    project: str, summary: str, description: str, priority: str = "High"
) -> str:
    try:
        issue = get_jira_client().create_issue(
            project=project,
            summary=summary,
            description=description,
            issuetype={"name": "Task"},
            priority={"name": priority},
        )
    except RuntimeError as e:
        return str(e)
    except JIRAError as e:
        return f"Jira rejected the request: {e.status_code} {e.text}"

    return f"Created {issue.key}: '{summary}' [{priority}] in project {project}"


def add_jira_comment_impl(ticket_id: str, comment: str) -> str:
    try:
        get_jira_client().add_comment(ticket_id, comment)
    except RuntimeError as e:
        return str(e)
    except JIRAError as e:
        if e.status_code == 404:
            return f"Ticket {ticket_id} not found."
        return f"Jira rejected the request: {e.status_code} {e.text}"

    preview = comment[:80] + ("..." if len(comment) > 80 else "")
    return f"Added comment to {ticket_id}: '{preview}'"


def post_slack_message_impl(channel: str, message: str) -> str:
    try:
        client = get_slack_client()
        resp = client.chat_postMessage(channel=channel, text=message)
    except RuntimeError as e:
        return str(e)
    except SlackApiError as e:
        return f"Slack rejected the post: {e.response['error']}"

    return f"Posted to #{channel.lstrip('#')} (ts={resp['ts']})"


def _load_dedupe() -> dict:
    if DEDUPE_PATH.exists():
        try:
            return json.loads(DEDUPE_PATH.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_dedupe(data: dict) -> None:
    DEDUPE_PATH.write_text(json.dumps(data))


def post_incident_alert_impl(service: str, severity: str, message: str) -> str:
    # ALERT DEDUPE: a flapping pod in a retry loop makes the agent call
    # this every few seconds. Without suppression the channel gets 40
    # identical pages a minute and humans mute it — a muted alert
    # channel is a dead alert channel. Suppression is itself logged via
    # the normal execute_tool -> log_tool_call path, since this return
    # value flows through it like any other result.
    key = f"{service}:{severity}"
    now = time.time()

    dedupe = _load_dedupe()
    last = dedupe.get(key)
    if last is not None and (now - last) < DEDUPE_WINDOW_SECONDS:
        return f"suppressed duplicate (posted {int(now - last)}s ago)"

    try:
        client = get_slack_client()
        text = f":rotating_light: {severity.upper()} | {service} | {message}"
        client.chat_postMessage(channel=INCIDENTS_CHANNEL, text=text)
    except RuntimeError as e:
        return str(e)
    except SlackApiError as e:
        return f"Slack rejected the incident alert: {e.response['error']}"

    # only record on a successful post — a failed attempt must not block
    # a legitimate retry from going out.
    dedupe[key] = now
    _save_dedupe(dedupe)

    return f"Incident alert fired — {severity.upper()} | {service} | {message[:80]}"

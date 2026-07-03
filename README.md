# devops-demo MCP server

An MCP server that gives Claude eyes and hands inside a production
environment — GitHub, Kubernetes, logs, Jira, and Slack — for
incident triage, with a safety layer that decides how much of that
Claude is allowed to use unsupervised.

## Tools

| Tool | Tier | Module |
|---|---|---|
| `get_system_status`, `list_pods`, `get_pod_logs`, `get_deployment_status`, `get_recent_commits`, `get_pr_status`, `get_workflow_run`, `search_logs`, `get_error_rate`, `get_ticket_status` | READ | `tools/k8s_tools.py`, `tools/github_tools.py`, `tools/logs_tools.py`, `tools/jira_slack_tools.py` |
| `create_jira_ticket`, `add_jira_comment`, `post_slack_message`, `post_incident_alert` | WRITE | `tools/jira_slack_tools.py` |
| `rollback_deployment`, `restart_pod`, `scale_deployment`, `delete_pod` | EXEC | `tools/k8s_tools.py` |

## Safety model

Every tool is assigned one of three tiers by blast radius, not by
whether it happens to mutate something: **READ** tools only observe
(commits, pod status, logs, ticket state) and run immediately.
**WRITE** tools change external systems — a Slack message, a Jira
ticket — but the damage is low and reversible: a wrong ticket gets
closed, a wrong message gets a follow-up. They also run immediately,
fully audit-logged. **EXEC** tools touch running production
infrastructure — a rollback, a forced pod deletion, a scale change —
where a mistake affects live traffic and isn't a quick undo. Tiering
by failure cost rather than by verb ("mutating" vs "read-only") is
the whole point: `post_incident_alert` and `rollback_deployment` are
both mutations, but only one of them can take down a service.

Every tool call, regardless of tier, is routed through a single
chokepoint (`tools/base.py::execute_tool`) rather than checked
ad hoc inside each tool. `execute_tool` calls `check_permission`,
which looks the tool up in `TOOL_REGISTRY`
(`execution/permission_engine.py`) and fails closed — any tool name
not explicitly registered as READ or WRITE defaults to EXEC and gets
blocked. Every call, blocked or not, is written to `audit.jsonl`
before the function returns, so the audit trail can never be
incomplete just because a wrapper "looked harmless enough" to skip
the check.

When `check_permission` blocks an EXEC call, `execute_tool` queues it
in `approval_queue.json` and hands Claude back a request ID and the
exact commands to approve or deny it — Claude cannot self-approve,
inspect the queue for a bypass, or retry around the block. A human
runs `python approve.py <id>` (or `--deny <id>`), which flips the
queue entry to `approved`, looks up the real implementation in
`execution/dispatch.py::DISPATCH`, executes it, and writes a second
audit entry with `approved_by` set to the approving human's name —
so `audit.jsonl` ends up containing both the blocked submission and
the approved execution, a complete paper trail from request to
human sign-off to action.

## Setup

```
pip install -r requirements.txt
cp .env.example .env   # fill in real tokens
python server.py
```

To act on a blocked EXEC request:

```
python approve.py --list
python approve.py <request_id>            # approve + execute
python approve.py --deny <request_id>
```

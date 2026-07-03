import os

from github import Github, GithubException

_client = None

MAX_COMMITS = 20


def get_client():
    global _client

    if not _client:
        _client = Github(os.environ["GITHUB_TOKEN"])

    return _client


def get_recent_commits_impl(
    repo: str,
    branch: str = "main",
    n: int = 5
) -> str:
    n = max(1, min(n, MAX_COMMITS))

    repo = get_client().get_repo(repo)

    commits = list(
        repo.get_commits(sha=branch)
    )[:n]

    lines = []

    for c in commits:
        lines.append(
            f"- {c.sha[:7]} | "
            f"{c.commit.author.date} | "
            f"{c.commit.author.name} | "
            f"{c.commit.message.splitlines()[0]}"
        )

    return "\n".join(lines) or "No commits found."


def get_pr_status_impl(
    repo: str,
    pr_number: int
) -> str:
    repo_name = repo
    try:
        repo = get_client().get_repo(repo)
        pr = repo.get_pull(pr_number)
    except GithubException as e:
        if e.status == 404:
            return f"PR #{pr_number} not found in {repo_name}."
        return f"GitHub API error: {e.status} {e.data.get('message', str(e))}"

    pr_commits = list(pr.get_commits())
    if pr_commits:
        checks = pr_commits[-1].get_check_runs()
        check_summary = ", ".join(
            f"{c.name}: {c.conclusion}" for c in checks
        ) or "no checks"
    else:
        check_summary = "no checks"

    if pr.mergeable is None:
        mergeable = "unknown (GitHub is still computing mergeability)"
    else:
        mergeable = pr.mergeable

    return (
        f"PR #{pr_number}: {pr.title}\n"
        f"Status: {pr.state}\n"
        f"Checks: {check_summary}\n"
        f"Mergeable: {mergeable}"
    )


def get_workflow_run_impl(repo: str, run_id: int) -> str:
    try:
        workflow_run = get_client().get_repo(repo).get_workflow_run(run_id)
    except GithubException as e:
        if e.status == 404:
            return f"Workflow run #{run_id} not found in {repo}."
        return f"GitHub API error: {e.status} {e.data.get('message', str(e))}"

    return (
        f"Run #{run_id}: {workflow_run.name}\n"
        f"Status:     {workflow_run.status}\n"
        f"Conclusion: {workflow_run.conclusion}\n"
        f"Branch:     {workflow_run.head_branch}\n"
        f"Commit:     {workflow_run.head_sha[:7]}\n"
        f"Started:    {workflow_run.run_started_at}"
    )

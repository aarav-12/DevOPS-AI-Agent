import os
from github import Github
# from tools.base import execute_tool

_client = None


def get_client():
    global _client

    if not _client:
        _client = Github(os.environ["GITHUB_TOKEN"])

    return _client


def get_recent_commits_impl(
    repo_name: str,
    branch: str = "main",
    n: int = 5
) -> str:

    repo = get_client().get_repo(repo_name)

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

    return "\n".join(lines)


def get_pr_status_impl(
    repo_name: str,
    pr_number: int
) -> str:

    repo = get_client().get_repo(repo_name)

    pr = repo.get_pull(pr_number)

    checks = list(
        pr.get_commits()
    )[-1].get_check_runs()

    check_summary = ", ".join(
        [
            f"{c.name}: {c.conclusion}"
            for c in checks
        ]
    ) or "no checks"

    return (
        f"PR #{pr_number}: {pr.title}\n"
        f"Status: {pr.state}\n"
        f"Checks: {check_summary}\n"
        f"Mergeable: {pr.mergeable}"
    )
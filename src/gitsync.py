"""Best-effort git synchronisation for vault repos.

A vault lives inside a git working tree (the whole `vaults/` mono-repo is one
GitHub repo, `brain-vaults`). These helpers let the server keep that repo in
step with GitHub so edits made on fly.io and edits made locally in Obsidian
converge:

  * `pull(vault)`  — run before a compile, so we build on the latest content.
  * `commit_and_push(vault, message)` — run after a write/compile, so changes
    land on GitHub and reach every other clone.

Everything is best-effort: if git is missing, there is no remote, or the repo
is offline, these functions return quietly and never crash a tool call.
Authentication is expected to be baked into the remote (an SSH key locally, or
a tokenised HTTPS remote on fly — see docker-entrypoint.sh), so this module
stays credential-agnostic.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.vaults import Vault

_TIMEOUT = 60  # seconds — a hung network call must not block a tool forever


def _run(args: list[str], cwd: str | Path) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            args, cwd=str(cwd), capture_output=True, text=True, timeout=_TIMEOUT
        )
    except Exception:
        return None


def _repo_root(path: Path) -> str | None:
    """Return the git toplevel containing `path`, or None if not a repo."""
    res = _run(["git", "rev-parse", "--show-toplevel"], path)
    if res is None or res.returncode != 0:
        return None
    return res.stdout.strip() or None


def _has_remote(repo: str) -> bool:
    res = _run(["git", "remote"], repo)
    return bool(res and res.returncode == 0 and res.stdout.strip())


def pull(vault: Vault) -> None:
    """Pull the latest content for this vault's repo. Best-effort, no-op on failure."""
    repo = _repo_root(vault.path)
    if not repo or not _has_remote(repo):
        return
    # --autostash keeps any uncommitted local edits; --rebase keeps history linear.
    _run(["git", "pull", "--rebase", "--autostash"], repo)


def commit_and_push(vault: Vault, message: str) -> str | None:
    """Stage everything, commit if there are changes, and push. Returns short hash or None."""
    repo = _repo_root(vault.path)
    if not repo:
        return None

    add = _run(["git", "add", "-A"], repo)
    if add is None or add.returncode != 0:
        return None

    # Nothing staged → nothing to do.
    staged = _run(["git", "diff", "--cached", "--quiet"], repo)
    if staged is not None and staged.returncode == 0:
        return None

    commit = _run(["git", "commit", "-m", message], repo)
    if commit is None or commit.returncode != 0:
        return None

    short_hash = None
    rev = _run(["git", "rev-parse", "--short", "HEAD"], repo)
    if rev and rev.returncode == 0:
        short_hash = rev.stdout.strip()

    # Push is best-effort: an offline box still keeps the local commit.
    if _has_remote(repo):
        _run(["git", "push"], repo)

    return short_hash or "committed"

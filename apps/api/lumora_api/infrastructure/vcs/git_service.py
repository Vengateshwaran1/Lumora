"""Wraps GitPython for the subset of operations repository ingestion needs:
clone, shallow incremental update, and tracked-file enumeration.

Clones are shallow (`depth=1`) — Milestone 1's incremental-indexing
correctness is driven by per-file content hashing (see
`application.indexing.index_repository`), not `git diff <sha>..HEAD`, so
full history is never needed and shallow clones are strictly better (less
disk, faster clone/fetch). See docs/architecture/ARCHITECTURE.md §6 for the
git-diff-based approach this deliberately simplifies for M1.
"""

import os
import shutil
import stat
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from git import Repo


def _clear_readonly_and_retry(func: Callable[[str], object], path: str, exc: BaseException) -> None:
    """`shutil.rmtree` error handler: Git marks pack files read-only on
    Windows, which makes plain deletion fail — clear the flag and retry."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


@dataclass(frozen=True)
class CloneResult:
    local_path: Path
    commit_sha: str
    default_branch: str


class GitService:
    def __init__(self, storage_root: Path) -> None:
        self._storage_root = storage_root

    def repo_path(self, repository_id: uuid.UUID) -> Path:
        return self._storage_root / str(repository_id)

    def clone_or_update(self, repository_id: uuid.UUID, url: str) -> CloneResult:
        path = self.repo_path(repository_id)

        if path.exists():
            repo = Repo(str(path))
            try:
                default_branch = repo.active_branch.name
                repo.git.fetch("origin", default_branch, depth=1)
                repo.git.reset("--hard", f"origin/{default_branch}")
                commit_sha = repo.head.commit.hexsha
            finally:
                repo.close()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            repo = Repo.clone_from(url, str(path), depth=1)
            try:
                default_branch = repo.active_branch.name
                commit_sha = repo.head.commit.hexsha
            finally:
                repo.close()

        return CloneResult(local_path=path, commit_sha=commit_sha, default_branch=default_branch)

    def list_tracked_files(self, local_path: Path) -> list[str]:
        """Files git considers tracked at HEAD — excludes `.git` and
        anything matched by `.gitignore` without needing to reimplement
        gitignore matching ourselves."""
        repo = Repo(str(local_path))
        try:
            output: str = repo.git.ls_files()
        finally:
            repo.close()
        return [line for line in output.splitlines() if line]

    def resolve_path(self, local_path: Path, relative_path: str) -> Path:
        return local_path / relative_path

    def delete_clone(self, repository_id: uuid.UUID) -> None:
        path = self.repo_path(repository_id)
        if path.exists():
            shutil.rmtree(path, onexc=_clear_readonly_and_retry)

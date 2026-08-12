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

from git import GitCommandError, Repo

from lumora_api.domain.git_diff import DiffEntry, parse_name_status


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
            # core.autocrlf=false: Lumora only ever reads these clones, so
            # there's no reason to want OS-native line endings on checkout
            # — and a big one to avoid it. Without this, on a machine with
            # autocrlf enabled, a working-tree read (full index, this repo)
            # and a `git show <sha>:<path>` read (incremental index, which
            # never applies checkout filters) hash the *same* committed
            # content differently, breaking "unchanged content is never
            # re-embedded" the moment a push touches an otherwise-untouched
            # file. Set once at clone time; it's a repo-local git config
            # value that persists for the lifetime of this clone.
            repo = Repo.clone_from(
                url,
                str(path),
                depth=1,
                multi_options=["-c", "core.autocrlf=false"],
                # `-c` is flagged unsafe by GitPython because arbitrary
                # git options can be a command-injection vector — not a
                # risk here, this literal option list is developer-
                # authored, not derived from `url` or any other input.
                allow_unsafe_options=True,
            )
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

    def has_clone(self, repository_id: uuid.UUID) -> bool:
        return self.repo_path(repository_id).exists()

    def fetch_commit(self, repository_id: uuid.UUID, url: str, commit_sha: str) -> Path:
        """Fetch a single commit object (tree + blobs, no working-tree
        checkout) into the repo's existing clone — creating the clone
        first if it doesn't exist yet. GitHub.com and GitHub Enterprise
        both allow fetching an arbitrary reachable commit SHA this way
        (`uploadpack.allowReachableSHA1InWant`, on by default), which is
        what lets incremental indexing pull just the two commits a push
        diff needs instead of walking full branch history."""
        path = self.repo_path(repository_id)
        if not path.exists():
            self.clone_or_update(repository_id, url)
        repo = Repo(str(path))
        try:
            repo.git.fetch("origin", commit_sha, depth=1)
        finally:
            repo.close()
        return path

    def diff_name_status(
        self, local_path: Path, before_sha: str, after_sha: str
    ) -> list[DiffEntry]:
        """`git diff --name-status -M` between two commits already present
        in the local object store (via `fetch_commit`) — `-M` is what makes
        Git report a delete+add pair as a single rename instead of two
        unrelated entries."""
        repo = Repo(str(local_path))
        try:
            output: str = repo.git.diff("--name-status", "-M", before_sha, after_sha)
        finally:
            repo.close()
        return parse_name_status(output)

    def search_commit_log(
        self, local_path: Path, term: str, max_results: int = 5
    ) -> list[tuple[str, str]]:
        """`git log --grep` over the local clone's history — read-only,
        no network call, no GitHub API token needed (Milestone 3 §11's
        "relevant historical context" node uses this for commit-message
        search alongside `Issue` table search; there's no PR data synced
        in this milestone). Returns `(short_sha, subject)` pairs, most
        recent first. Empty on any git error (e.g. a shallow clone whose
        single commit doesn't match) rather than raising — history search
        is best-effort context, not a required step."""
        try:
            repo = Repo(str(local_path))
        except Exception:
            return []
        try:
            output: str = repo.git.log(
                f"--grep={term}", "-i", "--oneline", f"-n{max_results}", "--format=%h %s"
            )
        except GitCommandError:
            return []
        finally:
            repo.close()

        results = []
        for line in output.splitlines():
            if not line.strip():
                continue
            sha, _, subject = line.partition(" ")
            results.append((sha, subject))
        return results

    def read_blob(self, local_path: Path, commit_sha: str, relative_path: str) -> bytes | None:
        """Read a file's content at a specific commit directly from the
        git object store — no working-tree checkout needed. Returns None
        if the path doesn't exist at that commit (shouldn't happen for a
        path the diff just reported as added/modified, but a defensive
        check beats an opaque `GitCommandError` bubbling up)."""
        repo = Repo(str(local_path))
        try:
            # GitPython strips a trailing newline from captured stdout by
            # default (`strip_newline_in_stdout=True`) — harmless for its
            # usual text-output use cases, but silently corrupts blob
            # content here: a file that ends in `\n` (as almost all source
            # files do) comes back one byte short, hashing differently
            # from the same content read off the working tree and
            # defeating "unchanged content is never re-embedded" for
            # exactly the files most likely to be untouched by a push.
            # The installed type stub doesn't know this kwarg exists.
            result = repo.git.execute(  # type: ignore[call-overload]
                ["git", "show", f"{commit_sha}:{relative_path}"],
                stdout_as_string=False,
                strip_newline_in_stdout=False,
            )
            return result if isinstance(result, bytes) else None
        except GitCommandError:
            return None
        finally:
            repo.close()

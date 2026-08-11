"""No network access — clones from a local git repo fixture (a `file://`-
style local path is exactly what `git clone` uses for a remote in every
other case too; this is not a mock, it's the real GitPython clone path)."""

import uuid

from lumora_api.domain.git_diff import DiffStatus
from lumora_api.infrastructure.vcs.git_service import GitService


def test_clone_or_update_clones_and_returns_commit_info(git_service: GitService, sample_repo_path):
    repository_id = uuid.uuid4()
    result = git_service.clone_or_update(repository_id, sample_repo_path)

    assert result.local_path.exists()
    assert result.default_branch == "main"
    assert len(result.commit_sha) == 40


def test_list_tracked_files_excludes_gitignored_paths(git_service: GitService, sample_repo_path):
    repository_id = uuid.uuid4()
    result = git_service.clone_or_update(repository_id, sample_repo_path)

    tracked = git_service.list_tracked_files(result.local_path)

    assert "app.py" in tracked
    assert "greeter.ts" in tracked
    assert "README.md" in tracked
    assert not any(path.startswith("build/") for path in tracked)


def test_clone_or_update_is_idempotent_on_existing_clone(git_service: GitService, sample_repo_path):
    repository_id = uuid.uuid4()
    first = git_service.clone_or_update(repository_id, sample_repo_path)
    second = git_service.clone_or_update(repository_id, sample_repo_path)

    assert first.local_path == second.local_path
    assert first.commit_sha == second.commit_sha


def test_resolve_path_joins_local_path_and_relative_path(git_service: GitService, tmp_path):
    local_path = tmp_path / "repo"
    resolved = git_service.resolve_path(local_path, "src/app.py")
    assert resolved == local_path / "src" / "app.py"


def test_delete_clone_removes_the_directory(git_service: GitService, sample_repo_path):
    repository_id = uuid.uuid4()
    result = git_service.clone_or_update(repository_id, sample_repo_path)
    assert result.local_path.exists()

    git_service.delete_clone(repository_id)

    assert not result.local_path.exists()


def test_has_clone_reflects_clone_state(git_service: GitService, sample_repo_path):
    repository_id = uuid.uuid4()
    assert git_service.has_clone(repository_id) is False

    git_service.clone_or_update(repository_id, sample_repo_path)
    assert git_service.has_clone(repository_id) is True


def test_fetch_commit_creates_clone_if_missing(git_service: GitService, sample_repo_with_history):
    repository_id = uuid.uuid4()
    path = git_service.fetch_commit(
        repository_id, sample_repo_with_history.path, sample_repo_with_history.commit_a
    )
    assert path.exists()
    assert git_service.has_clone(repository_id)


def test_diff_name_status_reports_all_change_kinds(
    git_service: GitService, sample_repo_with_history
):
    repository_id = uuid.uuid4()
    commit_a = sample_repo_with_history.commit_a
    git_service.fetch_commit(repository_id, sample_repo_with_history.path, commit_a)
    commit_b = sample_repo_with_history.push_commit_b()
    local_path = git_service.fetch_commit(repository_id, sample_repo_with_history.path, commit_b)

    entries = git_service.diff_name_status(local_path, commit_a, commit_b)
    by_status = {e.status: e for e in entries}

    assert by_status[DiffStatus.MODIFIED].path == "app.py"
    assert by_status[DiffStatus.ADDED].path == "new_file.py"
    assert by_status[DiffStatus.DELETED].path == "doomed.py"
    assert by_status[DiffStatus.RENAMED].path == "renamed_greeter.ts"
    assert by_status[DiffStatus.RENAMED].old_path == "greeter.ts"


def test_read_blob_returns_content_at_commit(git_service: GitService, sample_repo_with_history):
    repository_id = uuid.uuid4()
    commit_b = sample_repo_with_history.push_commit_b()
    local_path = git_service.fetch_commit(repository_id, sample_repo_with_history.path, commit_b)

    content = git_service.read_blob(local_path, commit_b, "app.py")

    assert content is not None
    assert b"def mul" in content


def test_read_blob_returns_none_for_missing_path(git_service: GitService, sample_repo_with_history):
    repository_id = uuid.uuid4()
    commit_b = sample_repo_with_history.push_commit_b()
    local_path = git_service.fetch_commit(repository_id, sample_repo_with_history.path, commit_b)

    content = git_service.read_blob(local_path, commit_b, "no_such_file.py")

    assert content is None

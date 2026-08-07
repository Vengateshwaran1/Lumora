"""No network access — clones from a local git repo fixture (a `file://`-
style local path is exactly what `git clone` uses for a remote in every
other case too; this is not a mock, it's the real GitPython clone path)."""

import uuid

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

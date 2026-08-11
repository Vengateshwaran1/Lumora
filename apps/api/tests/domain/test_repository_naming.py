from lumora_api.domain.repository_naming import derive_full_name, derive_repository_name


def test_derive_repository_name_strips_git_suffix():
    assert derive_repository_name("https://github.com/octocat/Hello-World.git") == "Hello-World"


def test_derive_full_name_from_https_url():
    assert derive_full_name("https://github.com/octocat/Hello-World.git") == "octocat/Hello-World"


def test_derive_full_name_from_https_url_without_git_suffix():
    assert derive_full_name("https://github.com/octocat/Hello-World") == "octocat/Hello-World"


def test_derive_full_name_from_ssh_url():
    assert derive_full_name("git@github.com:octocat/Hello-World.git") == "octocat/Hello-World"


def test_derive_full_name_none_for_non_github_url():
    assert derive_full_name("https://gitlab.com/octocat/Hello-World.git") is None


def test_derive_full_name_none_for_local_path():
    assert derive_full_name("/tmp/some/local/repo") is None

from lumora_api.domain.file_filter import is_safe_relative_path, looks_binary


def test_ordinary_relative_path_is_safe():
    assert is_safe_relative_path("src/app.py") is True


def test_parent_traversal_rejected():
    assert is_safe_relative_path("../../etc/passwd") is False


def test_absolute_path_rejected():
    assert is_safe_relative_path("/etc/passwd") is False


def test_home_relative_path_rejected():
    assert is_safe_relative_path("~/secrets.py") is False


def test_empty_path_rejected():
    assert is_safe_relative_path("") is False


def test_double_slash_rejected():
    assert is_safe_relative_path("src//app.py") is False


def test_looks_binary_detects_nul_byte():
    assert looks_binary(b"hello\x00world") is True


def test_looks_binary_false_for_text():
    assert looks_binary(b"hello world\n") is False

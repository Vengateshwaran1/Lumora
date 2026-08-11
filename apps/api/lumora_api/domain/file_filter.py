"""Heuristics for deciding whether a tracked file should be parsed/indexed.

`git ls-files` already excludes `.git` and anything covered by `.gitignore`
(build output, `node_modules`, `__pycache__`, etc.) — that's why there's no
separate directory-exclusion list here. What's left to filter: files whose
extension isn't a supported language, oversized files, and binary files
that happen to have a text-like extension.
"""

_BINARY_SCAN_WINDOW = 8192


def looks_binary(sample: bytes) -> bool:
    """Heuristic: a NUL byte in the first few KB almost never appears in
    genuine source text but is common in binary formats — the same
    heuristic Git itself uses to classify files as binary."""
    return b"\x00" in sample[:_BINARY_SCAN_WINDOW]


def is_safe_relative_path(path: str) -> bool:
    """Reject a path before it's used to key Postgres rows, Qdrant
    payloads, or a filesystem join. Paths from `git ls-files` (full index)
    are already repo-relative and safe by construction; paths from a
    webhook-driven `git diff` (incremental index) originate outside our
    control, so this is the boundary check ARCHITECTURE.md §13 asks for
    before any path-derived operation."""
    if not path or path.startswith("/") or path.startswith("~"):
        return False
    parts = path.split("/")
    return ".." not in parts and "" not in parts

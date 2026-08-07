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

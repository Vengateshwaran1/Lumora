"""Language detection by file extension.

Deliberately simple — a fixed extension → language table, not content
sniffing (e.g. linguist-style byte/heuristic analysis). Sufficient for
Milestone 1's fixed supported-language set; revisit only if a language
without a reliable 1:1 extension mapping needs support.
"""

from pathlib import PurePosixPath

_EXTENSION_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".md": "markdown",
    ".markdown": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
}

SUPPORTED_LANGUAGES: frozenset[str] = frozenset(_EXTENSION_LANGUAGE.values())


def detect_language(path: str) -> str | None:
    """Return the detected language for a repo-relative file path, or None."""
    suffix = PurePosixPath(path).suffix.lower()
    return _EXTENSION_LANGUAGE.get(suffix)

"""Derives a human-readable repository name from its clone URL, so callers
don't have to supply one — POST /repositories only needs a URL."""

import re


def derive_repository_name(url: str) -> str:
    cleaned = url.rstrip("/")
    cleaned = re.sub(r"\.git$", "", cleaned)
    return cleaned.rsplit("/", 1)[-1] or cleaned

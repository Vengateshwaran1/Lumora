"""Derives a human-readable repository name (and, where possible, a GitHub
`owner/repo` full name) from a clone URL, so callers don't have to supply
either — POST /repositories only needs a URL."""

import re

# Matches the owner/repo segment out of the GitHub URL forms GitHub itself
# uses: https://github.com/owner/repo(.git), git@github.com:owner/repo.git,
# ssh://git@github.com/owner/repo(.git). Anything else (a local path used
# in tests, a non-GitHub host) yields no full_name — that's fine, it just
# means webhook delivery lookup falls back to `github_repo_id` once a
# webhook has been received for the repo at least once.
_GITHUB_FULL_NAME_RE = re.compile(r"github\.com[:/]+(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$")


def derive_repository_name(url: str) -> str:
    cleaned = url.rstrip("/")
    cleaned = re.sub(r"\.git$", "", cleaned)
    return cleaned.rsplit("/", 1)[-1] or cleaned


def derive_full_name(url: str) -> str | None:
    match = _GITHUB_FULL_NAME_RE.search(url)
    if match is None:
        return None
    return f"{match.group('owner')}/{match.group('repo')}"

"""Pydantic models for the subset of a GitHub `push` webhook payload
Milestone 2 needs — deliberately not the full GitHub payload shape (dozens
of fields we don't use); `extra = "ignore"` (Pydantic's default) means
unmodeled fields are simply dropped, not rejected.
"""

from pydantic import BaseModel


class GitHubPushRepository(BaseModel):
    id: int
    full_name: str
    default_branch: str | None = None


class GitHubPushSender(BaseModel):
    login: str | None = None


class GitHubPushPayload(BaseModel):
    ref: str
    before: str
    after: str
    deleted: bool = False
    repository: GitHubPushRepository
    sender: GitHubPushSender | None = None

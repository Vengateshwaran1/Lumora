"""Parses `git diff --name-status -M` output into structured entries —
pure, no I/O, so it's unit-testable without a real git repository.

Status letters (see `git-diff(1)`): `A` added, `M` modified, `D` deleted,
`R###` renamed with a similarity percentage (`-M` is what makes Git detect
these instead of reporting a delete + add pair), `C###` copied (not
requested by this milestone — copies are treated as adds, see
`DiffStatus.COPIED` handling in the caller).
"""

from dataclasses import dataclass
from enum import StrEnum


class DiffStatus(StrEnum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    COPIED = "copied"


@dataclass(frozen=True)
class DiffEntry:
    status: DiffStatus
    path: str
    # Only set for renames/copies — the path this entry's content came from.
    old_path: str | None = None


def parse_name_status(output: str) -> list[DiffEntry]:
    entries: list[DiffEntry] = []
    for line in output.splitlines():
        if not line:
            continue
        fields = line.split("\t")
        code, rest = fields[0], fields[1:]
        if code.startswith("R"):
            old_path, new_path = rest
            entries.append(DiffEntry(status=DiffStatus.RENAMED, path=new_path, old_path=old_path))
        elif code.startswith("C"):
            old_path, new_path = rest
            entries.append(DiffEntry(status=DiffStatus.COPIED, path=new_path, old_path=old_path))
        elif code == "A":
            entries.append(DiffEntry(status=DiffStatus.ADDED, path=rest[0]))
        elif code == "M":
            entries.append(DiffEntry(status=DiffStatus.MODIFIED, path=rest[0]))
        elif code == "D":
            entries.append(DiffEntry(status=DiffStatus.DELETED, path=rest[0]))
        # Other codes (T type-change, U unmerged) don't apply to a
        # push-diff between two ordinary commits — ignored rather than
        # raising, so an unexpected code doesn't fail the whole job.
    return entries

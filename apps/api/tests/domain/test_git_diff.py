from lumora_api.domain.git_diff import DiffEntry, DiffStatus, parse_name_status


def test_parses_added_modified_deleted():
    output = "A\tnew.py\nM\tchanged.py\nD\tremoved.py"
    entries = parse_name_status(output)
    assert entries == [
        _entry(DiffStatus.ADDED, "new.py"),
        _entry(DiffStatus.MODIFIED, "changed.py"),
        _entry(DiffStatus.DELETED, "removed.py"),
    ]


def test_parses_rename_with_old_and_new_path():
    entries = parse_name_status("R100\told/path.py\tnew/path.py")
    assert len(entries) == 1
    entry = entries[0]
    assert entry.status == DiffStatus.RENAMED
    assert entry.old_path == "old/path.py"
    assert entry.path == "new/path.py"


def test_parses_copy():
    entries = parse_name_status("C075\tsource.py\tcopy.py")
    assert entries[0].status == DiffStatus.COPIED
    assert entries[0].old_path == "source.py"
    assert entries[0].path == "copy.py"


def test_empty_output_yields_no_entries():
    assert parse_name_status("") == []


def test_blank_lines_ignored():
    entries = parse_name_status("A\ta.py\n\nA\tb.py\n")
    assert [e.path for e in entries] == ["a.py", "b.py"]


def _entry(status: DiffStatus, path: str) -> DiffEntry:
    return DiffEntry(status=status, path=path)

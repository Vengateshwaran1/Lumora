"""Pure-logic tests for agents.planning.graph._validate — no LLM, no
retrieval, just the citation/affected-file/step-ordering checks (§16)."""

from lumora_api.agents.planning.graph import _validate
from lumora_api.infrastructure.models import IndexedFile, Repository


async def _repo_with_file(db_session, path: str = "app.py") -> Repository:
    repository = Repository(url="https://example.invalid/validate.git", name="validate")
    db_session.add(repository)
    await db_session.commit()
    await db_session.refresh(repository)
    db_session.add(IndexedFile(repository_id=repository.id, path=path, content_hash="a" * 64))
    await db_session.commit()
    return repository


def _plan(**overrides) -> dict:
    base = {
        "citations": [],
        "affected_files": [],
        "implementation_steps": [],
    }
    base.update(overrides)
    return base


async def test_valid_plan_with_no_claims_has_no_errors(db_session):
    repository = await _repo_with_file(db_session)
    state = {"implementation_plan": _plan(), "retrieved_chunks": [], "related_symbols": []}

    errors = await _validate(db_session, repository.id, state)

    assert errors == []


async def test_citation_referencing_unretrieved_file_is_flagged(db_session):
    repository = await _repo_with_file(db_session)
    citation = {"file_path": "never_retrieved.py", "start_line": 1, "end_line": 2, "claim": "x"}
    state = {
        "implementation_plan": _plan(citations=[citation]),
        "retrieved_chunks": [{"file_path": "app.py"}],
        "related_symbols": [],
    }

    errors = await _validate(db_session, repository.id, state)

    assert any("never_retrieved.py" in e for e in errors)


async def test_citation_referencing_retrieved_file_is_not_flagged(db_session):
    repository = await _repo_with_file(db_session)
    state = {
        "implementation_plan": _plan(
            citations=[{"file_path": "app.py", "start_line": 1, "end_line": 2, "claim": "x"}]
        ),
        "retrieved_chunks": [{"file_path": "app.py"}],
        "related_symbols": [],
    }

    errors = await _validate(db_session, repository.id, state)

    assert errors == []


async def test_affected_file_not_in_repo_is_flagged(db_session):
    repository = await _repo_with_file(db_session)
    state = {
        "implementation_plan": _plan(affected_files=["does_not_exist.py"]),
        "retrieved_chunks": [],
        "related_symbols": [],
    }

    errors = await _validate(db_session, repository.id, state)

    assert any("does_not_exist.py" in e for e in errors)


async def test_step_depending_on_later_step_is_flagged(db_session):
    repository = await _repo_with_file(db_session)
    state = {
        "implementation_plan": _plan(
            implementation_steps=[
                {"step_number": 1, "depends_on_steps": [2]},
                {"step_number": 2, "depends_on_steps": []},
            ]
        ),
        "retrieved_chunks": [],
        "related_symbols": [],
    }

    errors = await _validate(db_session, repository.id, state)

    assert any("Step 1" in e for e in errors)


async def test_no_plan_at_all_is_flagged(db_session):
    repository = await _repo_with_file(db_session)
    errors = await _validate(
        db_session, repository.id, {"implementation_plan": None, "retrieved_chunks": []}
    )
    assert errors

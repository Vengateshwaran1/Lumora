import pytest
from pydantic import BaseModel

from lumora_api.agents.planning.schemas import ImplementationPlan, IssueAnalysis, SearchQueries
from lumora_api.infrastructure.llm.planning import PlanGenerationError
from lumora_api.infrastructure.llm.template_planning import TemplatePlanningProvider


class _NoOfflineDefaultSchema(BaseModel):
    value: str


async def test_offline_default_used_for_issue_analysis():
    provider = TemplatePlanningProvider()
    result = await provider.generate_structured(prompt="Add JWT auth", schema=IssueAnalysis)
    assert isinstance(result, IssueAnalysis)
    assert "Add JWT auth" in result.problem


async def test_offline_default_used_for_search_queries():
    provider = TemplatePlanningProvider()
    result = await provider.generate_structured(prompt="Add JWT auth", schema=SearchQueries)
    assert isinstance(result, SearchQueries)
    assert len(result.queries) >= 1


async def test_offline_default_plan_makes_no_unsupported_claims():
    provider = TemplatePlanningProvider()
    result = await provider.generate_structured(prompt="Add JWT auth", schema=ImplementationPlan)
    assert isinstance(result, ImplementationPlan)
    # Never fabricate — an offline template must not claim specific
    # affected files or citations it never retrieved.
    assert result.affected_files == []
    assert result.citations == []
    assert result.confidence < 0.5


async def test_schema_without_offline_default_raises():
    provider = TemplatePlanningProvider()
    with pytest.raises(PlanGenerationError):
        await provider.generate_structured(prompt="x", schema=_NoOfflineDefaultSchema)

import pytest

from lumora_api.infrastructure.embeddings.deterministic import DeterministicEmbeddingProvider


async def test_same_text_produces_same_vector():
    provider = DeterministicEmbeddingProvider(dimensions=16)
    [v1] = await provider.embed(["hello world"])
    [v2] = await provider.embed(["hello world"])
    assert v1 == v2


async def test_different_text_produces_different_vectors():
    provider = DeterministicEmbeddingProvider(dimensions=16)
    [v1, v2] = await provider.embed(["hello", "goodbye"])
    assert v1 != v2


async def test_vector_has_requested_dimensions():
    provider = DeterministicEmbeddingProvider(dimensions=32)
    [vector] = await provider.embed(["anything"])
    assert len(vector) == 32


async def test_vector_is_unit_normalized():
    provider = DeterministicEmbeddingProvider(dimensions=16)
    [vector] = await provider.embed(["anything"])
    norm = sum(v * v for v in vector) ** 0.5
    assert norm == pytest.approx(1.0)


async def test_empty_input_returns_empty_list():
    provider = DeterministicEmbeddingProvider(dimensions=16)
    assert await provider.embed([]) == []

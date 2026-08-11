from lumora_api.infrastructure.vector_store.qdrant_store import VectorPoint


async def test_set_payload_updates_fields_without_changing_vector(vector_store):
    await vector_store.ensure_collection(dimensions=4)
    point = VectorPoint(
        id="11111111-1111-1111-1111-111111111111",
        vector=[0.1, 0.2, 0.3, 0.4],
        payload={"file_path": "old/path.py", "repository_id": "repo-1"},
    )
    await vector_store.upsert([point])

    await vector_store.set_payload([point.id], {"file_path": "new/path.py"})

    hits = await vector_store.search(
        query_vector=[0.1, 0.2, 0.3, 0.4], repository_id="repo-1", limit=1
    )
    assert len(hits) == 1
    assert hits[0].payload["file_path"] == "new/path.py"
    assert hits[0].payload["repository_id"] == "repo-1"  # untouched fields survive


async def test_set_payload_on_empty_list_is_a_no_op(vector_store):
    await vector_store.ensure_collection(dimensions=4)
    await vector_store.set_payload([], {"file_path": "irrelevant"})  # must not raise

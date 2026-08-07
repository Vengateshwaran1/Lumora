from lumora_api.infrastructure.retrieval.fusion import reciprocal_rank_fusion


def test_item_ranked_first_in_both_lists_wins():
    dense = ["a", "b", "c"]
    bm25 = ["a", "c", "b"]
    fused = reciprocal_rank_fusion(dense, bm25)
    assert max(fused, key=lambda k: fused[k]) == "a"


def test_item_only_in_one_list_still_included():
    dense = ["a", "b"]
    bm25 = ["c"]
    fused = reciprocal_rank_fusion(dense, bm25)
    assert set(fused) == {"a", "b", "c"}


def test_empty_lists_yield_empty_fusion():
    assert reciprocal_rank_fusion([], []) == {}


def test_appearing_in_both_lists_scores_higher_than_appearing_in_one():
    dense = ["a", "b"]
    bm25 = ["b", "a"]
    fused = reciprocal_rank_fusion(dense, bm25)
    # "a" is rank 0 in dense + rank 1 in bm25; "b" is rank 1 in dense + rank 0 in bm25.
    # Both appear in both lists, so both should score higher than a single-list item.
    only_one = reciprocal_rank_fusion(["c"], [])
    assert fused["a"] > only_one["c"]
    assert fused["b"] > only_one["c"]

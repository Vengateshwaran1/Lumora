"""Reciprocal Rank Fusion — combines independently-ranked result lists into
one ranking without needing their scores to be on a comparable scale.
Dense cosine similarity and BM25 scores aren't directly comparable, which
rules out simply weighting and summing raw scores; RRF sidesteps that by
using each item's *rank position*, not its score.
"""

_RRF_K = 60  # standard constant from the original RRF paper; dampens the
# influence of any single very-high rank so no one list dominates.


def reciprocal_rank_fusion(*ranked_id_lists: list[str]) -> dict[str, float]:
    """Each argument is a list of chunk_ids in rank order (best first).
    Returns {chunk_id: fused_score}, higher is better."""
    fused: dict[str, float] = {}
    for ranked_ids in ranked_id_lists:
        for rank, chunk_id in enumerate(ranked_ids):
            fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (_RRF_K + rank + 1)
    return fused

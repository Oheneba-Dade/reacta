import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

from backend.services.search import _compute_final_scores


def _make_clip(clip_id: uuid.UUID) -> MagicMock:
    clip = MagicMock()
    clip.id = clip_id
    clip.created_at = datetime.now(timezone.utc)
    return clip


def _ids(n: int) -> list[uuid.UUID]:
    return [uuid.uuid4() for _ in range(n)]


def _run(desc_scores, trans_scores, lexical_data=None, tag_labels=None, search_terms="test"):
    all_ids = set(desc_scores) | set(trans_scores)
    clips_by_id = {cid: _make_clip(cid) for cid in all_ids}
    return _compute_final_scores(
        desc_scores=desc_scores,
        trans_scores=trans_scores,
        lexical_data=lexical_data or {},
        clips_by_id=clips_by_id,
        tag_labels=tag_labels or [],
        search_terms=search_terms,
    )


def test_description_only_sets_match_source():
    clip_id = uuid.uuid4()
    result = _run({clip_id: 0.9}, {})
    assert len(result) == 1
    assert result[0][0] == clip_id
    assert result[0][2] == "description"


def test_transcript_only_sets_match_source():
    clip_id = uuid.uuid4()
    result = _run({}, {clip_id: 0.8})
    assert len(result) == 1
    assert result[0][2] == "transcript"


def test_both_sets_match_source():
    clip_id = uuid.uuid4()
    result = _run({clip_id: 0.7}, {clip_id: 0.9})
    assert len(result) == 1
    assert result[0][2] == "both"


def test_results_sorted_by_score_descending():
    ids = _ids(3)
    desc = {ids[0]: 0.5, ids[1]: 0.9, ids[2]: 0.7}
    result = _run(desc, {})
    scores = [r[1] for r in result]
    assert scores == sorted(scores, reverse=True)


def test_capped_at_top_10():
    ids = _ids(15)
    desc = {i: float(idx) / 15 for idx, i in enumerate(ids)}
    result = _run(desc, {})
    assert len(result) == 10


def test_empty_inputs_return_empty():
    assert _run({}, {}) == []


def test_deduplication_across_signals():
    clip_id = uuid.uuid4()
    other_id = uuid.uuid4()
    result = _run({clip_id: 0.8, other_id: 0.6}, {clip_id: 0.9})
    clip_ids = [r[0] for r in result]
    assert clip_ids.count(clip_id) == 1
    assert len(result) == 2


def test_lexical_score_boosts_ranking():
    id_a = uuid.uuid4()
    id_b = uuid.uuid4()
    # id_a has lower vector score but gets exact match bonus
    desc = {id_a: 0.5, id_b: 0.7}
    lexical = {id_a: {"lexical_score": 1.0, "has_exact_match": True}}
    result = _run(desc, {}, lexical_data=lexical)
    # id_a should outrank id_b due to exact match + lexical contribution
    assert result[0][0] == id_a


def test_exact_match_bonus_applied():
    clip_id = uuid.uuid4()
    lexical = {clip_id: {"lexical_score": 0.0, "has_exact_match": True}}
    result_with = _run({clip_id: 0.5}, {}, lexical_data=lexical)
    result_without = _run({clip_id: 0.5}, {})
    assert result_with[0][1] > result_without[0][1]


def test_tag_boost_increases_score():
    clip_id = uuid.uuid4()
    result_with = _run({clip_id: 0.5}, {}, tag_labels=["shock"], search_terms="shock")
    result_without = _run({clip_id: 0.5}, {}, tag_labels=["shock"], search_terms="unrelated")
    assert result_with[0][1] > result_without[0][1]

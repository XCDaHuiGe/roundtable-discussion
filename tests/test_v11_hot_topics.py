from engine.v11_hot_topics import HotTopicCandidate, rank_candidates, select_training_topics


def test_rank_candidates_prefers_high_controversy_and_filters_gossip():
    candidates = [
        HotTopicCandidate(
            title="某明星机场穿搭争议",
            summary="纯娱乐争议",
            sources=["微博"],
            heat=9,
            position_split=2,
            value_conflict=1,
            practical_relevance=1,
            expert_decomposability=1,
            non_gossip_signal=0,
        ),
        HotTopicCandidate(
            title="AI 情感陪伴是否会替代真实亲密关系",
            summary="涉及技术、两性、心理与商业化。",
            sources=["Bing", "知乎", "小红书"],
            heat=7,
            position_split=8,
            value_conflict=9,
            practical_relevance=8,
            expert_decomposability=9,
            non_gossip_signal=9,
        ),
    ]

    ranked = rank_candidates(candidates)
    assert ranked[0].title.startswith("AI 情感陪伴")
    assert ranked[0].score > ranked[1].score


def test_select_training_topics_returns_top_10_and_top_3():
    candidates = [
        HotTopicCandidate(
            title=f"议题{i}",
            summary="可讨论议题",
            sources=["Bing", "知乎"],
            heat=i,
            position_split=i,
            value_conflict=i,
            practical_relevance=i,
            expert_decomposability=i,
            non_gossip_signal=9,
        )
        for i in range(1, 31)
    ]

    top10, top3 = select_training_topics(candidates)
    assert len(top10) == 10
    assert len(top3) == 3
    assert [t.title for t in top3] == ["议题30", "议题29", "议题28"]

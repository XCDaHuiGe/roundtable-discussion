# -*- coding: utf-8 -*-
"""V11 热点候选评分与选择。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HotTopicCandidate:
    title: str
    summary: str
    sources: list[str]
    heat: int
    position_split: int
    value_conflict: int
    practical_relevance: int
    expert_decomposability: int
    non_gossip_signal: int
    score: float = field(default=0.0)


def _clamp_score(value: int) -> int:
    return max(0, min(10, int(value)))


def score_candidate(candidate: HotTopicCandidate) -> float:
    """争议价值评分，非八卦信号是硬门槛之一。"""
    heat = _clamp_score(candidate.heat)
    split = _clamp_score(candidate.position_split)
    conflict = _clamp_score(candidate.value_conflict)
    relevance = _clamp_score(candidate.practical_relevance)
    decomposable = _clamp_score(candidate.expert_decomposability)
    non_gossip = _clamp_score(candidate.non_gossip_signal)
    source_bonus = min(len(set(candidate.sources)), 4) * 0.5

    weighted = (
        heat * 0.12
        + split * 0.22
        + conflict * 0.22
        + relevance * 0.18
        + decomposable * 0.18
        + non_gossip * 0.08
        + source_bonus
    )
    if non_gossip < 3:
        weighted *= 0.35
    if split < 4 or conflict < 4:
        weighted *= 0.65
    return round(weighted, 2)


def rank_candidates(candidates: list[HotTopicCandidate]) -> list[HotTopicCandidate]:
    ranked = []
    for candidate in candidates:
        candidate.score = score_candidate(candidate)
        ranked.append(candidate)
    return sorted(ranked, key=lambda item: (item.score, _raw_total(item)), reverse=True)


def _raw_total(candidate: HotTopicCandidate) -> int:
    return (
        candidate.heat
        + candidate.position_split
        + candidate.value_conflict
        + candidate.practical_relevance
        + candidate.expert_decomposability
        + candidate.non_gossip_signal
    )


def select_training_topics(
    candidates: list[HotTopicCandidate],
) -> tuple[list[HotTopicCandidate], list[HotTopicCandidate]]:
    ranked = rank_candidates(candidates)
    top10 = ranked[:10]
    top3 = top10[:3]
    return top10, top3

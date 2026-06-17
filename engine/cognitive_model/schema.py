# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


IssueLevel = Literal["error", "warning"]


@dataclass
class QualityIssue:
    level: IssueLevel
    code: str
    message: str
    path: str

    def to_dict(self) -> dict[str, str]:
        return {
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "path": self.path,
        }


@dataclass
class Meta:
    title: str
    source_type: str = "book"
    version: str = "CognitiveModel.v1"


@dataclass
class SourceUnderstanding:
    material_map: list[dict[str, Any]] = field(default_factory=list)
    author_problem: str = ""
    paragraph_roles: list[dict[str, Any]] = field(default_factory=list)
    key_terms: list[str] = field(default_factory=list)


@dataclass
class BookSpine:
    core_question: str = ""
    baseline_positions: list[str] = field(default_factory=list)
    consensus_baseline: str = ""
    author_move: str = ""
    delta_sentence: str = ""
    delta_type: str = ""
    signature_terms: list[str] = field(default_factory=list)
    landing_sentence: str = ""
    carryaway: str = ""


@dataclass
class RootRank:
    domain_assumptions: list[str] = field(default_factory=list)
    phenomena: list[str] = field(default_factory=list)
    candidate_generators: list[str] = field(default_factory=list)
    root_generators: list[str] = field(default_factory=list)
    regeneration_matrix: list[dict[str, Any]] = field(default_factory=list)
    prediction_tests: list[str] = field(default_factory=list)


@dataclass
class Roundtable:
    participants: list[dict[str, Any]] = field(default_factory=list)
    tension_axes: list[str] = field(default_factory=list)
    rounds: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Distillation:
    insights: list[dict[str, Any]] = field(default_factory=list)
    qa_chain: list[dict[str, Any]] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    future_bets: list[str] = field(default_factory=list)


@dataclass
class Publishing:
    slides: list[dict[str, Any]] = field(default_factory=list)
    cards: list[dict[str, Any]] = field(default_factory=list)
    index_summary: str = ""


@dataclass
class Quality:
    checks: list[QualityIssue] = field(default_factory=list)


@dataclass
class CognitiveModel:
    title: str
    source_type: str = "book"
    source_understanding: SourceUnderstanding = field(default_factory=SourceUnderstanding)
    book_spine: BookSpine = field(default_factory=BookSpine)
    root_rank: RootRank = field(default_factory=RootRank)
    roundtable: Roundtable = field(default_factory=Roundtable)
    distillation: Distillation = field(default_factory=Distillation)
    publishing: Publishing = field(default_factory=Publishing)
    quality: Quality = field(default_factory=Quality)

    @property
    def meta(self) -> Meta:
        return Meta(title=self.title, source_type=self.source_type)

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": asdict(self.meta),
            "source_understanding": asdict(self.source_understanding),
            "book_spine": asdict(self.book_spine),
            "root_rank": asdict(self.root_rank),
            "roundtable": asdict(self.roundtable),
            "distillation": asdict(self.distillation),
            "publishing": asdict(self.publishing),
            "quality": {"checks": [issue.to_dict() for issue in self.quality.checks]},
        }

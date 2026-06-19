# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.html_ppt_display_logic import (
    DISPLAY_LOGICS,
    LAYOUT_VARIANTS,
    select_display_logic,
    select_layout_variant,
)
from engine.html_ppt_v12 import normalize_text, summarize_text


READING_LAYOUTS = {
    "reading_brief_4zone",
    "magazine_focus",
    "stance_spectrum",
    "case_file",
    "clash_courtroom",
    "evolution_ladder",
    "tension_bars",
    "question_wall",
}

READING_PAGE_TYPES = {
    "cover",
    "core_question",
    "baseline_delta",
    "rank_map",
    "response_graph",
    "qa",
    "insight",
    "insight_reading",
    "roundtable_reading",
    "clash_reading",
    "summary_reading",
    "ending",
    "source_map",
    "concept_anchor",
    "experts",
    "definition",
    "round",
    "round_opening",
    "case_shock",
    "clash",
    "moderator_crack",
    "cognitive_upgrade",
    "future_bets",
    "library_lens",
    "open_questions",
    "tension_map",
}


def ensure_reading_layout(layout: str) -> str:
    if layout not in READING_LAYOUTS:
        raise ValueError(f"unknown reading layout: {layout}")
    return layout


def ensure_display_logic(display_logic: str) -> str:
    if display_logic not in DISPLAY_LOGICS:
        raise ValueError(f"unknown display_logic: {display_logic}")
    return display_logic


def ensure_layout_variant(layout_variant: str) -> str:
    if layout_variant not in LAYOUT_VARIANTS:
        raise ValueError(f"unknown layout_variant: {layout_variant}")
    return layout_variant


def classify_position_label(text: Any) -> str:
    value = normalize_text(text)
    if any(token in value for token in ("制度", "法律", "法治", "法度")):
        return "制度解释"
    if any(token in value for token in ("资本", "生产关系", "阶级", "市场")):
        return "资本解释"
    if any(token in value for token in ("道", "自然", "规律", "无为")):
        return "规律解释"
    if "文化" in value:
        return "文化解释"
    return "综合解释"


@dataclass
class ReadingBlock:
    kind: str
    title: str
    text: str
    label: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.kind = normalize_text(self.kind)
        self.title = summarize_text(self.title, 36)
        self.text = summarize_text(self.text, 220)
        self.label = summarize_text(self.label, 28)


@dataclass
class ReadingPage:
    page_type: str
    title: str
    thesis: str = ""
    takeaway: str = ""
    layout: str = "reading_brief_4zone"
    display_logic: str = ""
    layout_variant: str = ""
    blocks: list[ReadingBlock] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.page_type not in READING_PAGE_TYPES:
            raise ValueError(f"unknown reading page_type: {self.page_type}")
        self.layout = ensure_reading_layout(self.layout)
        self.display_logic = ensure_display_logic(
            self.display_logic or select_display_logic(self.page_type, self.blocks, self.thesis, self.meta)
        )
        self.layout_variant = ensure_layout_variant(
            self.layout_variant or select_layout_variant(self.display_logic, self.page_type)
        )
        self.title = summarize_text(self.title, 42)
        self.thesis = summarize_text(self.thesis, 130)
        self.takeaway = summarize_text(self.takeaway, 150)

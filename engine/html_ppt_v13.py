# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.html_ppt_v12 import normalize_text, summarize_text


READING_LAYOUTS = {
    "reading_brief_4zone",
    "stance_spectrum",
    "clash_courtroom",
}

READING_PAGE_TYPES = {
    "cover",
    "insight_reading",
    "roundtable_reading",
    "clash_reading",
    "summary_reading",
}


def ensure_reading_layout(layout: str) -> str:
    if layout not in READING_LAYOUTS:
        raise ValueError(f"unknown reading layout: {layout}")
    return layout


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
        self.title = summarize_text(self.title, 32)
        self.text = summarize_text(self.text, 180)
        self.label = summarize_text(self.label, 24)


@dataclass
class ReadingPage:
    page_type: str
    title: str
    thesis: str = ""
    takeaway: str = ""
    layout: str = "reading_brief_4zone"
    blocks: list[ReadingBlock] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.page_type not in READING_PAGE_TYPES:
            raise ValueError(f"unknown reading page_type: {self.page_type}")
        self.layout = ensure_reading_layout(self.layout)
        self.title = summarize_text(self.title, 36)
        self.thesis = summarize_text(self.thesis, 90)
        self.takeaway = summarize_text(self.takeaway, 120)

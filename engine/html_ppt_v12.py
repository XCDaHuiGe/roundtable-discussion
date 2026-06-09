# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


PAGE_TYPES = {
    "cover",
    "insight_overview",
    "hypothesis_evolution",
    "tension_map",
    "experts",
    "round_overview",
    "speech",
    "clash",
    "cost_analysis",
    "human_nature",
    "consensus_state",
    "open_questions",
    "summary",
}


CAPACITY = {
    "title": 28,
    "subtitle": 60,
    "expert_belief": 60,
    "speech": 220,
    "clash_attack": 180,
    "clash_defense": 180,
    "insight_overview": 90,
    "open_question": 80,
    "summary": 120,
}


LAYOUT_BY_PAGE_TYPE = {
    "cover": "hero_split",
    "insight_overview": "list_compact",
    "hypothesis_evolution": "two_column_compare",
    "tension_map": "two_column_compare",
    "experts": "card_grid_2x3",
    "round_overview": "stacked_cards",
    "speech": "two_speeches",
    "clash": "single_clash",
    "cost_analysis": "stacked_cards",
    "human_nature": "stacked_cards",
    "consensus_state": "stacked_cards",
    "open_questions": "list_compact",
    "summary": "final_statement",
}


def ensure_page_type(page_type: str) -> str:
    if page_type not in PAGE_TYPES:
        raise ValueError(f"unknown page_type: {page_type}")
    return page_type


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return re.sub(r"\s+", " ", text).strip()


def summarize_text(value: Any, max_chars: int) -> str:
    text = normalize_text(value)
    if len(text) <= max_chars:
        return text
    chunks = split_text(text, max_chars)
    return chunks[0] if chunks else ""


def split_text(value: Any, max_chars: int) -> list[str]:
    text = normalize_text(value)
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    sentences = [s for s in re.split(r"(?<=[。！？!?])", text) if s.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences or [text]:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_hard_split(sentence, max_chars))
            continue
        if current and len(current) + len(sentence) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current += sentence
    if current:
        chunks.append(current)
    return chunks


def _hard_split(text: str, max_chars: int) -> list[str]:
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


@dataclass
class Page:
    page_type: str
    title: str
    layout: str | None = None
    items: list[dict[str, Any]] = field(default_factory=list)
    body: str = ""
    subtitle: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.page_type = ensure_page_type(self.page_type)
        if self.layout is None:
            self.layout = LAYOUT_BY_PAGE_TYPE[self.page_type]
        self.title = summarize_text(self.title, CAPACITY["title"])
        self.subtitle = summarize_text(self.subtitle, CAPACITY["subtitle"])
        self.body = normalize_text(self.body)

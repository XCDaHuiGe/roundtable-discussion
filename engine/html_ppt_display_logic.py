# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


DISPLAY_LOGICS = {
    "neutral",
    "impact",
    "evidence",
    "cross_exam",
    "diagnosis",
    "cost",
    "delta",
    "spectrum",
    "mechanism",
    "manifesto",
    "quiet_reading",
}


LAYOUT_VARIANTS = {
    "standard",
    "shock_poster",
    "evidence_wall",
    "interrogation_room",
    "xray_diagnosis",
    "cost_blast",
    "delta_map",
    "stance_radar",
    "mechanism_cutaway",
    "editorial_spread",
    "manifesto_poster",
    "quiet_notes",
}


def select_display_logic(
    page_type: str,
    blocks: list[Any] | None = None,
    thesis: str = "",
    meta: dict[str, Any] | None = None,
) -> str:
    """Pick the content's display intent before choosing a visual layout."""
    block_kinds = {str(getattr(block, "kind", "")).strip() for block in blocks or []}
    meta = meta or {}
    explicit = str(meta.get("display_logic") or "").strip()
    if explicit in DISPLAY_LOGICS:
        return explicit

    if page_type == "case_shock":
        if "cost" in block_kinds:
            return "cost"
        if {"source", "outcome"} & block_kinds:
            return "evidence"
        return "impact"
    if page_type == "clash":
        return "cross_exam"
    if page_type in {"cognitive_upgrade", "baseline_delta"}:
        return "delta"
    if page_type in {"rank_map", "tension_map"}:
        return "mechanism"
    if page_type in {"response_graph", "round"}:
        return "spectrum"
    if page_type in {"ending", "future_bets"}:
        return "manifesto"
    if page_type in {"qa", "open_questions", "definition", "concept_anchor"}:
        return "quiet_reading"
    return "neutral"


def select_layout_variant(display_logic: str, page_type: str = "") -> str:
    if display_logic == "impact":
        return "shock_poster"
    if display_logic == "evidence":
        return "evidence_wall"
    if display_logic == "cross_exam":
        return "interrogation_room"
    if display_logic == "diagnosis":
        return "xray_diagnosis"
    if display_logic == "cost":
        return "cost_blast"
    if display_logic == "delta":
        return "delta_map"
    if display_logic == "spectrum":
        return "stance_radar"
    if display_logic == "mechanism":
        return "mechanism_cutaway"
    if display_logic == "manifesto":
        return "manifesto_poster"
    if display_logic == "quiet_reading":
        return "quiet_notes"
    return "standard"

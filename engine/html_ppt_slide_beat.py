# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field


INTENSITIES = {"quiet", "editorial", "dramatic", "extreme"}


@dataclass
class SlideBeat:
    page_type: str
    display_logic: str
    layout_variant: str
    depth_role: str
    visual_intent: str
    reader_question: str
    memory_hook: str
    required_blocks: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    intensity: str = "editorial"


def validate_slide_beat(beat: SlideBeat) -> list[str]:
    issues: list[str] = []
    if beat.intensity not in INTENSITIES:
        issues.append("invalid_intensity")
    if not beat.depth_role.strip():
        issues.append("missing_depth_role")
    if not beat.visual_intent.strip():
        issues.append("missing_visual_intent")
    if not beat.reader_question.strip():
        issues.append("missing_reader_question")
    if not beat.memory_hook.strip():
        issues.append("missing_memory_hook")
    if beat.intensity == "extreme" and not beat.layout_variant.endswith("_extreme"):
        issues.append("extreme_requires_extreme_variant")
    return issues

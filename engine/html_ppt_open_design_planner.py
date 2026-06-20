# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from engine.html_ppt_v13 import ReadingPage
from engine.html_ppt_v13_planner import plan_reading_pages


def plan_open_design_pages(data: dict[str, Any], showoff: bool = False) -> list[ReadingPage]:
    pages = plan_reading_pages(data)
    if not showoff:
        return pages

    upgraded: list[ReadingPage] = []
    for page in pages:
        if page.page_type == "cover":
            upgraded.append(page)
        elif page.page_type == "clash_reading":
            upgraded.append(_upgrade_clash(page))
        elif page.page_type == "roundtable_reading":
            upgraded.append(_upgrade_roundtable(page))
        elif page.page_type in {"insight_reading", "summary_reading"}:
            upgraded.append(_upgrade_manifesto(page))
        else:
            upgraded.append(page)
    return upgraded


def _upgrade_clash(page: ReadingPage) -> ReadingPage:
    return ReadingPage(
        page_type="clash",
        title=page.title,
        thesis=page.thesis,
        takeaway=page.takeaway,
        layout="clash_courtroom",
        display_logic="cross_exam",
        layout_variant="interrogation_room_extreme",
        intensity="extreme",
        beat="put the strongest contradiction on trial",
        reader_question="Which frame survives the cross-examination?",
        memory_hook="A good clash makes the hidden frame visible.",
        source_refs=[f"rounds[{page.meta.get('round_index', '?')}].clash_rounds"],
        blocks=page.blocks,
        meta=page.meta,
    )


def _upgrade_roundtable(page: ReadingPage) -> ReadingPage:
    return ReadingPage(
        page_type="response_graph",
        title=page.title,
        thesis=page.thesis,
        takeaway=page.takeaway,
        layout="stance_spectrum",
        display_logic="spectrum",
        layout_variant="stance_radar",
        intensity="dramatic",
        beat="map positions before judging them",
        reader_question="Which stance changes the problem frame?",
        memory_hook="The argument is a field, not a queue.",
        source_refs=[f"rounds[{page.meta.get('round_index', '?')}].stances"],
        blocks=page.blocks,
        meta=page.meta,
    )


def _upgrade_manifesto(page: ReadingPage) -> ReadingPage:
    return ReadingPage(
        page_type="insight",
        title=page.title,
        thesis=page.thesis,
        takeaway=page.takeaway,
        layout="magazine_focus",
        display_logic="manifesto",
        layout_variant="manifesto_poster_extreme",
        intensity="extreme",
        beat="turn the distilled insight into a visual verdict",
        reader_question="What sentence should the reader remember?",
        memory_hook=page.takeaway or page.thesis,
        source_refs=["insights"],
        blocks=page.blocks,
        meta=page.meta,
    )

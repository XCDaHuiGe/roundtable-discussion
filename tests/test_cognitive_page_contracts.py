# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from engine.html_ppt.cognitive_page_contracts import COGNITIVE_PAGE_TYPES, PAGE_LAYOUTS
from engine.html_ppt_v13 import READING_LAYOUTS, READING_PAGE_TYPES, ReadingPage


def test_page_contracts_include_rhythm_and_depth_pages():
    expected = {
        "cover",
        "source_map",
        "experts",
        "library_lens",
        "core_question",
        "baseline_delta",
        "concept_anchor",
        "definition",
        "rank_map",
        "round",
        "round_opening",
        "response_graph",
        "case_shock",
        "clash",
        "moderator_crack",
        "cognitive_upgrade",
        "qa",
        "insight",
        "open_questions",
        "tension_map",
        "future_bets",
        "ending",
    }
    assert COGNITIVE_PAGE_TYPES == expected


def test_all_page_types_have_valid_layouts():
    assert set(COGNITIVE_PAGE_TYPES) == set(PAGE_LAYOUTS)
    for layout in PAGE_LAYOUTS.values():
        assert layout in READING_LAYOUTS


def test_layout_catalog_is_diverse_enough_to_avoid_flat_decks():
    assert len(set(PAGE_LAYOUTS.values())) >= 6
    assert PAGE_LAYOUTS["case_shock"] == "case_file"
    assert PAGE_LAYOUTS["cognitive_upgrade"] == "evolution_ladder"
    assert PAGE_LAYOUTS["open_questions"] == "question_wall"
    assert PAGE_LAYOUTS["tension_map"] == "tension_bars"
    assert PAGE_LAYOUTS["clash"] == "clash_courtroom"


def test_reading_page_accepts_all_cognitive_types():
    for page_type in COGNITIVE_PAGE_TYPES:
        page = ReadingPage(page_type=page_type, title=f"Test {page_type}", layout=PAGE_LAYOUTS[page_type])
        assert page.page_type == page_type
        assert page.layout == PAGE_LAYOUTS[page_type]
        assert page_type in READING_PAGE_TYPES


def test_reading_page_rejects_unknown_type():
    with pytest.raises(ValueError, match="unknown reading page_type"):
        ReadingPage(page_type="unknown_type", title="Test")

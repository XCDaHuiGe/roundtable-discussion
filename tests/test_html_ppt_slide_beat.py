from engine.html_ppt_slide_beat import SlideBeat, validate_slide_beat
from engine.html_ppt_v13 import ReadingPage


def test_valid_slide_beat_passes():
    beat = SlideBeat(
        page_type="case_shock",
        display_logic="cost",
        layout_variant="cost_blast_extreme",
        depth_role="make the cost visible",
        visual_intent="explode the hidden cost into the main composition",
        reader_question="What does this idea cost when accepted?",
        memory_hook="Every idea sends an invoice.",
        required_blocks=["event", "cost"],
        source_refs=["rounds[0].reality_cases[0]"],
        intensity="extreme",
    )

    assert validate_slide_beat(beat) == []


def test_reading_page_accepts_intensity_and_reader_question():
    page = ReadingPage(
        page_type="case_shock",
        title="cost",
        intensity="extreme",
        reader_question="What does this cost?",
        memory_hook="The idea sends an invoice.",
    )

    assert page.intensity == "extreme"
    assert page.layout_variant.endswith("_extreme")
    assert page.reader_question == "What does this cost?"

from engine.html_ppt_design_strength import validate_design_strength
from engine.html_ppt_display_logic import select_layout_variant
from engine.html_ppt_v13 import ReadingBlock, ReadingPage
from engine.html_ppt_v13_renderer import render_reading_html


def test_extreme_cost_uses_cost_blast_extreme():
    assert select_layout_variant("cost", "case_shock", intensity="extreme") == "cost_blast_extreme"


def test_editorial_cost_uses_existing_cost_blast():
    assert select_layout_variant("cost", "case_shock", intensity="editorial") == "cost_blast"


def test_extreme_evidence_uses_evidence_wall_extreme():
    assert select_layout_variant("evidence", "case_shock", intensity="extreme") == "evidence_wall_extreme"


def test_render_cost_blast_extreme_contains_stage_markers():
    page = ReadingPage(
        page_type="case_shock",
        title="cost",
        layout="case_file",
        display_logic="cost",
        intensity="extreme",
        blocks=[ReadingBlock("event", "event", "impact"), ReadingBlock("cost", "cost", "system cost")],
    )

    html = render_reading_html([page], title="extreme")

    assert 'data-layout-variant="cost_blast_extreme"' in html
    assert 'data-stage-shell="true"' in html
    assert "cost-blast-extreme" in html


def test_design_strength_requires_extreme_variant_for_extreme_page():
    issues = validate_design_strength([
        {"layout_variant": "cost_blast", "intensity": "extreme", "display_logic": "cost"},
    ])

    assert "extreme_without_extreme_variant" in issues


def test_design_strength_accepts_extreme_variant():
    issues = validate_design_strength([
        {"layout_variant": "cost_blast_extreme", "intensity": "extreme", "display_logic": "cost"},
        {"layout_variant": "quiet_notes", "intensity": "quiet", "display_logic": "quiet_reading"},
    ])

    assert issues == []


def test_design_strength_rejects_all_reading_shell_showoff_deck():
    issues = validate_design_strength([
        {"layout_variant": "quiet_notes", "intensity": "editorial", "display_logic": "quiet_reading", "shell": "reading"},
        {"layout_variant": "stance_radar", "intensity": "dramatic", "display_logic": "spectrum", "shell": "reading"},
        {"layout_variant": "quiet_notes", "intensity": "editorial", "display_logic": "quiet_reading", "shell": "reading"},
    ], showoff=True)

    assert "showoff_without_stage_shell" in issues

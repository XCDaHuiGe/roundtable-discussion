from engine.html_ppt_v13 import ReadingBlock, ReadingPage
from engine.html_ppt_v13_renderer import render_reading_html


def test_case_shock_with_cost_uses_cost_blast():
    page = ReadingPage(
        page_type="case_shock",
        title="case",
        layout="case_file",
        blocks=[
            ReadingBlock("event", "事件", "冲击"),
            ReadingBlock("cost", "代价", "系统代价"),
        ],
    )

    assert page.display_logic == "cost"
    assert page.layout_variant == "cost_blast"


def test_case_shock_without_cost_uses_shock_poster():
    page = ReadingPage(
        page_type="case_shock",
        title="case",
        layout="case_file",
        blocks=[ReadingBlock("event", "事件", "冲击")],
    )

    assert page.display_logic == "impact"
    assert page.layout_variant == "shock_poster"


def test_clash_uses_interrogation_room_variant():
    page = ReadingPage(
        page_type="clash",
        title="debate",
        layout="clash_courtroom",
        blocks=[
            ReadingBlock("attack", "攻击", "质疑"),
            ReadingBlock("defense", "回应", "反驳"),
        ],
    )

    assert page.display_logic == "cross_exam"
    assert page.layout_variant == "interrogation_room"


def test_renderer_exposes_open_design_attributes_and_variant_class():
    page = ReadingPage(
        page_type="case_shock",
        title="case",
        layout="case_file",
        takeaway="结论",
        blocks=[
            ReadingBlock("event", "事件", "冲击"),
            ReadingBlock("cost", "代价", "系统代价"),
        ],
    )

    html = render_reading_html([page], title="open design")

    assert 'data-display-logic="cost"' in html
    assert 'data-layout-variant="cost_blast"' in html
    assert "cost-blast" in html


def test_open_design_keeps_navigation_contract():
    page = ReadingPage(page_type="case_shock", title="case", layout="case_file")

    html = render_reading_html([page], title="open design")

    assert 'id="navDots"' in html
    assert html.count("function go(") == 1
    assert "setTimeout(()=>wheelTimer=null,400)" in html
    assert ".slide{" in html
    assert "height:100vh" in html

from engine.html_ppt_v13 import ReadingBlock, ReadingPage
from engine.html_ppt_v13_renderer import render_reading_html


def test_render_reading_html_contains_dense_reading_regions():
    html = render_reading_html([
        ReadingPage(
            page_type="roundtable_reading",
            title="文化属性真的决定命运吗",
            thesis="文化不是宿命，而是解释框架。",
            takeaway="读者应带走结构视角。",
            layout="stance_spectrum",
            blocks=[
                ReadingBlock("stance", "丁元英", "文化决定行动方式。", label="文化解释"),
                ReadingBlock("stance", "韩非子", "制度和法律塑造路径。", label="制度解释"),
                ReadingBlock("stance", "马克思", "资本放大结果。", label="资本解释"),
                ReadingBlock("stance", "老子", "规律不可违。", label="规律解释"),
            ],
        )
    ], title="测试")
    assert "阅读重点" in html
    assert "最终洞见" in html
    assert "stance-spectrum" in html
    assert html.count("reading-block") >= 4


def test_render_reading_html_keeps_v12_navigation_contract():
    html = render_reading_html([
        ReadingPage(page_type="summary_reading", title="总结", takeaway="结论", blocks=[
            ReadingBlock("takeaway", "结论一", "内容"),
            ReadingBlock("takeaway", "结论二", "内容"),
            ReadingBlock("takeaway", "结论三", "内容"),
        ])
    ], title="测试")
    assert html.count("function go(") == 1
    assert 'id="navDots"' in html
    assert "setTimeout(()=>wheelTimer=null,400)" in html
    assert ".slide{height:100vh" in html.replace(" ", "")

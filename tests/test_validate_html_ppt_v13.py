from engine.html_ppt_v13 import ReadingBlock, ReadingPage
from engine.html_ppt_v13_renderer import render_reading_html
from engine.validate_html_ppt_v13 import validate_reading_html


def valid_html():
    page = ReadingPage(
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
            ReadingBlock("stance", "芒格", "多元模型避免单因归因。", label="综合解释"),
        ],
    )
    return render_reading_html([page], title="测试")


def test_validate_reading_html_accepts_dense_page():
    result = validate_reading_html(valid_html())
    assert result.ok, result.errors


def test_validate_reading_html_rejects_missing_takeaway():
    html = valid_html().replace("最终洞见", "最终")
    result = validate_reading_html(html)
    assert not result.ok
    assert any("takeaway" in error for error in result.errors)


def test_validate_reading_html_rejects_low_information_page():
    html = valid_html().replace("reading-block", "thin-block")
    result = validate_reading_html(html)
    assert not result.ok
    assert any("information density" in error for error in result.errors)

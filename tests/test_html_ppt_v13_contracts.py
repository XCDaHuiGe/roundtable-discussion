import pytest

from engine.html_ppt_v13 import (
    ReadingBlock,
    ReadingPage,
    classify_position_label,
    ensure_reading_layout,
)


def test_reading_page_requires_known_layout():
    with pytest.raises(ValueError, match="unknown reading layout"):
        ReadingPage(page_type="roundtable_reading", title="标题", layout="bad_layout")


def test_reading_page_keeps_takeaway_and_blocks():
    page = ReadingPage(
        page_type="roundtable_reading",
        title="文化属性",
        thesis="文化不是宿命，而是情境应对系统。",
        takeaway="读者应带走结构视角。",
        layout="stance_spectrum",
        blocks=[ReadingBlock(kind="stance", title="丁元英", text="文化决定行动方式。")],
    )
    assert page.title == "文化属性"
    assert page.takeaway == "读者应带走结构视角。"
    assert page.blocks[0].kind == "stance"


def test_classify_position_label_without_gpt():
    assert classify_position_label("文化属性决定人的选择") == "文化解释"
    assert classify_position_label("制度和法律塑造路径") == "制度解释"
    assert classify_position_label("资本和生产关系放大结果") == "资本解释"
    assert classify_position_label("道法自然，遵循规律") == "规律解释"
    assert classify_position_label("复杂问题需要综合判断") == "综合解释"


def test_ensure_reading_layout_rejects_unknown_layout():
    with pytest.raises(ValueError, match="unknown reading layout"):
        ensure_reading_layout("poster")

from engine.html_ppt_v12 import Page
from engine.html_ppt_v12_renderer import render_html
from engine.validate_html_ppt_v12 import validate_html


def test_validate_html_accepts_v12_renderer_output():
    result = validate_html(render_html([Page("cover", title="封面")], title="测试"))
    assert result.ok, result.errors


def test_validate_html_rejects_internal_scroll():
    html = render_html([Page("cover", title="封面")], title="测试")
    result = validate_html(html + "<style>.x{overflow-y:auto}</style>")
    assert not result.ok
    assert any("internal scroll" in error for error in result.errors)


def test_validate_html_rejects_duplicate_navigation():
    html = render_html([Page("cover", title="封面")], title="测试")
    result = validate_html(html.replace("</body>", "<script>let wheelTimer=null;</script></body>"))
    assert not result.ok
    assert any("wheelTimer" in error for error in result.errors)


def test_validate_html_rejects_missing_click_navigation():
    html = render_html([Page("cover", title="封面")], title="测试")
    result = validate_html(html.replace("document.body.addEventListener('click'", "document.body.onclick"))
    assert not result.ok
    assert any("click navigation" in error for error in result.errors)

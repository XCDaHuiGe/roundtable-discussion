from engine.html_ppt_v12 import Page
from engine.html_ppt_v12_renderer import render_html


def test_render_html_has_single_navigation_system():
    html = render_html([
        Page("cover", title="封面"),
        Page("summary", title="总结", body="结论"),
    ], title="测试")
    assert html.count("function go(") == 1
    assert html.count("let wheelTimer=null") == 1
    assert html.count("setTimeout(()=>wheelTimer=null,400)") == 1
    assert html.count('id="navDots"') == 1
    assert html.count('class="slide visible"') == 1
    assert html.count('class="slide"') == 1


def test_render_html_contains_required_navigation_contract():
    html = render_html([Page("cover", title="封面")], title="测试")
    assert "e.preventDefault()" in html
    assert "setTimeout(()=>wheelTimer=null,400)" in html
    assert "ArrowDown" in html
    assert "PageDown" in html
    assert "Home" in html
    assert "End" in html
    assert "document.body.addEventListener('click'" in html


def test_render_html_escapes_content():
    html = render_html([Page("summary", title="<坏标题>", body="<script>alert(1)</script>")], title="测试")
    assert "&lt;坏标题&gt;" in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>alert(1)</script>" not in html

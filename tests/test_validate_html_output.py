# -*- coding: utf-8 -*-
"""HTML 输出质量门测试"""
from engine.quality_gates.validate_html_output import validate_html_output


def _make_valid_html() -> str:
    """生成一个符合规范的 HTML 模板"""
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
.slide {
  height: 100vh;
  overflow: hidden;
}
.nav-dot {
  width: 10px;
  height: 10px;
}
</style>
</head>
<body>
<section class="slide visible">
  <h1>封面</h1>
</section>
<section class="slide">
  <h1>第二页</h1>
</section>
<div id="navDots">
  <button class="nav-dot active"></button>
  <button class="nav-dot"></button>
</div>
<div id="progress"></div>
<script>
let cur = 0;
let wheelTimer = null;
const total = 2;
const sections = document.querySelectorAll('.slide');
const dotsContainer = document.getElementById('navDots');
const progress = document.getElementById('progress');

function go(n) {
  if (n < 0 || n >= total) return;
  sections[cur].classList.remove('visible');
  dotsContainer.children[cur].classList.remove('active');
  cur = n;
  sections[cur].scrollIntoView({behavior: 'smooth', block: 'start'});
  sections[cur].classList.add('visible');
  dotsContainer.children[cur].classList.add('active');
  progress.style.width = ((cur + 1) / total * 100) + '%';
}

document.addEventListener('keydown', e => {
  if (e.key === 'ArrowDown' || e.key === 'ArrowRight' || e.key === ' ') {
    e.preventDefault();
    go(cur + 1);
  } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
    e.preventDefault();
    go(cur - 1);
  }
});

document.addEventListener('wheel', e => {
  e.preventDefault();
  if (wheelTimer) return;
  wheelTimer = setTimeout(() => wheelTimer = null, 400);
  if (e.deltaY > 0) go(cur + 1);
  else if (e.deltaY < 0) go(cur - 1);
}, {passive: false});

document.body.addEventListener('click', e => {
  if (e.target.closest('.nav-dot')) return;
  go(cur + 1);
});

// 预置 nav dots，不动态创建
dotsContainer.querySelectorAll('.nav-dot').forEach((dot, i) => {
  dot.onclick = () => go(i);
});
</script>
</body>
</html>"""


def test_validate_html_output_accepts_valid_html():
    """正常 HTML 应该通过验证"""
    html = _make_valid_html()
    result = validate_html_output(html)
    assert result["ok"], f"Expected ok=True, got errors: {result['errors']}"


def test_validate_html_output_rejects_overflow_y_auto():
    """包含 overflow-y: auto 应该报错"""
    html = _make_valid_html()
    html = html.replace("</style>", ".content { overflow-y: auto; }</style>")
    result = validate_html_output(html)
    assert not result["ok"]
    assert any(e["code"] == "internal_scroll_y" for e in result["errors"])


def test_validate_html_output_rejects_overflow_y_scroll():
    """包含 overflow-y: scroll 应该报错"""
    html = _make_valid_html()
    html = html.replace("</style>", ".content { overflow-y: scroll; }</style>")
    result = validate_html_output(html)
    assert not result["ok"]
    assert any(e["code"] == "internal_scroll_y" for e in result["errors"])


def test_validate_html_output_rejects_overflow_auto_in_slide():
    """.slide 中包含 overflow: auto 应该报错"""
    html = _make_valid_html()
    html = html.replace(".slide {", ".slide { overflow: auto; ")
    result = validate_html_output(html)
    assert not result["ok"]
    assert any(e["code"] == "internal_scroll_in_slide" for e in result["errors"])


def test_validate_html_output_rejects_duplicate_go_function():
    """多个 go() 函数应该报错"""
    html = _make_valid_html()
    html = html.replace("</script>", "function go(n) { console.log('duplicate'); }</script>")
    result = validate_html_output(html)
    assert not result["ok"]
    assert any(e["code"] == "duplicate_go_function" for e in result["errors"])


def test_validate_html_output_rejects_missing_go_function():
    """缺少 go() 函数应该报错"""
    html = _make_valid_html()
    html = html.replace("function go(n)", "function navigate(n)")
    result = validate_html_output(html)
    assert not result["ok"]
    assert any(e["code"] == "missing_go_function" for e in result["errors"])


def test_validate_html_output_rejects_missing_wheel_timer():
    """缺少 wheelTimer 应该报错"""
    html = _make_valid_html()
    html = html.replace("let wheelTimer = null;", "let timer = null;")
    html = html.replace("wheelTimer", "timer")
    result = validate_html_output(html)
    assert not result["ok"]
    assert any(e["code"] == "missing_wheel_timer" for e in result["errors"])


def test_validate_html_output_rejects_duplicate_wheel_timer():
    """多次声明 wheelTimer 应该报错"""
    html = _make_valid_html()
    html = html.replace("let wheelTimer = null;", "let wheelTimer = null; let wheelTimer = null;")
    result = validate_html_output(html)
    assert not result["ok"]
    assert any(e["code"] == "duplicate_wheel_timer" for e in result["errors"])


def test_validate_html_output_rejects_slide_nav_dot_mismatch():
    """slide 数与 nav dot 数不一致应该报错"""
    html = _make_valid_html()
    # 添加一个额外的 slide 但不添加对应的 nav dot
    html = html.replace(
        '<section class="slide">',
        '<section class="slide"><h1>第三页</h1></section><section class="slide">'
    )
    result = validate_html_output(html)
    assert not result["ok"]
    assert any(e["code"] == "slide_nav_dot_mismatch" for e in result["errors"])


def test_validate_html_output_rejects_no_slides():
    """没有 slide 应该报错"""
    html = _make_valid_html()
    html = html.replace('<section class="slide visible">', '<div class="slide visible">')
    html = html.replace('<section class="slide">', '<div class="slide">')
    html = html.replace('</section>', '</div>')
    result = validate_html_output(html)
    assert not result["ok"]
    assert any(e["code"] == "no_slides" for e in result["errors"])


def test_validate_html_output_rejects_no_nav_dots():
    """没有 nav dot 应该报错"""
    html = _make_valid_html()
    # 替换所有 nav-dot 相关的 class
    html = html.replace('class="nav-dot active"', 'class="navigation-dot active"')
    html = html.replace('class="nav-dot"', 'class="navigation-dot"')
    result = validate_html_output(html)
    assert not result["ok"]
    assert any(e["code"] == "no_nav_dots" for e in result["errors"])


def test_validate_html_output_rejects_missing_slide_height():
    """缺少 slide height 应该报错"""
    html = _make_valid_html()
    html = html.replace("height: 100vh;", "min-height: 100vh;")
    result = validate_html_output(html)
    assert not result["ok"]
    assert any(e["code"] == "missing_slide_height" for e in result["errors"])


def test_validate_html_output_warns_missing_overflow_hidden():
    """缺少 overflow: hidden 应该警告"""
    html = _make_valid_html()
    html = html.replace("overflow: hidden;", "overflow: visible;")
    result = validate_html_output(html)
    # 这只是 warning，不影响 ok
    assert result["ok"]
    assert any(e["code"] == "missing_overflow_hidden" for e in result["errors"])


def test_validate_html_output_warns_horizontal_scroll():
    """横向滚动应该警告"""
    html = _make_valid_html()
    html = html.replace("</style>", ".container { overflow-x: auto; }</style>")
    result = validate_html_output(html)
    # 这只是 warning，不影响 ok
    assert result["ok"]
    assert any(e["code"] == "horizontal_scroll" for e in result["errors"])


def test_validate_html_output_warns_missing_viewport():
    """缺少 viewport meta 标签应该警告"""
    html = _make_valid_html()
    html = html.replace('<meta name="viewport" content="width=device-width, initial-scale=1.0">', '')
    result = validate_html_output(html)
    # 这只是 warning，不影响 ok
    assert result["ok"]
    assert any(e["code"] == "missing_viewport" for e in result["errors"])


def test_validate_html_output_rejects_multiple_initial_visible_slides():
    """多个初始可见 slide 应该报错"""
    html = _make_valid_html()
    html = html.replace('<section class="slide">', '<section class="slide visible">')
    result = validate_html_output(html)
    assert not result["ok"]
    assert any(e["code"] == "initial_visible_slide" for e in result["errors"])


def test_validate_html_output_rejects_no_initial_visible_slide():
    """没有初始可见 slide 应该报错"""
    html = _make_valid_html()
    html = html.replace('class="slide visible"', 'class="slide"')
    result = validate_html_output(html)
    assert not result["ok"]
    assert any(e["code"] == "initial_visible_slide" for e in result["errors"])
# -*- coding: utf-8 -*-
"""Tests for V13 strict template auditor."""
from engine.audit_templates_v13 import audit_template, TemplateAudit
from pathlib import Path
import tempfile


def _write_tmp(content: str) -> Path:
    p = Path(tempfile.mktemp(suffix=".html"))
    p.write_text(content, encoding="utf-8")
    return p


GOOD_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><style>
*{box-sizing:border-box}
html,body{margin:0;height:100%;overflow:hidden}
.slide{height:100vh;width:100vw;overflow:hidden;display:none}
.slide.visible{display:flex}
</style></head>
<body>
{{slides}}
<div id="navDots"></div>
<script>
(function(){
  const sections=[...document.querySelectorAll('.slide')];
  const total=sections.length;
  let cur=0;
  function go(n){
    if(n<0||n>=total)return;
    sections[cur].classList.remove('visible');
    cur=n;
    sections[cur].classList.add('visible');
  }
  document.addEventListener('keydown',e=>{
    if(e.key==='ArrowDown'){e.preventDefault();go(cur+1)}
    else if(e.key==='ArrowUp'){e.preventDefault();go(cur-1)}
  });
  let wheelTimer=null;
  document.addEventListener('wheel',e=>{
    e.preventDefault();
    if(wheelTimer)return;
    wheelTimer=setTimeout(()=>wheelTimer=null,400);
    if(e.deltaY>0)go(cur+1);
    else if(e.deltaY<0)go(cur-1);
  },{passive:false});
  document.body.addEventListener('click',e=>{
    if(e.target.closest('.nav-dot'))return;
    go(cur+1);
  });
})();
</script>
</body>
</html>
"""


def test_good_template_gets_grade_a():
    p = _write_tmp(GOOD_TEMPLATE)
    try:
        r = audit_template(p, "test-good")
        assert r.grade == "A", f"Expected A, got {r.grade}: {r.issues}"
    finally:
        p.unlink()


def test_missing_100vh_gets_penalty():
    content = GOOD_TEMPLATE.replace("height:100vh", "height:auto")
    p = _write_tmp(content)
    try:
        r = audit_template(p, "test-no-100vh")
        assert r.grade != "A"
        assert any("slide_height_100vh" in i for i in r.issues)
    finally:
        p.unlink()


def test_internal_scroll_detected():
    content = GOOD_TEMPLATE.replace("overflow:hidden", "overflow-y:auto", 1)
    p = _write_tmp(content)
    try:
        r = audit_template(p, "test-scroll")
        assert r.checks.get("no_internal_scroll") is False
    finally:
        p.unlink()


def test_handlebars_legacy_gets_grade_c():
    content = GOOD_TEMPLATE.replace("{{slides}}", "{{#each slides}}\n{{/each}}")
    p = _write_tmp(content)
    try:
        r = audit_template(p, "test-hb")
        assert r.grade == "C"
        assert any("Handlebars" in i for i in r.issues)
    finally:
        p.unlink()


def test_duplicate_wheel_listener_detected():
    # inject a second wheel listener
    content = GOOD_TEMPLATE.replace(
        "})();\n</script>",
        "  document.addEventListener('wheel',function(e){e.preventDefault()},{passive:false});\n})();\n</script>",
    )
    p = _write_tmp(content)
    try:
        r = audit_template(p, "test-dup")
        assert r.checks.get("no_duplicate_nav") is False
    finally:
        p.unlink()


def test_missing_body_html_lock_detected():
    content = GOOD_TEMPLATE.replace("overflow:hidden", "overflow:visible")
    p = _write_tmp(content)
    try:
        r = audit_template(p, "test-unlock")
        assert r.checks.get("body_html_scroll_locked") is False
    finally:
        p.unlink()


def test_mixed_slide_section_selector_detected():
    content = GOOD_TEMPLATE.replace(
        "querySelectorAll('.slide')",
        "querySelectorAll('.section')",
    )
    # now it uses .section but CSS still defines .slide
    # inject a second querySelectorAll('.slide')
    content = content.replace(
        "})();\n</script>",
        "  const x=document.querySelectorAll('.slide');\n})();\n</script>",
    )
    p = _write_tmp(content)
    try:
        r = audit_template(p, "test-mixed")
        assert r.checks.get("slide_selector_consistent") is False
    finally:
        p.unlink()


def test_file_not_found_gets_grade_c():
    r = audit_template(Path("/nonexistent/file.html"), "test-missing")
    assert r.grade == "C"
    assert any("not found" in i for i in r.issues)

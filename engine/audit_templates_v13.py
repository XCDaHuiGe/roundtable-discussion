# -*- coding: utf-8 -*-
"""
V13 模板审计器 - 严格检查 engine/template-*.html 是否符合 V13 生成标准。

分级：
  A 可提炼主题 — 结构和导航基本合格，可提取视觉 token
  B 需修规范   — 存在可修复的结构性问题
  C legacy 隔离 — Handlebars legacy 或结构性不可修复

用法：
  python engine/audit_templates_v13.py
  python engine/audit_templates_v13.py --json  # 输出 JSON
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ENGINE_DIR = Path(__file__).parent


@dataclass
class TemplateAudit:
    file: str
    template_id: str
    grade: str = "B"  # A / B / C
    checks: dict[str, bool] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.grade == "A"


# ---- individual checks ----

def _check_doctype(content: str) -> tuple[str, bool]:
    return ("has_doctype", "<!DOCTYPE html>" in content)


def _check_slides_placeholder(content: str) -> tuple[str, bool]:
    has_adapter = "{{slides}}" in content
    has_handlebars = bool(re.search(r"\{\{#each", content))
    return ("has_slides_placeholder", has_adapter or has_handlebars)


def _is_handlebars(content: str) -> tuple[str, bool]:
    return ("is_handlebars_legacy", bool(re.search(r"\{\{#each|\{\{add", content)))


def _check_slide_height_100vh(content: str) -> tuple[str, bool]:
    """检查 .section 或 .slide 是否显式定义 height:100vh 或 height:100vh"""
    compact = re.sub(r"\s+", "", content)
    patterns = [
        ".slide{height:100vh",
        ".section{height:100vh",
        ".slide{height:100%",
        ".section{height:100%",
    ]
    found = any(p in compact for p in patterns)
    # also check via regex for spacing variants
    if not found:
        found = bool(re.search(r"\.(slide|section)\s*\{[^}]*height\s*:\s*100(vh|%)", content))
    return ("slide_height_100vh", found)


def _check_overflow_hidden(content: str) -> tuple[str, bool]:
    compact = re.sub(r"\s+", "", content)
    # check .slide or .section has overflow:hidden
    found = bool(re.search(r"\.(slide|section)\s*\{[^}]*overflow\s*:\s*hidden", content))
    return ("overflow_hidden_on_slides", found)


def _check_no_internal_scroll(content: str) -> tuple[str, bool]:
    """检查是否出现 overflow-y:auto / overflow-y:scroll / overflow:auto / overflow:scroll"""
    # exclude comments
    stripped = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    violations = re.findall(
        r"overflow(?:-y)?\s*:\s*(?:auto|scroll)",
        stripped,
        re.IGNORECASE,
    )
    return ("no_internal_scroll", len(violations) == 0)


def _check_body_html_locked(content: str) -> tuple[str, bool]:
    """检查 body 和 html 是否锁滚动（overflow:hidden）"""
    compact = re.sub(r"\s+", "", content)
    body_locked = bool(re.search(r"body\s*\{[^}]*overflow\s*:\s*hidden", content))
    html_locked = bool(re.search(r"html\s*\{[^}]*overflow\s*:\s*hidden", content))
    # also check combined html,body
    combined = "html,body" in compact and "overflow:hidden" in compact
    ok = (body_locked or combined) and (html_locked or combined)
    return ("body_html_scroll_locked", ok)


def _check_keyboard_nav(content: str) -> tuple[str, bool]:
    has_next = "go(cur+1)" in content or "go(cur + 1)" in content
    has_prev = "go(cur-1)" in content or "go(cur - 1)" in content
    return ("has_keyboard_nav", has_next and has_prev)


def _check_wheel_nav(content: str) -> tuple[str, bool]:
    has_wheel = "addEventListener('wheel'" in content or 'addEventListener("wheel"' in content
    has_prevent = "e.preventDefault()" in content or "event.preventDefault()" in content
    has_passive = "{passive:false}" in content or "{ passive: false }" in content
    return ("has_wheel_nav", has_wheel and has_prevent and has_passive)


def _check_click_nav(content: str) -> tuple[str, bool]:
    has_click = "addEventListener('click'" in content or 'addEventListener("click"' in content
    return ("has_click_nav", has_click)


def _check_nav_dots(content: str) -> tuple[str, bool]:
    has_dots = 'id="navDots"' in content or 'id="nav"' in content or 'class="nav-dots"' in content
    return ("has_nav_dots", has_dots)


def _check_duplicate_nav_scripts(content: str) -> tuple[str, bool]:
    """检查是否存在重复导航脚本（多段 wheel/keydown/click 监听）"""
    wheel_count = len(re.findall(r"addEventListener\s*\(\s*['\"]wheel['\"]", content))
    keydown_count = len(re.findall(r"addEventListener\s*\(\s*['\"]keydown['\"]", content))
    click_count = len(re.findall(r"addEventListener\s*\(\s*['\"]click['\"]", content))
    # also check for multiple go() function definitions
    go_count = len(re.findall(r"function\s+go\s*\(", content))

    issues = []
    if wheel_count > 1:
        issues.append(f"wheel listeners: {wheel_count}")
    if keydown_count > 1:
        issues.append(f"keydown listeners: {keydown_count}")
    if go_count > 1:
        issues.append(f"go() definitions: {go_count}")

    return ("no_duplicate_nav", len(issues) == 0)


def _check_slide_selector_consistency(content: str) -> tuple[str, bool]:
    """检查 querySelector 是否只用 .slide 或只用 .section，不混用"""
    uses_slide = bool(re.search(r"querySelectorAll\s*\(\s*['\"]\.slide['\"]", content))
    uses_section = bool(re.findall(r"querySelectorAll\s*\(\s*['\"]\.section['\"]", content))
    # mixed usage is a problem
    if uses_slide and uses_section:
        return ("slide_selector_consistent", False)
    return ("slide_selector_consistent", True)


# ---- main audit logic ----

ALL_CHECKS = [
    _check_doctype,
    _check_slides_placeholder,
    _is_handlebars,
    _check_slide_height_100vh,
    _check_overflow_hidden,
    _check_no_internal_scroll,
    _check_body_html_locked,
    _check_keyboard_nav,
    _check_wheel_nav,
    _check_click_nav,
    _check_nav_dots,
    _check_duplicate_nav_scripts,
    _check_slide_selector_consistency,
]


def audit_template(template_path: Path, template_id: str) -> TemplateAudit:
    result = TemplateAudit(file=template_path.name, template_id=template_id)

    if not template_path.exists():
        result.grade = "C"
        result.issues.append("file not found")
        return result

    content = template_path.read_text(encoding="utf-8")

    for check_fn in ALL_CHECKS:
        name, passed = check_fn(content)
        result.checks[name] = passed

    # grading logic
    is_hb = result.checks.get("is_handlebars_legacy", False)
    if is_hb:
        result.grade = "C"
        result.issues.append("Handlebars legacy — cannot enter V13 directly")
        return result

    # critical checks for grade A
    critical = [
        "slide_height_100vh",
        "overflow_hidden_on_slides",
        "no_internal_scroll",
        "body_html_scroll_locked",
        "has_keyboard_nav",
        "has_wheel_nav",
        "has_click_nav",
        "has_nav_dots",
        "no_duplicate_nav",
        "slide_selector_consistent",
    ]
    for key in critical:
        if not result.checks.get(key, False):
            result.issues.append(f"failed: {key}")

    failed_critical = sum(1 for key in critical if not result.checks.get(key, False))
    if failed_critical == 0:
        result.grade = "A"
    elif failed_critical <= 3:
        result.grade = "B"
    else:
        result.grade = "C"

    return result


def audit_all_templates() -> list[TemplateAudit]:
    config_path = ENGINE_DIR / "templates.json"
    if not config_path.exists():
        return []

    config = json.loads(config_path.read_text(encoding="utf-8"))
    results = []
    for t in config.get("templates", []):
        path = ENGINE_DIR / t["file"]
        results.append(audit_template(path, t["id"]))
    return results


def print_report(results: list[TemplateAudit]) -> None:
    grade_icons = {"A": "🟢", "B": "🟡", "C": "🔴"}

    print("\n" + "=" * 70)
    print(" V13 模板严格审计报告")
    print("=" * 70)

    for grade_label, grade_char in [("可提炼主题 (A)", "A"), ("需修规范 (B)", "B"), ("Legacy 隔离 (C)", "C")]:
        group = [r for r in results if r.grade == grade_char]
        if not group:
            continue
        print(f"\n{grade_icons[grade_char]} {grade_label}：{len(group)} 个")
        print("-" * 50)
        for r in group:
            print(f"  {r.template_id:<22} {r.file}")
            for issue in r.issues:
                print(f"    ⚠ {issue}")

    # summary
    counts = {g: sum(1 for r in results if r.grade == g) for g in "ABC"}
    print(f"\n{'=' * 70}")
    print(f" 总计：A={counts['A']}  B={counts['B']}  C={counts['C']}  共 {len(results)} 个模板")

    # check matrix
    all_checks = set()
    for r in results:
        all_checks.update(r.checks.keys())

    print(f"\n{'=' * 70}")
    print(" 检查矩阵")
    print("-" * 70)
    for check in sorted(all_checks):
        passed = sum(1 for r in results if r.checks.get(check, False))
        print(f"  {check:<32} {passed}/{len(results)}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="V13 template strict auditor")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of markdown")
    args = parser.parse_args()

    results = audit_all_templates()
    if not results:
        print("No templates found")
        return 1

    if args.json:
        data = [
            {"id": r.template_id, "file": r.file, "grade": r.grade, "checks": r.checks, "issues": r.issues}
            for r in results
        ]
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_report(results)

    # exit non-zero if any C-grade
    if any(r.grade == "C" for r in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

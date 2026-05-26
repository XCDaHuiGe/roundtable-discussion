#!/usr/bin/env python3
"""
圆桌洞见 HTML PPT 质量校验脚本
适配 roundtable-template.html 模板格式

用法：
    python tools/validate_html.py <html_file> [--strict]

检查项：
    - [P0] HTML 结构完整性（</body></html>）
    - [P0] JavaScript 导航逻辑（go()、键盘、滚轮、触摸）
    - [P0] 每页 slide 有 data-title 属性
    - [P0] 第一个 slide 有 active class
    - [P0] 无 emoji
    - [P1] 总页数 30-45 页
    - [P1] CSS 自包含（无外部 @import）
    - [P1] TOC 面板存在
    - [P1] 底部导航栏存在
    - [P1] 发言块结构正确（.sp > .sh + .st）
    - [P1] 碰撞块使用颜色 class
    - [P1] 洞见卡存在
"""

import re
import sys
import io
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


@dataclass
class CheckResult:
    level: str  # P0, P1
    name: str
    passed: bool
    message: str
    details: List[str] = field(default_factory=list)


def check_html_structure(content: str) -> CheckResult:
    """检查 HTML 结构完整性"""
    has_body = '</body>' in content.lower()
    has_html = '</html>' in content.lower()
    if has_body and has_html:
        return CheckResult('P0', 'HTML结构', True, 'HTML 结构完整')
    missing = []
    if not has_body:
        missing.append('</body>')
    if not has_html:
        missing.append('</html>')
    return CheckResult('P0', 'HTML结构', False, f'缺少结束标签: {", ".join(missing)}')


def check_javascript(content: str) -> CheckResult:
    """检查 JavaScript 导航逻辑"""
    has_go = 'function go(' in content
    has_keydown = 'keydown' in content
    has_wheel = 'wheel' in content
    has_touch = 'touchstart' in content and 'touchend' in content
    has_toggle_toc = 'toggleTOC' in content or 'toc-panel' in content

    found = []
    missing = []
    if has_go:
        found.append('go() 函数')
    else:
        missing.append('go() 函数')
    if has_keydown:
        found.append('键盘导航')
    else:
        missing.append('键盘导航')
    if has_wheel:
        found.append('滚轮翻页')
    else:
        missing.append('滚轮翻页')
    if has_touch:
        found.append('触摸滑动')
    else:
        missing.append('触摸滑动')
    if has_toggle_toc:
        found.append('TOC 切换')
    else:
        missing.append('TOC 切换')

    if has_go and has_keydown:
        return CheckResult('P0', 'JavaScript导航', True, f'导航逻辑完整: {", ".join(found)}', found)
    else:
        return CheckResult('P0', 'JavaScript导航', False, f'缺少: {", ".join(missing)}', missing)


def check_data_titles(content: str) -> CheckResult:
    """检查每页 slide 有 data-title 属性"""
    # 支持 <div class="slide ..."> 和 <section class="slide ...">
    slides = re.findall(r'<(?:div|section)[^>]*class="[^"]*slide[^"]*"[^>]*>', content)
    slides_without_title = []
    for slide in slides:
        if 'data-title=' not in slide:
            slides_without_title.append(slide[:80])

    if not slides:
        return CheckResult('P0', 'data-title属性', False, '未找到任何 slide 元素')
    if not slides_without_title:
        return CheckResult('P0', 'data-title属性', True, f'所有 {len(slides)} 页都有 data-title')
    return CheckResult('P0', 'data-title属性', False,
                       f'{len(slides_without_title)} 页缺少 data-title',
                       slides_without_title[:5])


def check_first_slide_active(content: str) -> CheckResult:
    """检查第一个 slide 有 active class"""
    first_slide = re.search(r'<(?:div|section)[^>]*class="[^"]*slide[^"]*"[^>]*>', content)
    if first_slide and 'active' in first_slide.group():
        return CheckResult('P0', '首页active', True, '第一个 slide 有 active class')
    return CheckResult('P0', '首页active', False, '第一个 slide 缺少 active class')


def check_emoji(content: str) -> CheckResult:
    """检查是否有 emoji"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U0001F900-\U0001F9FF"
        "\U00002702-\U000027B0"
        "\U00002600-\U000026FF"
        "]+",
        flags=re.UNICODE
    )
    emojis = emoji_pattern.findall(content)
    allowed = {'⚠', '✓', '✗', '→', '←', '↑', '↓', '·', '•', '—', '–', '"', '"', '\'', '\'', '⚡', '☰'}
    real_emojis = [e for e in emojis if e not in allowed and len(e) <= 4]
    if not real_emojis:
        return CheckResult('P0', '无Emoji', True, '未发现 emoji')
    return CheckResult('P0', '无Emoji', False,
                       f'发现 {len(real_emojis)} 个 emoji', real_emojis[:10])


def check_slide_count(content: str) -> CheckResult:
    """检查总页数 30-45 页"""
    slides = re.findall(r'<(?:div|section)[^>]*class="[^"]*slide[^"]*"[^>]*>', content)
    count = len(slides)
    if 30 <= count <= 45:
        return CheckResult('P1', '页数', True, f'共 {count} 页（符合 30-45 要求）')
    elif count > 0:
        return CheckResult('P1', '页数', False, f'共 {count} 页（要求 30-45 页）')
    else:
        return CheckResult('P1', '页数', False, '未找到 slide 元素')


def check_css_self_contained(content: str) -> CheckResult:
    """检查 CSS 自包含（无外部 @import）"""
    imports = re.findall(r'@import\s+url\([^)]+\)', content)
    external_links = re.findall(r'<link[^>]+href="https?://[^"]+"', content)
    if not imports and not external_links:
        return CheckResult('P1', 'CSS自包含', True, '无外部资源引用')
    issues = imports + external_links
    return CheckResult('P1', 'CSS自包含', False,
                       f'发现 {len(issues)} 处外部引用', issues[:5])


def check_toc_panel(content: str) -> CheckResult:
    """检查 TOC 面板存在"""
    has_toc_html = 'toc-panel' in content or 'tocPanel' in content
    has_toc_js = 'toggleTOC' in content or 'toc-panel' in content
    if has_toc_html and has_toc_js:
        return CheckResult('P1', 'TOC面板', True, 'TOC 面板存在且有切换逻辑')
    elif has_toc_html:
        return CheckResult('P1', 'TOC面板', True, 'TOC 面板 HTML 存在')
    return CheckResult('P1', 'TOC面板', False, '未检测到 TOC 面板')


def check_nav_bar(content: str) -> CheckResult:
    """检查底部导航栏存在"""
    has_nav_bar = 'nav-bar' in content
    has_nav_btn = 'nav-btn' in content
    if has_nav_bar and has_nav_btn:
        return CheckResult('P1', '导航栏', True, '底部导航栏完整')
    elif has_nav_bar:
        return CheckResult('P1', '导航栏', True, '导航栏存在')
    return CheckResult('P1', '导航栏', False, '未检测到底部导航栏')


def check_speech_blocks(content: str) -> CheckResult:
    """检查发言块结构（.sp > .sh + .st）"""
    sp_count = content.count('class="sp"') + content.count("class='sp'")
    # 也检查带额外 class 的情况
    sp_count += len(re.findall(r'class="sp\s', content))

    if sp_count == 0:
        return CheckResult('P1', '发言块', True, '无发言块（可能全碰撞页）')

    sh_count = content.count('class="sh"') + len(re.findall(r'class="sh\s', content))
    st_count = content.count('class="st"') + len(re.findall(r'class="st\s', content))

    if sh_count > 0 and st_count > 0:
        return CheckResult('P1', '发言块', True,
                           f'发言块结构正确: {sp_count} 个 .sp, {sh_count} 个 .sh, {st_count} 个 .st')
    elif sp_count > 0 and st_count > 0:
        return CheckResult('P1', '发言块', True, f'发言块存在: {sp_count} 个 .sp, {st_count} 个 .st')
    return CheckResult('P1', '发言块', False,
                       f'发言块结构不完整: {sp_count} .sp, {sh_count} .sh, {st_count} .st')


def check_collision_blocks(content: str) -> CheckResult:
    """检查碰撞块使用颜色 class"""
    cb_count = content.count('class="cb"') + len(re.findall(r'class="cb\s', content))
    color_classes = ['cb blue', 'cb purple', 'cb orange', 'cb green']
    color_count = sum(content.count(f'class="{c}"') for c in color_classes)

    if cb_count > 0 or color_count > 0:
        total = cb_count + color_count
        return CheckResult('P1', '碰撞块', True,
                           f'碰撞块: {total} 个（其中 {color_count} 个有颜色标记）')
    return CheckResult('P1', '碰撞块', False, '未检测到碰撞块（.cb）')


def check_insight_cards(content: str) -> CheckResult:
    """检查洞见卡存在"""
    has_insight_c = 'insight-c' in content
    has_insight_q = 'insight-q' in content
    if has_insight_c and has_insight_q:
        return CheckResult('P1', '洞见卡', True, '洞见卡结构完整')
    elif has_insight_c:
        return CheckResult('P1', '洞见卡', True, '洞见卡存在')
    return CheckResult('P1', '洞见卡', False, '未检测到洞见卡（.insight-c）')


def check_nav_dots(content: str) -> CheckResult:
    """检查右侧圆点导航"""
    if 'nav-dots' in content and 'nd' in content:
        return CheckResult('P1', '圆点导航', True, '右侧圆点导航存在')
    return CheckResult('P1', '圆点导航', False, '未检测到圆点导航')


def validate_html(file_path: str, strict: bool = False) -> Tuple[List[CheckResult], bool]:
    """执行所有检查"""
    path = Path(file_path)
    if not path.exists():
        print(f"[FAIL] 文件不存在: {file_path}")
        return [], False

    content = path.read_text(encoding='utf-8')

    checks = [
        # P0
        check_html_structure(content),
        check_javascript(content),
        check_data_titles(content),
        check_first_slide_active(content),
        check_emoji(content),
        # P1
        check_slide_count(content),
        check_css_self_contained(content),
        check_toc_panel(content),
        check_nav_bar(content),
        check_nav_dots(content),
        check_speech_blocks(content),
        check_collision_blocks(content),
        check_insight_cards(content),
    ]

    p0_passed = all(c.passed for c in checks if c.level == 'P0')
    if strict:
        all_passed = all(c.passed for c in checks)
        return checks, all_passed
    return checks, p0_passed


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    file_path = sys.argv[1]
    strict = '--strict' in sys.argv

    print(f"\n{'='*60}")
    print(f"圆桌洞见 HTML 校验 {'[严格模式]' if strict else ''}")
    print(f"文件: {file_path}")
    print(f"{'='*60}\n")

    checks, passed = validate_html(file_path, strict)

    for check in checks:
        status = '[PASS]' if check.passed else '[FAIL]'
        level = f'[{check.level}]'
        print(f"{status} {level:4} {check.name}: {check.message}")
        if check.details and not check.passed:
            for detail in check.details[:5]:
                print(f"      - {detail}")

    print(f"\n{'='*60}")
    p0_count = sum(1 for c in checks if c.level == 'P0' and c.passed)
    p0_total = sum(1 for c in checks if c.level == 'P0')
    p1_count = sum(1 for c in checks if c.level == 'P1' and c.passed)
    p1_total = sum(1 for c in checks if c.level == 'P1')

    print(f"P0 检查: {p0_count}/{p0_total} 通过")
    print(f"P1 检查: {p1_count}/{p1_total} 通过")

    if passed:
        print(f"\n[PASS] 校验通过！")
        sys.exit(0)
    else:
        print(f"\n[FAIL] 校验失败，请修复 P0 级问题")
        sys.exit(1)


if __name__ == '__main__':
    main()

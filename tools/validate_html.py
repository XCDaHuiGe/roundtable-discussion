#!/usr/bin/env python3
"""
圆桌洞见 HTML PPT 质量校验脚本
适配 roundtable-template.html + 16 种新模板格式

用法：
    python tools/validate_html.py <html_file> [--strict]
    python tools/validate_html.py output/ --batch [--strict]

检查项：
    - [P0] HTML 结构完整性（</body></html>）
    - [P0] JavaScript 导航逻辑（go()、键盘、滚轮）
    - [P0] 每页 slide 有 data-title 属性
    - [P0] 第一个 slide 有 active class
    - [P0] 无 emoji
    - [P1] 总页数 >= 12 页（建议 30-45 页）
    - [P1] CSS 自包含（无外部 @import，允许 Google Fonts）
    - [P1] 导航组件存在（TOC / 导航栏 / 圆点）
    - [P1] 内容结构完整（发言块 / 碰撞块 / 洞见卡）
    - [P1] 文件大小合理（< 5MB）
"""

import re
import sys
import io
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


@dataclass
class CheckResult:
    level: str  # P0, P1
    name: str
    passed: bool
    message: str
    details: List[str] = field(default_factory=list)


# ─── 模板检测 ──────────────────────────────────────────────

KNOWN_TEMPLATES = {
    'premium-dark': '高端科技杂志风格',
    'v3-magazine': '杂志墨水风格',
    'v2-starry': '深邃星空风格',
    'consulting-report': '咨询报告风格',
    'editorial': '杂志编辑风格',
    'geek-report': '极客风格',
    'clean-review': '简约测评风格',
    'rain-notes': '雨天手记风格',
    'sunrise': '日光风格',
    'pixel-report': '黑底闪光风格',
    'dot-matrix': '点阵编辑风格',
    'dot-matrix-light': '点阵编辑-亮色',
    'shiny-tiles': '闪光瓦片风格',
    'studio-photo': '摄影工作室风格',
    'story-field': '故事集风格',
    'y2k-brand': 'Y2K手册风格',
}


def detect_template(content: str) -> str:
    """检测使用的模板类型"""
    for tid, name in KNOWN_TEMPLATES.items():
        if f'template-{tid}' in content or f'template_{tid}' in content:
            return f'{name} ({tid})'

    if 'roundtable-template' in content:
        return 'roundtable-template (V8)'

    if '{{slides}}' in content:
        return 'adapter 模板'

    if '{{#each' in content:
        return 'handlebars 模板'

    return '未知模板'


# ─── P0 检查 ──────────────────────────────────────────────

def check_html_structure(content: str) -> CheckResult:
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
    has_go = 'function go(' in content
    has_keydown = 'keydown' in content
    has_wheel = 'wheel' in content

    found = []
    missing = []
    if has_go:
        found.append('go()')
    else:
        missing.append('go()')
    if has_keydown:
        found.append('键盘导航')
    else:
        missing.append('键盘导航')
    if has_wheel:
        found.append('滚轮翻页')
    else:
        missing.append('滚轮翻页')

    has_nav = has_go and has_keydown
    if has_nav:
        return CheckResult('P0', 'JavaScript导航', True, f'导航逻辑完整: {", ".join(found)}', found)
    return CheckResult('P0', 'JavaScript导航', False, f'缺少: {", ".join(missing)}', missing)


def check_data_titles(content: str) -> CheckResult:
    slides = re.findall(r'<(?:div|section)[^>]*class="(?:[^"]*\s)?slide(?:\s[^"]*)?"[^>]*>', content)
    slides_without_title = []
    for slide in slides:
        if 'data-title=' not in slide:
            slides_without_title.append(slide[:80])

    if not slides:
        return CheckResult('P0', 'data-title属性', False, '未找到任何 slide 元素')
    if not slides_without_title:
        return CheckResult('P0', 'data-title属性', True, f'所有 {len(slides)} 页都有 data-title')
    return CheckResult('P0', 'data-title属性', False,
                       f'{len(slides_without_title)}/{len(slides)} 页缺少 data-title',
                       slides_without_title[:5])


def check_first_slide_active(content: str) -> CheckResult:
    first_slide = re.search(r'<(?:div|section)[^>]*class="(?:[^"]*\s)?slide(?:\s[^"]*)?"[^>]*>', content)
    if first_slide and 'active' in first_slide.group():
        return CheckResult('P0', '首页active', True, '第一个 slide 有 active class')
    return CheckResult('P0', '首页active', False, '第一个 slide 缺少 active class')


def check_emoji(content: str) -> CheckResult:
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
    allowed = {'⚠', '✓', '✗', '→', '←', '↑', '↓', '·', '•', '—', '–', '"', '"', '\'', '\'', '⚡', '☰', '🖋'}
    real_emojis = [e for e in emojis if e not in allowed and len(e) <= 4]
    if not real_emojis:
        return CheckResult('P0', '无Emoji', True, '未发现 emoji')
    return CheckResult('P0', '无Emoji', False,
                       f'发现 {len(real_emojis)} 个 emoji', real_emojis[:10])


# ─── P1 检查 ──────────────────────────────────────────────

def check_slide_count(content: str) -> CheckResult:
    slides = re.findall(r'<(?:div|section)[^>]*class="(?:[^"]*\s)?slide(?:\s[^"]*)?"[^>]*>', content)
    count = len(slides)
    if count >= 30:
        return CheckResult('P1', '页数', True, f'共 {count} 页（符合 30-45 建议）')
    elif count >= 12:
        return CheckResult('P1', '页数', True, f'共 {count} 页（>=12 合规，建议 30-45）')
    elif count > 0:
        return CheckResult('P1', '页数', False, f'共 {count} 页（最少 12 页）')
    return CheckResult('P1', '页数', False, '未找到 slide 元素')


def check_css_self_contained(content: str) -> CheckResult:
    imports = re.findall(r'@import\s+url\([^)]+\)', content)
    external_links = re.findall(r'<link[^>]+href="(https?://[^"]+)"', content)
    allowed_hosts = ['fonts.googleapis.com', 'fonts.gstatic.com', 'cdn.jsdelivr.net']
    external_issues = []
    for link in external_links:
        if not any(host in link for host in allowed_hosts):
            external_issues.append(link[:80])

    if not imports and not external_issues:
        return CheckResult('P1', 'CSS自包含', True, '无外部资源引用（Google Fonts 允许）')
    issues = imports + external_issues
    return CheckResult('P1', 'CSS自包含', False,
                       f'发现 {len(issues)} 处外部引用', issues[:5])


def check_nav_components(content: str) -> CheckResult:
    """检查导航组件（兼容新旧模板）"""
    has_toc = 'toc-panel' in content or 'tocPanel' in content
    has_nav_bar = 'nav-bar' in content or 'id="nav"' in content
    has_nav_btn = 'nav-btn' in content or 'prevBtn' in content or 'btnPrev' in content
    has_dots = 'nav-dots' in content or 'navDots' in content or 'class="dots"' in content

    found = []
    if has_toc:
        found.append('TOC面板')
    if has_nav_bar:
        found.append('导航栏')
    if has_nav_btn:
        found.append('翻页按钮')
    if has_dots:
        found.append('圆点导航')

    if len(found) >= 2:
        return CheckResult('P1', '导航组件', True, f'导航组件完整: {", ".join(found)}', found)
    elif found:
        return CheckResult('P1', '导航组件', True, f'部分导航组件: {", ".join(found)}', found)
    return CheckResult('P1', '导航组件', False, '未检测到导航组件')


def check_speech_blocks(content: str) -> CheckResult:
    sp_count = content.count('class="sp"') + content.count("class='sp'")
    sp_count += len(re.findall(r'class="sp\s', content))
    # 新模板使用 .speech-block / .speech-card
    sp_count += len(re.findall(r'class="speech-block', content))
    sp_count += len(re.findall(r'class="speech-card', content))
    sp_count += len(re.findall(r'class="stance-item', content))

    if sp_count == 0:
        return CheckResult('P1', '发言块', True, '无发言块（可能全碰撞页）')

    sh_count = content.count('class="sh"') + len(re.findall(r'class="sh\s', content))
    st_count = content.count('class="st"') + len(re.findall(r'class="st\s', content))
    st_count += len(re.findall(r'class="speech-content', content))
    st_count += len(re.findall(r'class="stance-content', content))

    if sh_count > 0 and st_count > 0:
        return CheckResult('P1', '发言块', True,
                           f'发言块结构正确: {sp_count} 个发言块, {sh_count} 个头部, {st_count} 个内容')
    elif sp_count > 0:
        return CheckResult('P1', '发言块', True, f'发言块存在: {sp_count} 个')
    return CheckResult('P1', '发言块', False, f'发言块结构不完整')


def check_collision_blocks(content: str) -> CheckResult:
    cb_count = content.count('class="cb"') + len(re.findall(r'class="cb\s', content))
    color_classes = ['cb blue', 'cb purple', 'cb orange', 'cb green']
    color_count = sum(content.count(f'class="{c}"') for c in color_classes)
    clash_count = content.count('class="clash-round"') + len(re.findall(r'class="clash-round\s', content))
    clash_count += len(re.findall(r'class="clash-block', content))
    clash_count += len(re.findall(r'class="clash-item', content))
    clash_count += len(re.findall(r'class="collision', content))

    total = cb_count + color_count + clash_count
    if total > 0:
        return CheckResult('P1', '碰撞块', True,
                           f'碰撞块: {total} 个（.cb: {cb_count + color_count}, .clash: {clash_count}）')
    return CheckResult('P1', '碰撞块', False, '未检测到碰撞块')


def check_insight_cards(content: str) -> CheckResult:
    has_insight_c = 'insight-c' in content
    has_insight_q = 'insight-q' in content
    has_insight_block = 'insight-block' in content
    has_insight_card = 'insight-card' in content
    has_insight_label = 'insight-label' in content or 'insight-marker' in content

    if (has_insight_c or has_insight_block or has_insight_card) and (has_insight_q or has_insight_label):
        return CheckResult('P1', '洞见卡', True, '洞见卡结构完整')
    elif has_insight_c or has_insight_block or has_insight_card:
        return CheckResult('P1', '洞见卡', True, '洞见卡存在')
    return CheckResult('P1', '洞见卡', False, '未检测到洞见卡')


def check_file_size(file_path: str) -> CheckResult:
    """检查文件大小"""
    size = os.path.getsize(file_path)
    size_kb = size / 1024
    size_mb = size / (1024 * 1024)

    if size_mb > 5:
        return CheckResult('P1', '文件大小', False, f'{size_mb:.1f}MB（超过 5MB 限制）')
    elif size_mb > 2:
        return CheckResult('P1', '文件大小', True, f'{size_mb:.1f}MB（较大，建议 < 2MB）')
    return CheckResult('P1', '文件大小', True, f'{size_kb:.0f}KB')


def check_expert_count(content: str) -> CheckResult:
    """检查专家数量"""
    avatar_count = len(re.findall(r'class="(?:expert-)?avatar', content))
    expert_card_count = len(re.findall(r'class="expert-card', content))

    count = max(avatar_count, expert_card_count)
    if count >= 6:
        return CheckResult('P1', '专家数量', True, f'检测到 {count} 位专家')
    elif count >= 4:
        return CheckResult('P1', '专家数量', True, f'检测到 {count} 位专家（建议 6 位）')
    elif count > 0:
        return CheckResult('P1', '专家数量', False, f'仅检测到 {count} 位专家（建议 6 位）')
    return CheckResult('P1', '专家数量', True, '未检测到专家卡片（可能使用不同结构）')


# ─── 校验主函数 ──────────────────────────────────────────────

def validate_html(file_path: str, strict: bool = False) -> Tuple[List[CheckResult], bool]:
    path = Path(file_path)
    if not path.exists():
        print(f"[FAIL] 文件不存在: {file_path}")
        return [], False

    content = path.read_text(encoding='utf-8')
    template_info = detect_template(content)

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
        check_nav_components(content),
        check_speech_blocks(content),
        check_collision_blocks(content),
        check_insight_cards(content),
        check_file_size(str(file_path)),
        check_expert_count(content),
    ]

    p0_passed = all(c.passed for c in checks if c.level == 'P0')
    if strict:
        all_passed = all(c.passed for c in checks)
        return checks, all_passed
    return checks, p0_passed


def print_result(checks: List[CheckResult], passed: bool, template_info: str = ""):
    for check in checks:
        status = '[PASS]' if check.passed else '[FAIL]'
        level = f'[{check.level}]'
        print(f"{status} {level:4} {check.name}: {check.message}")
        if check.details and not check.passed:
            for detail in check.details[:5]:
                print(f"      - {detail}")

    print(f"\n{'='*60}")
    if template_info:
        print(f"模板: {template_info}")
    p0_count = sum(1 for c in checks if c.level == 'P0' and c.passed)
    p0_total = sum(1 for c in checks if c.level == 'P0')
    p1_count = sum(1 for c in checks if c.level == 'P1' and c.passed)
    p1_total = sum(1 for c in checks if c.level == 'P1')

    print(f"P0 检查: {p0_count}/{p0_total} 通过")
    print(f"P1 检查: {p1_count}/{p1_total} 通过")

    if passed:
        print(f"\n[PASS] 校验通过！")
    else:
        print(f"\n[FAIL] 校验失败，请修复 P0 级问题")


def validate_batch(dir_path: str, strict: bool = False):
    """批量校验目录下所有 HTML 文件"""
    dir_path = Path(dir_path)
    html_files = sorted(dir_path.glob("*.html"))

    if not html_files:
        print(f"目录下没有 HTML 文件: {dir_path}")
        return

    print(f"\n{'='*60}")
    print(f"批量校验: {dir_path}")
    print(f"文件数: {len(html_files)}")
    print(f"模式: {'严格' if strict else '标准'}")
    print(f"{'='*60}\n")

    results = []
    for f in html_files:
        content = f.read_text(encoding='utf-8')
        template_info = detect_template(content)
        checks, passed = validate_html(str(f), strict)

        status = 'PASS' if passed else 'FAIL'
        p0_ok = sum(1 for c in checks if c.level == 'P0' and c.passed)
        p0_all = sum(1 for c in checks if c.level == 'P0')
        p1_ok = sum(1 for c in checks if c.level == 'P1' and c.passed)
        p1_all = sum(1 for c in checks if c.level == 'P1')

        print(f"[{status}] {f.name:<45} P0:{p0_ok}/{p0_all} P1:{p1_ok}/{p1_all} | {template_info}")
        results.append((f.name, passed, checks))

    print(f"\n{'='*60}")
    total = len(results)
    passed_count = sum(1 for _, p, _ in results if p)
    print(f"总计: {passed_count}/{total} 通过")

    if passed_count < total:
        print("\n失败文件:")
        for name, p, checks in results:
            if not p:
                failed = [c.name for c in checks if not c.passed and c.level == 'P0']
                print(f"  - {name}: {', '.join(failed)}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    target = sys.argv[1]
    strict = '--strict' in sys.argv
    batch = '--batch' in sys.argv

    if batch or os.path.isdir(target):
        validate_batch(target, strict)
        return

    file_path = target

    print(f"\n{'='*60}")
    print(f"圆桌洞见 HTML 校验 {'[严格模式]' if strict else ''}")
    print(f"文件: {file_path}")
    print(f"{'='*60}\n")

    content = Path(file_path).read_text(encoding='utf-8')
    template_info = detect_template(content)
    checks, passed = validate_html(file_path, strict)
    print_result(checks, passed, template_info)

    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()

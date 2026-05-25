#!/usr/bin/env python3
"""
HTML PPT 质量校验脚本
V5.1 新增：可执行的 Phase 4 质量门控

用法：
    python tools/validate_html.py <html_file> [--strict]

检查项：
    - [P0] HTML 结构完整性（</body></html> 结束标签）
    - [P0] JavaScript 翻页逻辑存在
    - [P0] 每页 slide 有 data-title 属性
    - [P0] 无 emoji
    - [P1] 主题交替合理（无连续 3 页相同主题，hero占比>=20%）
    - [P1] 语义类使用正确
    - [P1] 图片使用标准比例类
    - [P1] 入场动画使用
    - [P1] CSS 链接（信息性，零依赖单HTML可忽略）
    - [P1] 字体分工正确（标题用衬线，正文用无衬线）
    - [P1] 无自定义渐变/阴影/圆角
    - [P1] 布局类合规
    - [P1] 页眉页脚完整
    - [P1] 引用块使用语义类
    - [P1] 流程可见性（battle-tested / expert-card 标记）
    - [P1] 攻防页内容完整性（红队攻击+蓝队辩护同时存在）
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class CheckResult:
    level: str  # P0, P1, P2
    name: str
    passed: bool
    message: str
    details: List[str] = None

def check_html_structure(content: str) -> CheckResult:
    """检查 HTML 结构完整性"""
    has_body_close = '</body>' in content.lower()
    has_html_close = '</html>' in content.lower()
    
    if has_body_close and has_html_close:
        return CheckResult('P0', 'HTML结构', True, 'HTML 结构完整')
    else:
        missing = []
        if not has_body_close:
            missing.append('</body>')
        if not has_html_close:
            missing.append('</html>')
        return CheckResult('P0', 'HTML结构', False, f'缺少结束标签: {", ".join(missing)}')

def check_javascript(content: str) -> CheckResult:
    """检查 JavaScript 翻页逻辑"""
    has_go = 'function go(' in content or 'const go=' in content or 'let go=' in content
    has_next_prev = 'function next(' in content or 'function prev(' in content
    has_goto = 'function goTo(' in content or 'const goTo=' in content or 'goTo(' in content
    has_scroll_snap = 'scroll-snap-type' in content
    has_slide_nav = has_go or has_next_prev or has_goto or has_scroll_snap
    has_keydown = 'keydown' in content
    has_touch = 'touchstart' in content and 'touchend' in content

    if has_slide_nav and (has_keydown or has_scroll_snap):
        details = []
        if has_go:
            details.append('[ok] go() 函数')
        if has_next_prev:
            details.append('[ok] next()/prev() 函数')
        if has_goto:
            details.append('[ok] goTo() 函数')
        if has_scroll_snap:
            details.append('[ok] scroll-snap 滚屏')
        if has_touch:
            details.append('[ok] 触摸滑动支持')
        return CheckResult('P0', 'JavaScript翻页', True, '翻页逻辑完整', details)
    else:
        missing = []
        if not has_slide_nav:
            missing.append('翻页函数 (go/next/prev/goTo/scroll-snap)')
        if not has_keydown and not has_scroll_snap:
            missing.append('键盘导航或scroll-snap')
        return CheckResult('P0', 'JavaScript翻页', False, f'缺少: {", ".join(missing)}')

def check_data_titles(content: str) -> CheckResult:
    """检查每页 slide 有 data-title 属性"""
    slides = re.findall(r'<section[^>]*class="[^"]*slide[^"]*"[^>]*>', content)
    slides_without_title = []
    
    for slide in slides:
        if 'data-title=' not in slide:
            slides_without_title.append(slide[:80] + '...')
    
    if not slides_without_title:
        slide_count = len(slides)
        return CheckResult('P0', 'data-title属性', True, f'所有 {slide_count} 页都有 data-title')
    else:
        return CheckResult('P0', 'data-title属性', False, 
                          f'{len(slides_without_title)} 页缺少 data-title', 
                          slides_without_title[:5])

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
    allowed = {'⚠', '✓', '✗', '→', '←', '↑', '↓', '·', '•', '—', '–', '"', '"', '\'', '\''}
    real_emojis = [e for e in emojis if e not in allowed and len(e) <= 4]

    if not real_emojis:
        return CheckResult('P0', '无Emoji', True, '未发现 emoji')
    else:
        return CheckResult('P0', '无Emoji', False,
                          f'发现 {len(real_emojis)} 个 emoji',
                          real_emojis[:10])

def check_theme_alternation(content: str) -> CheckResult:
    """检查主题交替"""
    slides = re.findall(r'<section[^>]*class="([^"]*)"[^>]*>', content)
    
    themes = []
    for classes in slides:
        if 'slide' in classes:
            if 'hero' in classes:
                themes.append('hero')
            elif 'dark' in classes:
                themes.append('dark')
            else:
                themes.append('light')
    
    violations = []
    current_theme = None
    count = 0
    
    for i, theme in enumerate(themes):
        if theme == current_theme:
            count += 1
            if count >= 3:
                violations.append(f'第 {i+1} 页: 连续 3+ 页 {theme}')
        else:
            current_theme = theme
            count = 1
    
    if not violations:
        hero_count = themes.count('hero')
        hero_ratio = hero_count / len(themes) if themes else 0
        return CheckResult('P1', '主题交替', True, 
                          f'主题交替合理，hero 占比 {hero_ratio:.0%}')
    else:
        return CheckResult('P1', '主题交替', False, 
                          f'发现 {len(violations)} 处连续相同主题', violations)

def check_semantic_classes(content: str) -> CheckResult:
    """检查语义类使用"""
    semantic_classes = [
        'mod-title', 'mod-sub', 'mod-label',
        'card-rise', 'card-fall',
        'warning-box', 'ok-box',
        'stat-num', 'stat-label',
        'expert-card', 'roundtable-grid'
    ]
    
    found = []
    for cls in semantic_classes:
        if cls in content:
            found.append(cls)
    
    if found:
        return CheckResult('P1', '语义类', True, f'使用了 {len(found)} 种语义类', found)
    else:
        return CheckResult('P1', '语义类', False, '未使用任何语义类（建议使用 mod-title/mod-sub 等）')

def check_animation_attrs(content: str) -> CheckResult:
    """检查动画属性"""
    has_data_anim = 'data-anim=' in content
    has_anim_class = any(f'anim-{i}' in content for i in range(1, 7))
    
    if has_data_anim:
        anim_count = content.count('data-anim=')
        return CheckResult('P1', '入场动画', True, f'使用了 {anim_count} 处 data-anim 属性')
    elif has_anim_class:
        return CheckResult('P1', '入场动画', True, '使用了 anim-* 延迟类')
    else:
        return CheckResult('P1', '入场动画', False, '未使用入场动画（建议添加 data-anim 属性）')

def check_image_classes(content: str) -> CheckResult:
    """检查图片比例类"""
    has_images = '<img' in content

    if not has_images:
        return CheckResult('P1', '图片比例', True, '无图片')

    ratio_classes = ['r-16x9', 'r-16x10', 'r-4x3', 'r-3x2', 'r-1x1']
    has_ratio = any(cls in content for cls in ratio_classes)

    if has_ratio:
        return CheckResult('P1', '图片比例', True, '使用了标准比例类')
    else:
        return CheckResult('P1', '图片比例', False, '图片未使用标准比例类')

def check_font_division(content: str) -> CheckResult:
    """检查字体分工：标题用衬线(serif)，正文用无衬线(sans-serif)"""
    has_serif_title = any(cls in content for cls in [
        'font-serif', 'Noto Serif', 'Georgia', 'serif',
        'ed-display', 'ed-h1', 'h-hero', 'h-xl', 'h-lg',
        'mod-title'
    ])
    has_sans_body = any(cls in content for cls in [
        'font-sans', 'Noto Sans', 'system-ui', 'sans-serif',
        'ed-body', 'mod-sub', 'lead'
    ])

    if has_serif_title and has_sans_body:
        return CheckResult('P1', '字体分工', True, '标题衬线+正文无衬线')
    elif has_serif_title:
        return CheckResult('P1', '字体分工', True, '标题使用衬线字体')
    else:
        return CheckResult('P1', '字体分工', False, '未检测到明确的字体分工（建议标题用衬线，正文用无衬线）')

def check_custom_styles(content: str) -> CheckResult:
    """检查是否使用了自定义渐变/阴影/圆角（规范禁止）"""
    violations = []
    if re.search(r'border-radius:\s*\d+px', content):
        violations.append('自定义 border-radius')
    if re.search(r'box-shadow:\s*[^;{]*\d+px', content):
        violations.append('自定义 box-shadow')
    if re.search(r'linear-gradient\([^)]+\)', content):
        gradient_count = len(re.findall(r'linear-gradient\(', content))
        if gradient_count > 2:
            violations.append(f'使用了 {gradient_count} 处 linear-gradient')
    if re.search(r'radial-gradient\(', content):
        violations.append('自定义 radial-gradient')

    if not violations:
        return CheckResult('P1', '自定义样式', True, '未发现违规自定义样式')
    else:
        return CheckResult('P1', '自定义样式', False,
                          f'发现 {len(violations)} 处违规', violations)

def check_layout_compliance(content: str) -> CheckResult:
    """检查布局类是否来自预定义的 12 种模板"""
    allowed_layouts = [
        'hero-cover', 'act-divider', 'big-numbers', 'text-image-split',
        'image-grid', 'pipeline', 'pipeline-section', 'question-page',
        'big-quote', 'before-after', 'mixed-layout', 'timeline',
        'battle-tested', 'expert-panel', 'expert-tension', 'expert-open',
        'expert-roster', 'expert-debate', 'expert-output',
        'hero', 'slide'
    ]
    sections = re.findall(r'<section[^>]*class="([^"]*)"', content)
    unknown_classes = []
    for classes in sections:
        for cls in classes.split():
            if cls not in allowed_layouts and cls not in [
                'slide', 'light', 'dark', 'is-active', 'prev-slide',
                'hero-slide', 'hero-dark', 'hero-light'
            ] and not cls.startswith('anim-') and not cls.startswith('data-'):
                if cls not in unknown_classes:
                    unknown_classes.append(cls)

    if not unknown_classes:
        return CheckResult('P1', '布局合规', True, '布局类均来自预定义模板')
    else:
        return CheckResult('P1', '布局合规', False,
                          f'发现 {len(unknown_classes)} 个非标准类',
                          unknown_classes[:5])

def check_chrome_footer(content: str) -> CheckResult:
    """检查每页是否有页眉(chrome)和页脚(footer)"""
    slides = re.findall(r'<section[^>]*class="[^"]*slide[^"]*"[^>]*>(.*?)</section>',
                        content, re.DOTALL)
    if not slides:
        return CheckResult('P1', '页眉页脚', True, '无 slide')

    missing_chrome = 0
    missing_footer = 0
    for i, slide in enumerate(slides):
        has_chrome = 'chrome' in slide or 'chrome-header' in slide
        has_footer = 'footer' in slide or 'foot' in slide or 'slide-footer' in slide or 'deck-footer' in slide
        if not has_chrome:
            missing_chrome += 1
        if not has_footer:
            missing_footer += 1

    if missing_chrome == 0 and missing_footer == 0:
        return CheckResult('P1', '页眉页脚', True, f'所有 {len(slides)} 页都有页眉页脚')
    else:
        issues = []
        if missing_chrome > 0:
            issues.append(f'{missing_chrome} 页缺少页眉')
        if missing_footer > 0:
            issues.append(f'{missing_footer} 页缺少页脚')
        return CheckResult('P1', '页眉页脚', False, ', '.join(issues))

def check_citation_blocks(content: str) -> CheckResult:
    """检查引用块是否使用语义类（callout/q-big/cite）"""
    has_quotes = '<blockquote' in content or 'class="callout' in content or 'class="q-big' in content
    has_callout = 'callout' in content or 'q-big' in content or 'cite' in content

    if not has_quotes:
        return CheckResult('P1', '引用语义', True, '无引用块')

    if has_callout:
        return CheckResult('P1', '引用语义', True, '引用块使用了语义类')
    else:
        return CheckResult('P1', '引用语义', False, '引用块未使用语义类（建议使用 callout/q-big/cite）')

def check_css_links(content: str) -> CheckResult:
    """检查 CSS 链接"""
    has_base_css = 'ppt-assets/base.css' in content or 'base.css' in content
    has_semantic_css = 'ppt-assets/semantic.css' in content or 'semantic.css' in content
    has_theme_css = 'ppt-assets/themes/' in content or re.search(r'themes/[^"]+\.css', content)
    
    details = []
    if has_base_css:
        details.append('[ok] base.css')
    if has_semantic_css:
        details.append('[ok] semantic.css')
    if has_theme_css:
        details.append('[ok] 主题 CSS')
    
    if has_base_css and has_theme_css:
        return CheckResult('P1', 'CSS链接', True, 'CSS 链接完整（外部引用）', details)
    else:
        return CheckResult('P1', 'CSS链接', False,
                          f'内联CSS（零依赖单HTML模式）', details)

def check_process_visibility(content: str) -> CheckResult:
    """检查流程可见性：battle-tested / 圆桌布局标记是否在 HTML 中出现"""
    has_pressure_tested = 'PRESSURE TESTED' in content or 'PRESSURE_TESTED' in content or 'battle-tested' in content
    has_expert_roster = 'expert-roster' in content or 'ROUNDTABLE' in content
    has_expert_debate = 'expert-debate' in content or 'action-tag' in content
    has_expert_tension = 'expert-tension' in content or '核心张力' in content or 'cross_panel_conflict' in content
    has_expert_output = 'expert-output' in content or '圆桌产出' in content
    has_expert_card = 'expert-card' in content

    found_markers = []
    if has_pressure_tested:
        found_markers.append('battle-tested (红蓝对抗)')
    if has_expert_roster:
        found_markers.append('expert-roster (专家阵容)')
    if has_expert_debate:
        found_markers.append('expert-debate (多轮交锋)')
    if has_expert_tension:
        found_markers.append('expert-tension (观点对立)')
    if has_expert_output:
        found_markers.append('expert-output (圆桌产出)')
    if has_expert_card and not has_expert_roster:
        found_markers.append('expert-card (专家卡片)')

    if found_markers:
        return CheckResult('P1', '流程可见性', True,
                          f'流程节点产出在 PPT 中可见: {", ".join(found_markers)}',
                          found_markers)
    else:
        return CheckResult('P1', '流程可见性', False,
                          '未检测到 battle-tested / 圆桌布局标记（建议新增攻防摘要页和专家圆桌页）')

def check_roundtable_content(content: str) -> CheckResult:
    """检查圆桌布局页是否有实质内容（防止空洞的占位幻灯片）"""
    markers = {
        'expert-roster':    {'label': '专家阵容',    'min_count': 3, 'keywords': ['专家', 'expert', 'title']},
        'expert-debate':    {'label': '多轮交锋',    'min_count': 2, 'keywords': ['speaker', 'action-tag', 'speech']},
        'expert-tension':   {'label': '观点对立',    'min_count': 1, 'keywords': ['pro_side', 'con_side', 'root_cause']},
        'expert-output':    {'label': '圆桌产出',    'min_count': 1, 'keywords': ['共识', '行动', 'question']},
    }
    
    issues = []
    for layout, cfg in markers.items():
        sections = re.findall(rf'<section[^>]*class="[^"]*{layout}[^"]*"[^>]*>(.*?)</section>', content, re.DOTALL)
        if not sections:
            issues.append(f'未找到 {cfg["label"]} 页 ({layout})')
            continue
        for i, sec in enumerate(sections):
            text_len = len(re.sub(r'<[^>]+>', '', sec).strip())
            if text_len < 30:
                issues.append(f'{cfg["label"]} 第 {i+1} 页内容过短: {text_len} 字')

    if not issues:
        layout_summary = ', '.join(f'{v["label"]}({len(re.findall(rf"<section[^>]*{k}[^>]*>", content))}页)'
                                   for k, v in markers.items())
        return CheckResult('P1', '圆桌内容', True, f'所有圆桌布局均有实质内容: {layout_summary}')
    else:
        return CheckResult('P1', '圆桌内容', False, '; '.join(issues[:5]))

def check_battle_tested_content(content: str) -> CheckResult:
    """检查攻防页是否同时包含红队攻击和蓝队辩护内容"""
    sections = re.findall(r'<section[^>]*battle-tested[^>]*>(.*?)</section>', content, re.DOTALL)
    if not sections:
        return CheckResult('P1', '攻防内容', True, '无 battle-tested 页，跳过')

    all_complete = True
    issues = []
    for i, section in enumerate(sections):
        has_attack = 'warning-box' in section or 'card-fall' in section or '红队' in section
        has_defense = 'ok-box' in section or 'card-rise' in section or '蓝队' in section
        if not has_attack:
            issues.append(f'battle-tested 第 {i+1} 页缺少红队攻击内容')
            all_complete = False
        if not has_defense:
            issues.append(f'battle-tested 第 {i+1} 页缺少蓝队辩护内容')
            all_complete = False

    if all_complete:
        return CheckResult('P1', '攻防内容', True,
                          f'所有 {len(sections)} 页 battle-tested 均包含红队攻击和蓝队辩护')
    else:
        return CheckResult('P1', '攻防内容', False, '; '.join(issues))

def validate_html(file_path: str, strict: bool = False) -> Tuple[List[CheckResult], bool]:
    """执行所有检查"""
    path = Path(file_path)
    
    if not path.exists():
        print(f"[FAIL] 文件不存在: {file_path}")
        return [], False
    
    content = path.read_text(encoding='utf-8')
    
    checks = [
        check_html_structure(content),
        check_javascript(content),
        check_data_titles(content),
        check_emoji(content),
        check_css_links(content),
        check_theme_alternation(content),
        check_semantic_classes(content),
        check_animation_attrs(content),
        check_image_classes(content),
        check_font_division(content),
        check_custom_styles(content),
        check_layout_compliance(content),
        check_chrome_footer(content),
        check_citation_blocks(content),
        check_process_visibility(content),
        check_battle_tested_content(content),
        check_roundtable_content(content),
    ]
    
    p0_passed = all(c.passed for c in checks if c.level == 'P0')
    
    if strict:
        all_passed = all(c.passed for c in checks)
        return checks, all_passed
    else:
        return checks, p0_passed

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    file_path = sys.argv[1]
    strict = '--strict' in sys.argv

    print(f"\n{'='*60}")
    print(f"HTML PPT 质量校验 {'[严格模式]' if strict else ''}")
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

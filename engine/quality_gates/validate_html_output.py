# -*- coding: utf-8 -*-
"""
HTML 输出质量门

验证 HTML 输出满足质量门要求：
1. 单页高度：每个 slide/section 固定 100vh
2. 内部滚动：不允许任何内部滚动（overflow-y: auto/scroll）
3. 导航唯一：只有一套 go()、wheelTimer、nav dots
4. 内容容量：文本超出视口时必须拆页
5. 移动端：无横向溢出，按钮和文字不重叠
6. 页面完整：slide 数、nav dot 数、进度条状态一致
"""
from __future__ import annotations

import re
from typing import TypedDict


class QualityError(TypedDict):
    """质量错误"""
    level: str  # "error" 或 "warning"
    code: str   # 错误代码
    message: str  # 错误描述


class ValidationResult(TypedDict):
    """验证结果"""
    ok: bool
    errors: list[QualityError]


def validate_html_output(html: str) -> ValidationResult:
    """
    验证 HTML 输出满足质量门要求。
    
    Args:
        html: HTML 字符串
        
    Returns:
        {"ok": bool, "errors": [{"level": str, "code": str, "message": str}]}
    """
    errors: list[QualityError] = []
    
    # 1. 检查内部滚动
    _check_internal_scroll(html, errors)
    
    # 2. 检查导航唯一性
    _check_navigation_uniqueness(html, errors)
    
    # 3. 检查页面完整性
    _check_page_integrity(html, errors)
    
    # 4. 检查单页高度
    _check_page_height(html, errors)
    
    # 5. 检查移动端横向溢出
    _check_mobile_overflow(html, errors)
    
    return {"ok": not any(e["level"] == "error" for e in errors), "errors": errors}


def _check_internal_scroll(html: str, errors: list[QualityError]) -> None:
    """检查不允许的内部滚动"""
    # 检查 overflow-y: auto/scroll
    if re.search(r"overflow-y\s*:\s*(auto|scroll)", html, re.IGNORECASE):
        errors.append({
            "level": "error",
            "code": "internal_scroll_y",
            "message": "overflow-y: auto/scroll 不允许出现，会导致内部滚动"
        })
    
    # 检查 .slide 或 .section 中的 overflow: auto/scroll
    # 匹配 .slide{...} 或 .section{...} 中的 overflow
    slide_section_styles = re.findall(
        r'\.(?:slide|section)\s*\{([^}]+)\}',
        html,
        re.IGNORECASE | re.DOTALL
    )
    
    for style_block in slide_section_styles:
        if re.search(r"overflow\s*:\s*(auto|scroll)", style_block, re.IGNORECASE):
            errors.append({
                "level": "error",
                "code": "internal_scroll_in_slide",
                "message": ".slide 或 .section 中不允许 overflow: auto/scroll"
            })
            break


def _check_navigation_uniqueness(html: str, errors: list[QualityError]) -> None:
    """检查导航逻辑唯一性"""
    # 检查 go() 函数只出现一次
    go_count = len(re.findall(r'\bfunction\s+go\s*\(', html))
    if go_count == 0:
        errors.append({
            "level": "error",
            "code": "missing_go_function",
            "message": "缺少 go() 导航函数"
        })
    elif go_count > 1:
        errors.append({
            "level": "error",
            "code": "duplicate_go_function",
            "message": f"go() 函数出现 {go_count} 次，应只出现一次"
        })
    
    # 检查 wheelTimer 只出现一次
    wheel_timer_count = html.count("wheelTimer")
    if wheel_timer_count == 0:
        errors.append({
            "level": "error",
            "code": "missing_wheel_timer",
            "message": "缺少 wheelTimer 节流变量"
        })
    elif wheel_timer_count > 1:
        # wheelTimer 通常会出现多次（声明、判断、赋值），这里只检查声明次数
        wheel_timer_declare = len(re.findall(r'let\s+wheelTimer\s*=', html))
        if wheel_timer_declare > 1:
            errors.append({
                "level": "error",
                "code": "duplicate_wheel_timer",
                "message": f"wheelTimer 声明 {wheel_timer_declare} 次，应只声明一次"
            })


def _check_page_integrity(html: str, errors: list[QualityError]) -> None:
    """检查页面完整性：slide 数 == nav dot 数"""
    # 统计 slide 数量
    slide_count = len(re.findall(r'<section\s+class="slide(?:\s+visible)?"', html))
    
    # 统计 nav dot 数量（匹配 class="nav-dot" 或 class="nav-dot active" 等）
    nav_dot_count = len(re.findall(r'class="nav-dot(?:\s+\w+)*"', html))
    
    if slide_count == 0:
        errors.append({
            "level": "error",
            "code": "no_slides",
            "message": "未找到任何 slide 页面"
        })
    elif nav_dot_count == 0:
        errors.append({
            "level": "error",
            "code": "no_nav_dots",
            "message": "未找到任何导航点"
        })
    elif slide_count != nav_dot_count:
        errors.append({
            "level": "error",
            "code": "slide_nav_dot_mismatch",
            "message": f"slide 数量 ({slide_count}) 与 nav dot 数量 ({nav_dot_count}) 不一致"
        })
    
    # 检查初始可见页面
    if slide_count > 0 and html.count('class="slide visible"') != 1:
        errors.append({
            "level": "error",
            "code": "initial_visible_slide",
            "message": "必须有且只有一个初始可见的 slide"
        })


def _check_page_height(html: str, errors: list[QualityError]) -> None:
    """检查单页高度设置"""
    # 移除空白字符后检查
    compact = re.sub(r'\s+', '', html)
    
    # 检查 .slide 是否定义了 height:100vh（不包括 min-height 或 max-height）
    if '.slide{height:100vh' not in compact:
        # 尝试更宽松的匹配，但要排除 min-height 和 max-height
        # 使用正则确保 height 前面不是 min- 或 max-
        if not re.search(r'\.slide\s*\{[^}]*[^-]height\s*:\s*100vh', html, re.IGNORECASE):
            # 再检查是否有 height:100vh 在 .slide 的样式块中
            slide_styles = re.findall(r'\.slide\s*\{([^}]+)\}', html, re.IGNORECASE | re.DOTALL)
            has_height_100vh = False
            for style in slide_styles:
                # 检查是否有 height: 100vh（不包括 min-height 或 max-height）
                if re.search(r'(?<![a-z-])height\s*:\s*100vh', style, re.IGNORECASE):
                    has_height_100vh = True
                    break
            if not has_height_100vh:
                errors.append({
                    "level": "error",
                    "code": "missing_slide_height",
                    "message": ".slide 必须定义 height: 100vh"
                })
    
    # 检查 .slide 是否定义了 overflow:hidden
    if 'overflow:hidden' not in compact:
        # 尝试更宽松的匹配
        if not re.search(r'\.slide\s*\{[^}]*overflow\s*:\s*hidden', html, re.IGNORECASE):
            errors.append({
                "level": "warning",
                "code": "missing_overflow_hidden",
                "message": ".slide 建议定义 overflow: hidden 以防止内部滚动"
            })


def _check_mobile_overflow(html: str, errors: list[QualityError]) -> None:
    """检查移动端横向溢出"""
    # 检查是否有横向滚动的样式
    if re.search(r"overflow-x\s*:\s*(auto|scroll)", html, re.IGNORECASE):
        errors.append({
            "level": "warning",
            "code": "horizontal_scroll",
            "message": "overflow-x: auto/scroll 可能导致移动端横向滚动"
        })
    
    # 检查是否有 viewport meta 标签
    if '<meta name="viewport"' not in html:
        errors.append({
            "level": "warning",
            "code": "missing_viewport",
            "message": "缺少 viewport meta 标签，移动端可能显示异常"
        })
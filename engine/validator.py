# -*- coding: utf-8 -*-
"""圆桌会议HTML验证器 - 自动检查生成的HTML是否符合标准"""

import re
from typing import Dict, List, Tuple


class HTMLValidator:
    """HTML验证器"""
    
    def __init__(self, html_content: str):
        self.html = html_content
        self.errors = []
        self.warnings = []
    
    def validate_structure(self) -> bool:
        """验证HTML结构"""
        # 检查slides
        slide_count = len(re.findall(r'<div class="slide', self.html))
        active_count = len(re.findall(r'class="slide[^"]*active', self.html))
        
        if slide_count == 0:
            self.errors.append("没有找到任何slide")
            return False
        
        if active_count != 1:
            self.errors.append(f"active slide数量错误：{active_count}（应为1）")
            return False
        
        if slide_count < 5:
            self.warnings.append(f"slide数量过少：{slide_count}")
        
        return True
    
    def validate_js(self) -> bool:
        """验证JS完整性"""
        js_checks = {
            "go() function": r'function go\(n\)',
            "go(0) init": r'go\(0\)',
            "querySelectorAll": r'querySelectorAll',
            "classList.remove": r'classList\.remove',
            "classList.add": r'classList\.add',
            "wheel event": r'addEventListener\("wheel"',
            "keyboard event": r'addEventListener\("keydown"'
        }
        
        all_pass = True
        for name, pattern in js_checks.items():
            if not re.search(pattern, self.html):
                self.errors.append(f"JS缺失：{name}")
                all_pass = False
        
        return all_pass
    
    def validate_css(self) -> bool:
        """验证CSS完整性"""
        css_checks = {
            "display:none": r'\.slide\{[^}]*display:none',
            "display:flex": r'\.slide\.active\{[^}]*display:flex',
            "font system": r'IBM Plex Mono|Noto Serif SC',
            "color system": r'--ink:|#[0a]{6}'
        }
        
        all_pass = True
        for name, pattern in css_checks.items():
            if not re.search(pattern, self.html):
                self.errors.append(f"CSS缺失：{name}")
                all_pass = False
        
        return all_pass
    
    def validate_components(self) -> bool:
        """验证组件完整性"""
        component_checks = {
            "发言块": r'class="sp"',
            "碰撞块": r'class="cb"',
            "洞见卡": r'class="insight-c"',
            "TOC": r'toc-panel',
            "进度条": r'progress-bar',
            "导航栏": r'nav-bar'
        }
        
        all_pass = True
        for name, pattern in component_checks.items():
            if not re.search(pattern, self.html):
                self.warnings.append(f"组件缺失：{name}")
        
        return all_pass
    
    def validate_animations(self) -> bool:
        """验证动画属性"""
        anim_count = len(re.findall(r'data-anim', self.html))
        if anim_count == 0:
            self.warnings.append("没有找到data-anim属性")
            return False
        return True
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """执行所有验证"""
        results = [
            self.validate_structure(),
            self.validate_js(),
            self.validate_css(),
            self.validate_components(),
            self.validate_animations()
        ]
        
        is_valid = all(results) and len(self.errors) == 0
        return is_valid, self.errors, self.warnings


def validate_html_file(filepath: str) -> Tuple[bool, List[str], List[str]]:
    """验证HTML文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    validator = HTMLValidator(html)
    return validator.validate_all()


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    import sys
    if len(sys.argv) != 2:
        print("Usage: python validator.py <html_file>")
        sys.exit(1)
    
    is_valid, errors, warnings = validate_html_file(sys.argv[1])
    
    print(f"验证结果：{'PASS' if is_valid else 'FAIL'}")
    
    if errors:
        print("\n错误：")
        for e in errors:
            print(f"  ❌ {e}")
    
    if warnings:
        print("\n警告：")
        for w in warnings:
            print(f"  ⚠️ {w}")
    
    sys.exit(0 if is_valid else 1)
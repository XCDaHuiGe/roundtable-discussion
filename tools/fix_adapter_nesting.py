# -*- coding: utf-8 -*-
"""修复适配器移除双重嵌套结构"""

import re
from pathlib import Path

ENGINE_DIR = Path(__file__).parent.parent / "engine"
ADAPTER_FILE = ENGINE_DIR / "render_adapter.py"

def fix_adapter():
    content = ADAPTER_FILE.read_text(encoding='utf-8')
    original = content
    
    # 移除 adapt_to_geek_report 中的 .inner > .slides 嵌套
    # 模式：<div class="slide" id="sX">\n  <div class="inner">\n    <div class="slides">\n      <div class="slide" id="sX-1">
    # 替换为：<div class="slide" id="sX">
    
    # 修复 geek_report
    pattern1 = r'<div class="slide" id="s\d+">\s*\n\s*<div class="inner">\s*\n\s*<div class="slides">\s*\n\s*<div class="slide" id="s\d+-\d+">'
    replacement1 = '<div class="slide">'
    content = re.sub(pattern1, replacement1, content)
    
    # 修复结尾标签
    pattern2 = r'</div>\s*\n\s*</div>\s*\n\s*</div>\s*\n\s*</div>'
    replacement2 = '</div>'
    content = re.sub(pattern2, replacement2, content)
    
    # 更具体的修复：移除 .inner 和 .slides 的嵌套
    # 查找并替换
    content = content.replace('''
<div class="slide" id="s1">
  <div class="inner">
    <div class="slides">
      <div class="slide" id="s1-1">''', '''
<div class="slide">''')
    
    content = content.replace('''
      </div>
    </div>
  </div>
</div>''', '''
</div>''')
    
    # 通用模式修复
    content = re.sub(
        r'<div class="slide" id="s\d+">\s*<div class="inner">\s*<div class="slides">\s*<div class="slide"[^>]*>',
        '<div class="slide">',
        content
    )
    
    content = re.sub(
        r'</div>\s*</div>\s*</div>\s*</div>',
        '</div>',
        content
    )
    
    if content != original:
        ADAPTER_FILE.write_text(content, encoding='utf-8')
        print("✓ Fixed render_adapter.py")
        return True
    else:
        print("  No changes needed")
        return False

if __name__ == "__main__":
    fix_adapter()
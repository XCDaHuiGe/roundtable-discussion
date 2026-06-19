# -*- coding: utf-8 -*-
"""修复模板容器结构 - 确保{{slides}}在正确的容器中"""

import os
import re
from pathlib import Path

ENGINE_DIR = Path(__file__).parent.parent / "engine"

CONTAINER_WRAPPER = '''<div class="frame">
  <div class="inner">
    <div class="slides">
{{slides}}
    </div>
  </div>
</div>'''

def fix_template_container(file_path: Path) -> bool:
    content = file_path.read_text(encoding='utf-8')
    original = content
    
    if '{{slides}}' not in content:
        return False
    
    if '<div class="frame">' in content and '<div class="slides">' in content:
        return False
    
    pattern = r'<div id="progress"[^>]*>.*?</div>\s*{{slides}}'
    replacement = f'<div id="progress" style="width: 0%;"></div>\n{CONTAINER_WRAPPER}'
    content = re.sub(pattern, replacement, content)
    
    if '{{slides}}' in content and '<div class="frame">' not in content:
        content = content.replace('{{slides}}', CONTAINER_WRAPPER.replace('{{slides}}', '{{slides}}'))
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return True
    return False

def batch_fix():
    templates = list(ENGINE_DIR.glob('template-*.html'))
    print(f"Found {len(templates)} templates")
    print("=" * 60)
    
    fixed = 0
    for t in sorted(templates):
        if fix_template_container(t):
            fixed += 1
            print(f"✓ Fixed: {t.name}")
        else:
            print(f"  Skip: {t.name} (already has container or no {{slides}})")
    
    print("=" * 60)
    print(f"Fixed {fixed}/{len(templates)} templates")

if __name__ == "__main__":
    batch_fix()
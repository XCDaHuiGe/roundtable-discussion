# -*- coding: utf-8 -*-
"""批量修复模板禁止内部滚动"""

import os
import re

ENGINE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")

def fix_template(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    content = re.sub(r'overflow-y:\s*auto', 'overflow:hidden', content)
    content = re.sub(r'overflow-y:\s*scroll', 'overflow:hidden', content)
    
    if 'overflow:hidden' in content and '.slide' in content:
        if not re.search(r'\.slide[^{]*{[^}]*overflow:hidden', content):
            content = re.sub(r'(\.slide\s*{[^}]*)(overflow[^;]*;)', 
                           r'\1overflow:hidden;', content)
    
    wheel_pattern = r'var\s+wheelTimer[^;]*;\s*deck\.addEventListener\s*\(\s*"wheel"\s*,\s*function\s*\(\s*e\s*\)\s*{[^}]*var\s+sl\s*=[^;]*;[^}]*if\s*\([^}]*\)\s*{[^}]*wheelTimer[^;]*;[^}]*go\s*\([^)]*\)[^}]*}[^}]*e\.preventDefault\s*\(\s*\)[^}]*}\s*else[^}]*}\s*,\s*{[^}]*passive[^}]*}\s*\)'
    
    simple_wheel = '''var wheelTimer=null;
deck.addEventListener("wheel",function(e){
  e.preventDefault();
  if(!wheelTimer){wheelTimer=setTimeout(function(){wheelTimer=null},400)}
  if(e.deltaY>0)go(cur+1);
  else if(e.deltaY<0)go(cur-1);
},{passive:false});'''
    
    content = re.sub(wheel_pattern, simple_wheel, content, flags=re.DOTALL)
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def batch_fix():
    templates = [f for f in os.listdir(ENGINE_DIR) if f.startswith('template-') and f.endswith('.html')]
    print(f"Found {len(templates)} templates")
    
    fixed = 0
    for t in templates:
        path = os.path.join(ENGINE_DIR, t)
        if fix_template(path):
            fixed += 1
            print(f"✓ Fixed: {t}")
        else:
            print(f"  Skip: {t} (no changes needed)")
    
    print(f"\nFixed {fixed}/{len(templates)} templates")

if __name__ == "__main__":
    batch_fix()
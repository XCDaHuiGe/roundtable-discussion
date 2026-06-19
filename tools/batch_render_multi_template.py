# -*- coding: utf-8 -*-
"""批量渲染V8 JSON - 使用多模板"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.render_v8_adapter import render_v8_with_selected_template

CONTENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

def batch_render_multi_template():
    json_files = [f for f in os.listdir(CONTENT_DIR) if f.endswith("_v8.json")]
    print(f"Found {len(json_files)} JSON files")
    print("=" * 60)
    
    success = 0
    template_usage = {}
    
    for json_file in sorted(json_files):
        json_path = os.path.join(CONTENT_DIR, json_file)
        base_name = json_file.replace("_v8.json", "")
        output_path = os.path.join(OUTPUT_DIR, f"{base_name}_圆桌洞见.html")
        
        with open(json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        topic = data.get('title', base_name)
        
        try:
            html, template_id, template_name = render_v8_with_selected_template(data, topic)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            success += 1
            template_usage[template_name] = template_usage.get(template_name, 0) + 1
            print(f"✓ {base_name} → {template_name}")
        except Exception as e:
            print(f"✗ {base_name}: {e}")
    
    print("=" * 60)
    print(f"完成: {success}/{len(json_files)}")
    print("\n模板使用统计:")
    for name, count in sorted(template_usage.items(), key=lambda x: -x[1]):
        print(f"  {name}: {count}")

if __name__ == "__main__":
    batch_render_multi_template()
# -*- coding: utf-8 -*-
"""批量重新渲染所有V8 JSON文件"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.render_v8 import render_from_json

CONTENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

def batch_render():
    json_files = [f for f in os.listdir(CONTENT_DIR) if f.endswith("_v8.json")]
    print(f"Found {len(json_files)} JSON files to render")
    
    success_count = 0
    error_count = 0
    
    for json_file in json_files:
        json_path = os.path.join(CONTENT_DIR, json_file)
        base_name = json_file.replace("_v8.json", "")
        output_path = os.path.join(OUTPUT_DIR, f"{base_name}_圆桌洞见.html")
        
        try:
            render_from_json(json_path, output_path)
            success_count += 1
            print(f"✓ {base_name}")
        except Exception as e:
            error_count += 1
            print(f"✗ {base_name}: {e}")
    
    print(f"\n完成: {success_count} 成功, {error_count} 失败")

if __name__ == "__main__":
    batch_render()
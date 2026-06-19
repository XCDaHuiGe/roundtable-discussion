#!/usr/bin/env python3
"""
模板验证脚本 - 检查所有模板是否完整可用
"""

import json
from pathlib import Path

ENGINE_DIR = Path(__file__).parent
TEMPLATES_CONFIG = ENGINE_DIR / "templates.json"

REQUIRED_ELEMENTS_ADAPTER = [
    ("<!DOCTYPE html>", "HTML声明"),
    ("{{slides}}", "内容占位符"),
    ("</html>", "HTML结束标签"),
    ("<script>", "JavaScript脚本"),
]

REQUIRED_ELEMENTS_HANDLEBARS = [
    ("<!DOCTYPE html>", "HTML声明"),
    ("{{#each", "Handlebars循环"),
    ("</html>", "HTML结束标签"),
    ("<script>", "JavaScript脚本"),
]

def validate_template(template_file: Path, template_id: str) -> dict:
    """验证单个模板"""
    result = {
        "file": template_file.name,
        "id": template_id,
        "exists": template_file.exists(),
        "size": 0,
        "type": "unknown",
        "checks": {},
        "errors": []
    }
    
    if not template_file.exists():
        result["errors"].append("文件不存在")
        return result
    
    content = template_file.read_text(encoding="utf-8")
    result["size"] = len(content)
    
    # 判断模板类型
    if "{{#each" in content or "{{add" in content:
        result["type"] = "handlebars"
        required = REQUIRED_ELEMENTS_HANDLEBARS
    elif "{{slides}}" in content:
        result["type"] = "adapter"
        required = REQUIRED_ELEMENTS_ADAPTER
    else:
        result["type"] = "unknown"
        required = REQUIRED_ELEMENTS_ADAPTER
    
    for element, name in required:
        found = element in content
        result["checks"][name] = found
        if not found:
            result["errors"].append(f"缺少: {name}")
    
    # 检查导航（多种形式，包括滚动式）
    nav_patterns = ["id=\"nav\"", "id=\"navDots\"", "class=\"nav-bar\"", 
                   "class=\"bottom-nav\"", "class=\"nav-dots\"", "id=\"navDots\""]
    has_nav = any(p in content for p in nav_patterns)
    result["checks"]["导航组件"] = has_nav
    if not has_nav:
        result["errors"].append("缺少导航组件")
    
    # 检查翻页逻辑（滚动式模板不需要翻页按钮）
    # 检查是否有滚动式设计：CSS 中定义 .section 类 + scrollIntoView
    has_scroll_css = ".section{" in content or ".section " in content
    has_scroll_js = "scrollIntoView" in content
    is_scroll_template = has_scroll_css and has_scroll_js
    has_pagination = "prevBtn" in content or "btnPrev" in content or is_scroll_template
    result["checks"]["翻页按钮"] = has_pagination
    if not has_pagination:
        result["errors"].append("缺少翻页按钮")
    
    return result

def main():
    """验证所有模板"""
    with open(TEMPLATES_CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    print("\n📋 模板验证报告\n")
    print("=" * 80)
    
    total = len(config["templates"])
    passed = 0
    failed = 0
    
    for t in config["templates"]:
        template_file = ENGINE_DIR / t["file"]
        result = validate_template(template_file, t["id"])
        
        status = "✅" if not result["errors"] else "❌"
        if not result["errors"]:
            passed += 1
        else:
            failed += 1
        
        type_icon = "🔷" if result["type"] == "handlebars" else "🔶" if result["type"] == "adapter" else "❓"
        
        print(f"\n{status} {type_icon} {t['id']:<20} {t['name']}")
        print(f"   文件: {result['file']}")
        print(f"   类型: {result['type']}")
        print(f"   大小: {result['size']} bytes")
        
        if result["errors"]:
            print(f"   错误: {', '.join(result['errors'])}")
        else:
            checks = [k for k, v in result["checks"].items() if v]
            print(f"   检查: {len(checks)}/{len(result['checks'])} 通过")
    
    print("\n" + "=" * 80)
    print(f"\n📊 统计: {passed}/{total} 通过, {failed}/{total} 失败\n")
    
    # 按类型统计
    handlebars_count = sum(1 for t in config["templates"] 
                          if "{{#each" in (ENGINE_DIR / t["file"]).read_text(encoding="utf-8"))
    adapter_count = total - handlebars_count
    
    print(f"🔷 Handlebars 模板: {handlebars_count} 个 (配合 render_v8.py)")
    print(f"🔶 Adapter 模板: {adapter_count} 个 (配合 render_adapter.py)")
    
    if failed == 0:
        print("\n🎉 所有模板验证通过！")
    else:
        print("\n⚠️ 有模板需要修复")

if __name__ == "__main__":
    main()
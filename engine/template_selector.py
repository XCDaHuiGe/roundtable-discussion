#!/usr/bin/env python3
"""
模板选择器 - 随机选择合适的渲染模板
用法: python template_selector.py [--topic TOPIC] [--force TEMPLATE_ID]
"""

import json
import random
import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
TEMPLATES_CONFIG = SCRIPT_DIR / "templates.json"

TOPIC_TEMPLATES = {
    "投资": ["consulting-report", "clean-review", "v3-magazine"],
    "哲学": ["editorial", "rain-notes", "v2-starry"],
    "科技": ["geek-report", "pixel-report", "dot-matrix", "v2-starry"],
    "AI": ["geek-report", "pixel-report", "consulting-report"],
    "文学": ["editorial", "sunrise", "v3-magazine"],
    "社会": ["dot-matrix", "editorial", "v2-starry"],
    "情感": ["rain-notes", "sunrise", "story-field"],
    "创意": ["y2k-brand", "editorial", "sunrise"],
}

def load_templates():
    with open(TEMPLATES_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

def save_templates(config):
    with open(TEMPLATES_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_topic_key(topic: str) -> str:
    """从话题中提取匹配键"""
    topic = topic.upper()
    for key in TOPIC_TEMPLATES.keys():
        if key in topic:
            return key
    return "default"

def select_template(topic: str = None, force_id: str = None, seed: int = None) -> dict:
    """选择模板"""
    config = load_templates()
    
    if seed is not None:
        random.seed(seed)
    else:
        random.seed()
    
    if force_id:
        for t in config["templates"]:
            if t["id"] == force_id:
                _log_usage(config, t["id"], topic, "forced")
                return t
        print(f"⚠️ 未找到指定模板 {force_id}，将随机选择")
    
    if topic:
        key = get_topic_key(topic)
        candidate_ids = TOPIC_TEMPLATES.get(key, config["selection"].get("default", ["consulting-report"]))
        candidates = [t for t in config["templates"] if t["id"] in candidate_ids]
        if candidates:
            selected = random.choice(candidates)
            _log_usage(config, selected["id"], topic, "topic_matched")
            return selected
    
    selected = random.choice(config["templates"])
    _log_usage(config, selected["id"], topic, "random")
    return selected

def _log_usage(config, template_id: str, topic: str, reason: str):
    """记录使用日志"""
    if "usage_log" not in config:
        config["usage_log"] = []
    
    config["usage_log"].append({
        "template": template_id,
        "topic": topic,
        "reason": reason
    })
    
    if len(config["usage_log"]) > 100:
        config["usage_log"] = config["usage_log"][-100:]
    
    save_templates(config)

def list_templates():
    """列出所有可用模板"""
    config = load_templates()
    print("\n📋 可用模板列表:\n")
    print(f"{'ID':<22} {'名称':<18} {'来源':<10} {'描述'}")
    print("-" * 90)
    for t in config["templates"]:
        origin = t.get("origin", "original")
        desc = t.get("description", "")[:40]
        print(f"{t['id']:<22} {t['name']:<18} {origin:<10} {desc}")
    print()

def render_with_template(data: dict, template_id: str, output_path: str = None):
    """使用指定模板渲染数据"""
    from render_adapter import adapt
    
    config = load_templates()
    template_file = None
    
    for t in config["templates"]:
        if t["id"] == template_id:
            template_file = SCRIPT_DIR / t["file"]
            break
    
    if not template_file or not template_file.exists():
        print(f"❌ 模板文件不存在: {template_id}")
        return None
    
    template_html = template_file.read_text(encoding="utf-8")
    slides_html = adapt(data, template_id)
    
    html = template_html.replace("{{slides}}", slides_html)
    html = html.replace("{{title}}", data.get("title", "圆桌洞见"))
    html = html.replace("{{subtitle}}", data.get("subtitle", ""))
    
    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")
        print(f"✅ 已渲染到: {output_path}")
    
    return html

def main():
    parser = argparse.ArgumentParser(description="圆桌洞见模板选择器")
    parser.add_argument("--topic", "-t", help="话题内容")
    parser.add_argument("--force", "-f", help="强制使用指定模板ID")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有模板")
    parser.add_argument("--seed", "-s", type=int, help="随机种子(可复现)")
    parser.add_argument("--render", "-r", help="渲染数据JSON文件")
    parser.add_argument("--output", "-o", help="输出HTML文件路径")
    
    args = parser.parse_args()
    
    if args.list:
        list_templates()
        return
    
    if args.render:
        import json
        with open(args.render, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        template = select_template(topic=data.get("title", ""), force_id=args.force, seed=args.seed)
        print(f"🎨 使用模板: {template['name']} ({template['id']})")
        
        output = args.output or args.render.replace(".json", "_圆桌洞见.html")
        render_with_template(data, template["id"], output)
        return
    
    template = select_template(topic=args.topic, force_id=args.force, seed=args.seed)
    print(f"🎨 {template['name']} ({template['id']})")
    print(f"📄 {SCRIPT_DIR / template['file']}")

if __name__ == "__main__":
    main()

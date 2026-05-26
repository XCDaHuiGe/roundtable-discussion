#!/usr/bin/env python3
"""
模板选择器 - 随机选择合适的渲染模板
用法: python template_selector.py [--topic TOPIC] [--force TEMPLATE_ID]
"""

import json
import random
import argparse
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent
TEMPLATES_CONFIG = TEMPLATES_DIR / "templates.json"

TOPIC_TEMPLATES = {
    "投资": ["v3-magazine", "v2-starry"],
    "哲学": ["v2-starry"],
    "科技": ["v2-starry", "v3-magazine"],
    "文学": ["v3-magazine", "v2-starry"],
    "社会": ["v2-starry"],
    "default": ["v3-magazine", "v2-starry"]
}

def load_templates():
    with open(TEMPLATES_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

def save_templates(config):
    with open(TEMPLATES_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_topic_key(topic: str) -> str:
    """从话题中提取匹配键"""
    for key in TOPIC_TEMPLATES.keys():
        if key != "default" and key in topic:
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
        candidate_ids = TOPIC_TEMPLATES.get(key, TOPIC_TEMPLATES["default"])
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
    print(f"{'ID':<20} {'名称':<20} {'风格'}")
    print("-" * 60)
    for t in config["templates"]:
        print(f"{t['id']:<20} {t['name']:<20} {t['style']}")
    print()

def main():
    parser = argparse.ArgumentParser(description="模板选择器")
    parser.add_argument("--topic", "-t", help="话题内容")
    parser.add_argument("--force", "-f", help="强制使用指定模板ID")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有模板")
    parser.add_argument("--seed", "-s", type=int, help="随机种子(可复现)")
    
    args = parser.parse_args()
    
    if args.list:
        list_templates()
        return
    
    template = select_template(topic=args.topic, force_id=args.force, seed=args.seed)
    print(template["file"])

if __name__ == "__main__":
    main()

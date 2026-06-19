# -*- coding: utf-8 -*-
"""
圆桌洞见渲染器 V9.0

Agent传入JSON数据，Python只做HTML渲染。
零LLM依赖。

用法：
    python render_roundtable.py <json_path> [--output OUTPUT] [--template TEMPLATE]
    python render_roundtable.py content/穷查理宝典_v8.json --template v3-magazine
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CONTENT_DIR = Path(__file__).parent.parent / "content"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def render_from_json(
    json_path: str,
    output_path: str = None,
    template_id: str = None,
) -> str:
    """
    从JSON渲染HTML

    Args:
        json_path: v8 JSON文件路径
        output_path: 输出HTML路径（可选）
        template_id: 模板ID（可选）

    Returns:
        渲染后的HTML路径
    """
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON文件不存在: {json_path}")

    with open(json_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    if isinstance(data, dict) and "title" in data:
        data["title"] = data["title"].lstrip("\ufeff")

    book_title = data.get("title", json_path.stem)
    if book_title.startswith("《"):
        book_title = book_title[1:]
    if book_title.endswith("》"):
        book_title = book_title[:-1]
    if book_title.endswith("圆桌洞见"):
        book_title = book_title[:-4]

    if not output_path:
        output_path = OUTPUT_DIR / f"{book_title}_圆桌洞见.html"

    _render_html(data, str(output_path), template_id)

    return str(output_path)


def _render_html(data: Dict, output_path: str, template_id: str = None):
    """渲染HTML"""
    try:
        from template_selector import select_template, render_with_template

        if template_id:
            template = select_template(force_id=template_id)
        else:
            template = select_template(topic=data.get("title", ""))

        print(f"[TEMPLATE] {template['name']} ({template['id']})")
        render_with_template(data, template["id"], output_path)
        print(f"[SAVE] HTML: {output_path}")

    except ImportError:
        try:
            from render_adapter import adapt

            template_path = Path(__file__).parent / "template-premium-dark.html"
            if template_path.exists():
                template_html = template_html.read_text(encoding="utf-8")
                html = adapt(data, "premium-dark")
                html = template_html.replace("{{slides}}", html)
                html = html.replace("{{title}}", data.get("title", ""))
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                Path(output_path).write_text(html, encoding="utf-8")
                print(f"[SAVE] HTML: {output_path}")
            else:
                print(f"[WARN] 模板文件不存在")
                _render_fallback(data, output_path)

        except Exception as e:
            print(f"[WARN] 渲染失败: {e}")
            _render_fallback(data, output_path)


def _render_fallback(data: Dict, output_path: str):
    """回退渲染（无模板时）"""
    title = data.get("title", "圆桌洞见")
    experts = data.get("experts", [])
    rounds = data.get("rounds", [])

    html_parts = [
        "<!DOCTYPE html>",
        "<html><head>",
        f"<title>{title}</title>",
        "<style>",
        "body{font-family:system-ui;background:#1a1a2a;color:#eee;padding:40px;}",
        ".expert{margin:20px 0;padding:20px;background:#2a2a4a;border-radius:8px;}",
        ".round{margin:30px 0;padding:30px;background:#16213e;border-radius:12px;}",
        ".stance{margin:15px 0;padding:15px;background:#0f3460;}",
        ".clash{margin:15px 0;padding:15px;background:#e94560;color:#fff;}",
        "</style>",
        "</head><body>",
        f"<h1>{title}</h1>",
    ]

    if experts:
        html_parts.append("<h2>参与专家</h2>")
        for e in experts:
            html_parts.append(f"<div class='expert'><b>{e.get('name','')}</b> - {e.get('title','')}</div>")

    for r in rounds:
        html_parts.append(f"<div class='round'><h3>Round {r.get('round_number',0)}: {r.get('topic','')}</h3>")

        for s in r.get("stances", []):
            html_parts.append(f"<div class='stance'><b>{s.get('expert','')}</b>: {s.get('stance','')}</div>")

        for c in r.get("clash_rounds", []):
            html_parts.append(
                f"<div class='clash'><b>{c.get('attacker','')}</b> → <b>{c.get('target','')}</b>: {c.get('attack_content','')}</div>"
            )

        html_parts.append("</div>")

    html_parts.append("</body></html>")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text("\n".join(html_parts), encoding="utf-8")
    print(f"[SAVE] HTML (fallback): {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="圆桌洞见渲染器")
    parser.add_argument("json_path", help="v8 JSON文件路径")
    parser.add_argument("--output", "-o", help="输出HTML路径")
    parser.add_argument("--template", "-t", help="指定模板ID")

    args = parser.parse_args()

    output = render_from_json(
        json_path=args.json_path,
        output_path=args.output,
        template_id=args.template,
    )

    print(f"\n渲染完成: {output}")


if __name__ == "__main__":
    main()
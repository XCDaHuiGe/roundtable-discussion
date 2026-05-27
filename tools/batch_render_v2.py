# -*- coding: utf-8 -*-
"""批量渲染5个新话题的讨论JSON到HTML - 简化版"""

import json
import os
import subprocess
import shutil

def convert_to_render_format(input_path: str, output_path: str):
    """将讨论JSON转换为render_roundtable.js期望的格式"""

    with open(input_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    # 提取专家信息
    experts = []
    expert_names = set()
    for round_data in data.get("rounds", []):
        for speaker in round_data.get("speakers", []):
            name = speaker.get("name", "")
            if name and name not in expert_names:
                expert_names.add(name)
                role = speaker.get("role", "")
                color = speaker.get("avatar_color", "#4a6a9a")

                # 为每个专家分配一个emoji作为头像
                emojis = ["🎓", "📚", "💡", "🔍", "⚖️", "🎯"]
                avatar_idx = len(experts) % len(emojis)

                experts.append({
                    "id": name,
                    "name": name,
                    "title": role,
                    "avatar": emojis[avatar_idx],
                    "color": color
                })

    # 构建轮次
    rounds = []
    for i, round_data in enumerate(data.get("rounds", [])):
        discussions = []
        for speaker in round_data.get("speakers", []):
            discussions.append({
                "expert_id": speaker.get("name", ""),
                "stance": round_data.get("question", ""),
                "content": speaker.get("content", ""),
                "quotes": [],
                "citations": []
            })

        collision = round_data.get("clashes", [])
        collision_content = ""
        if collision:
            c = collision[0]
            collision_content = f"{c.get('expert', '')}：{c.get('content', '')}"

        rounds.append({
            "title": round_data.get("topic", ""),
            "description": round_data.get("question", ""),
            "discussions": discussions,
            "collision": {
                "title": f"第{i+1}轮碰撞",
                "content": collision_content
            }
        })

    # 提取洞见
    key_insights = []
    for i, round_data in enumerate(data.get("rounds", [])):
        insight = round_data.get("insight", {})
        if insight:
            key_insights.append({
                "expert": f"第{i+1}轮综合",
                "title": insight.get("statement", "")[:100],
                "summary": insight.get("explanation", "")[:300]
            })

    output = {
        "title": data.get("title", ""),
        "subtitle": data.get("subtitle", ""),
        "date": "2026-05-26",
        "experts": experts,
        "rounds": rounds,
        "key_insights": key_insights
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Converted: {output_path}")
    return output_path


def run_node_renderer(content_json_path, output_html_path):
    """运行Node.js渲染器"""
    # 复制现有的render_roundtable.js并修改输入输出路径
    source_js = os.path.join(os.path.dirname(__file__), '..', 'tools', 'render_roundtable.js')

    with open(source_js, 'r', encoding='utf-8') as f:
        js_content = f.read()

    # 修改输入输出路径
    content_json_name = os.path.basename(content_json_path)
    output_html_name = os.path.basename(output_html_path)

    js_content = js_content.replace(
        "const jsonPath = path.join(__dirname, '..', 'content', '影视模因_散户狂潮_讨论.json');",
        f"const jsonPath = path.join(__dirname, '..', 'content', '{content_json_name}');"
    )
    js_content = js_content.replace(
        "const outputPath = path.join(__dirname, '..', 'output', '影视模因_散户狂潮_圆桌洞见.html');",
        f"const outputPath = path.join(__dirname, '..', 'output', '{output_html_name}');"
    )

    # 写入临时脚本
    temp_js = os.path.join(os.path.dirname(content_json_path), '_temp_render_roundtable.js')
    with open(temp_js, 'w', encoding='utf-8') as f:
        f.write(js_content)

    # 运行
    try:
        result = subprocess.run(
            ['node', temp_js],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print(f"HTML generated: {output_html_path}")
        else:
            print(f"Error: {result.stderr}")
    finally:
        if os.path.exists(temp_js):
            os.remove(temp_js)


def main():
    content_dir = os.path.join(os.path.dirname(__file__))
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')

    topics = [
        ("算法情感_金融信任套利_讨论.json", "算法情感_金融信任套利_圆桌洞见.html"),
        ("多巴胺_叙事降级_讨论.json", "多巴胺_叙事降级_圆桌洞见.html"),
        ("数字农奴_生活殖民化_讨论.json", "数字农奴_生活殖民化_圆桌洞见.html"),
        ("银幕景观_底层债务_讨论.json", "银幕景观_底层债务_圆桌洞见.html"),
        ("人机协作_权力倒挂_讨论.json", "人机协作_权力倒挂_圆桌洞见.html"),
    ]

    for input_file, output_file in topics:
        input_path = os.path.join(content_dir, input_file)
        output_path = os.path.join(output_dir, output_file)

        if os.path.exists(input_path):
            print(f"\n{'='*50}")
            print(f"Processing: {input_file}")

            # 转换格式
            temp_json = os.path.join(content_dir, '_temp_render.json')
            convert_to_render_format(input_path, temp_json)

            # 复制到正确的位置（render_roundtable.js会从content目录读取）
            temp_json_for_render = os.path.join(content_dir, '影视模因_散户狂潮_讨论.json')
            shutil.copy(temp_json, temp_json_for_render)

            # 运行渲染器
            run_node_renderer(temp_json_for_render, output_path)

            # 清理
            if os.path.exists(temp_json):
                os.remove(temp_json)
            if os.path.exists(temp_json_for_render):
                os.remove(temp_json_for_render)
        else:
            print(f"File not found: {input_path}")

    print("\n" + "="*50)
    print("All topics processed!")


if __name__ == "__main__":
    main()

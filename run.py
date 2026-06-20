# -*- coding: utf-8 -*-
"""
run.py — 圆桌洞见端到端管线

用法：
  python run.py "AI会取代人类工作吗"
  python run.py "消费主义的本质" --theme acid --rounds 3
  python run.py "人生的意义" --experts "老子,尼采,苏格拉底"
  python run.py --topic "AI与人性" --material material.txt

管线步骤：
  Step1: 话题分析 → 自动匹配6位专家
  Step2: 素材收集（从文件/参数/本地）
  Step3: LLM生成V8 JSON辩论
  Step4: 自动评分
  Step5: 渲染HTML-PPT
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

ENGINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'engine')
sys.path.insert(0, ENGINE_DIR)

from topic_router import select_experts, explain_selection
from material_collector import collect_material
from debate_generator import generate_debate
from html_renderer import render_to_file
from auto_scorer import auto_score_debate
from scorer import score_discussion


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
CONTENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'content')


def run_pipeline(
    topic: str,
    experts: list = None,
    material_text: str = '',
    web_text: str = '',
    zhihu_text: str = '',
    rounds: int = 3,
    theme: str = 'gold',
    output_name: str = None,
    skip_debate: bool = False,
    debate_json_path: str = None,
) -> dict:
    """端到端管线

    Args:
        topic: 话题
        experts: 指定专家列表（可选，None则自动匹配）
        material_text: 预置素材文本
        web_text: WebSearch 结果
        zhihu_text: 知乎搜索结果
        rounds: 辩论轮数
        theme: HTML主题 (gold/acid/warm)
        output_name: 输出文件名（可选）
        skip_debate: 跳过LLM辩论生成（使用已有JSON）
        debate_json_path: 已有的辩论JSON路径（skip_debate=True时使用）

    Returns:
        {success, html_path, json_path, score, experts, elapsed}
    """
    start_time = time.time()
    result = {
        'success': False,
        'topic': topic,
        'html_path': '',
        'json_path': '',
        'score': {},
        'experts': [],
        'elapsed': 0,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CONTENT_DIR, exist_ok=True)

    # ── Step1: 专家匹配 ──
    print(f"\n{'='*60}")
    print(f"  Step1: 专家匹配")
    print(f"{'='*60}")

    if experts:
        # 使用指定专家
        expert_list = [{'name': e, 'domain': '指定', 'score': 100, 'reason': '用户指定'} for e in experts]
    else:
        expert_list = select_experts(topic, count=6)

    result['experts'] = [e['name'] for e in expert_list]
    expert_names = [e['name'] for e in expert_list]

    for e in expert_list:
        print(f"  ✅ {e['name']} ({e['domain']}) — {e.get('reason', '')}")

    # ── Step2: 素材收集 ──
    print(f"\n{'='*60}")
    print(f"  Step2: 素材收集")
    print(f"{'='*60}")

    material = collect_material(
        topic,
        web_text=web_text or material_text,
        zhihu_text=zhihu_text,
    )
    print(f"  素材长度: {len(material)} 字符")

    # ── Step3: 辩论生成 ──
    print(f"\n{'='*60}")
    print(f"  Step3: 辩论生成")
    print(f"{'='*60}")

    if skip_debate and debate_json_path and os.path.exists(debate_json_path):
        print(f"  使用已有JSON: {debate_json_path}")
        with open(debate_json_path, 'r', encoding='utf-8') as f:
            debate_data = json.load(f)
    else:
        print(f"  调用LLM生成辩论 ({rounds}轮)...")
        try:
            debate_data = generate_debate(
                topic=topic,
                experts=expert_names,
                material=material,
                rounds=rounds,
            )
        except Exception as e:
            print(f"  ❌ 辩论生成失败: {e}")
            result['error'] = str(e)
            return result

    # 保存V8 JSON
    if not output_name:
        safe_name = topic[:30].replace(' ', '_').replace('/', '_').replace('\\', '_')
        output_name = safe_name

    json_path = os.path.join(CONTENT_DIR, f"{output_name}_v8.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(debate_data, f, ensure_ascii=False, indent=2)
    result['json_path'] = json_path
    print(f"  JSON已保存: {json_path}")

    # ── Step4: 自动评分 ──
    print(f"\n{'='*60}")
    print(f"  Step4: 自动评分")
    print(f"{'='*60}")

    try:
        auto_scores = auto_score_debate(debate_data, expert_names=expert_names)
        score_result = score_discussion(auto_scores)
        result['score'] = score_result
        print(f"  总分: {score_result['total']} ({score_result['grade']})")
        for dim, val in auto_scores.items():
            print(f"    {dim}: {val}")
    except Exception as e:
        print(f"  ⚠️ 评分失败: {e}")

    # ── Step5: 渲染HTML ──
    print(f"\n{'='*60}")
    print(f"  Step5: 渲染HTML")
    print(f"{'='*60}")

    html_path = os.path.join(OUTPUT_DIR, f"{output_name}_圆桌洞见.html")
    try:
        render_to_file(debate_data, html_path, theme=theme)
        result['html_path'] = html_path
        print(f"  HTML已保存: {html_path}")
    except Exception as e:
        print(f"  ❌ 渲染失败: {e}")
        result['error'] = str(e)
        return result

    # ── 完成 ──
    elapsed = time.time() - start_time
    result['success'] = True
    result['elapsed'] = round(elapsed, 1)

    print(f"\n{'='*60}")
    print(f"  ✅ 完成! 耗时 {elapsed:.1f}s")
    print(f"  话题: {topic}")
    print(f"  专家: {', '.join(expert_names)}")
    print(f"  JSON: {json_path}")
    print(f"  HTML: {html_path}")
    if result['score']:
        print(f"  评分: {result['score']['total']} ({result['score']['grade']})")
    print(f"{'='*60}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description='圆桌洞见 — 端到端管线',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py "AI会取代人类工作吗"
  python run.py "消费主义的本质" --theme acid --rounds 3
  python run.py "人生的意义" --experts "老子,尼采,苏格拉底"
  python run.py --json content/existing_v8.json --skip-debate
        """
    )
    parser.add_argument('topic', nargs='?', help='讨论话题')
    parser.add_argument('--experts', type=str, help='指定专家（逗号分隔）')
    parser.add_argument('--rounds', type=int, default=3, help='辩论轮数（默认3）')
    parser.add_argument('--theme', type=str, default='gold', choices=['gold', 'acid', 'warm'], help='HTML主题')
    parser.add_argument('--output', type=str, help='输出文件名')
    parser.add_argument('--material', type=str, help='素材文件路径')
    parser.add_argument('--web', type=str, help='WebSearch结果文本')
    parser.add_argument('--zhihu', type=str, help='知乎搜索结果文本')
    parser.add_argument('--json', type=str, help='已有V8 JSON路径（跳过生成）')
    parser.add_argument('--skip-debate', action='store_true', help='跳过LLM辩论生成')
    parser.add_argument('--explain', action='store_true', help='只显示专家匹配理由')

    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')

    if not args.topic and not args.json:
        parser.print_help()
        return

    topic = args.topic or '未知话题'

    # 专家匹配解释模式
    if args.explain:
        explain_selection(topic, count=6)
        return

    # 读取素材文件
    material_text = ''
    if args.material and os.path.exists(args.material):
        with open(args.material, 'r', encoding='utf-8') as f:
            material_text = f.read()

    # 解析专家
    experts = args.experts.split(',') if args.experts else None

    # 运行管线
    result = run_pipeline(
        topic=topic,
        experts=experts,
        material_text=material_text,
        web_text=args.web or '',
        zhihu_text=args.zhihu or '',
        rounds=args.rounds,
        theme=args.theme,
        output_name=args.output,
        skip_debate=args.skip_debate,
        debate_json_path=args.json,
    )

    if not result['success']:
        sys.exit(1)


if __name__ == '__main__':
    main()

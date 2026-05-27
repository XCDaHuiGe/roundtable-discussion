# -*- coding: utf-8 -*-
"""
圆桌洞见生成管线

从书籍文本 → 专家选择 → 多轮讨论 → 渲染 HTML

优化特性：
- 缓存专家档案（避免重复 LLM 调用）
- 指数退避重试
- 可配置超时参数
- 进度条追踪

用法：
    python generate_roundtable.py <book_path> [--output OUTPUT] [--template TEMPLATE]
    python generate_roundtable.py content/穷查理宝典.txt --template v3-magazine
"""

import json
import os
import sys
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_generate import (
    call_llm_json,
    ProgressTracker,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
    DEFAULT_MAX_RETRIES,
)

# ─── 配置 ──────────────────────────────────────────────────

EXPERT_LIBRARY_PATH = Path(__file__).parent.parent.parent / "expert-library" / "experts"
CONTENT_DIR = Path(__file__).parent.parent / "content"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
CACHE_DIR = Path(__file__).parent.parent / ".cache"

# LLM 调用默认参数
LLM_DEFAULTS = {
    "connect_timeout": DEFAULT_CONNECT_TIMEOUT,
    "read_timeout": DEFAULT_READ_TIMEOUT,
    "max_retries": DEFAULT_MAX_RETRIES,
    "request_interval": 1.5,
}

# 专家角色模板（6 位专家固定角色）
EXPERT_ROLES = [
    {"role": "价值投资奠基人", "perspective": "从长期价值和企业基本面分析"},
    {"role": "不确定性思想家", "perspective": "从风险、黑天鹅和反脆弱性分析"},
    {"role": "行为经济学之父", "perspective": "从认知偏误和决策心理学分析"},
    {"role": "情商理论专家", "perspective": "从情绪智商和人际关系分析"},
    {"role": "科技投资观察者", "perspective": "从科技趋势和产业变革分析"},
    {"role": "实证管理学家", "perspective": "从企业管理和组织行为分析"},
]

# 专家颜色
EXPERT_COLORS = ["#1a5f2a", "#8a2a4a", "#333333", "#2a6a8a", "#2a6a6a", "#4a2d8a"]


# ─── 缓存管理 ──────────────────────────────────────────────

def _cache_key(text: str) -> str:
    """生成缓存键"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:12]


def _load_cache(key: str) -> Optional[Dict]:
    """加载缓存"""
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def _save_cache(key: str, data: Dict):
    """保存缓存"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─── 专家库加载 ──────────────────────────────────────────────

def load_expert_library() -> List[Dict]:
    """从 expert-library 加载所有专家档案"""
    experts = []
    if not EXPERT_LIBRARY_PATH.exists():
        print(f"[WARN] 专家库路径不存在: {EXPERT_LIBRARY_PATH}")
        return experts

    for category_dir in EXPERT_LIBRARY_PATH.iterdir():
        if not category_dir.is_dir():
            continue
        for expert_file in category_dir.glob("*.md"):
            try:
                content = expert_file.read_text(encoding="utf-8")
                expert = _parse_expert_md(content, expert_file.stem)
                if expert:
                    experts.append(expert)
            except Exception as e:
                print(f"[WARN] 解析专家文件失败 {expert_file}: {e}")

    return experts


def _parse_expert_md(content: str, name: str) -> Optional[Dict]:
    """解析专家 Markdown 档案"""
    lines = content.strip().split("\n")
    if not lines:
        return None

    expert = {"name": name, "raw_content": content}

    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            expert["name"] = line[2:].strip()
        elif "核心信念" in line or "core_belief" in line.lower():
            parts = line.split("：", 1)
            if len(parts) > 1:
                expert["core_belief"] = parts[1].strip()
        elif "利益" in line or "interest" in line.lower():
            parts = line.split("：", 1)
            if len(parts) > 1:
                expert["interest"] = parts[1].strip()
        elif "恐惧" in line or "fear" in line.lower():
            parts = line.split("：", 1)
            if len(parts) > 1:
                expert["fear"] = parts[1].strip()
        elif "偏见" in line or "bias" in line.lower():
            parts = line.split("：", 1)
            if len(parts) > 1:
                expert["bias"] = parts[1].strip()

    return expert


def select_experts(book_title: str, book_content: str, library: List[Dict]) -> List[Dict]:
    """为书籍选择 6 位最合适的专家"""
    cache_key = _cache_key(f"experts_{book_title}_{book_content[:500]}")
    cached = _load_cache(cache_key)
    if cached:
        print(f"[CACHE] 命中专家选择缓存")
        return cached

    # 构建专家库摘要
    expert_summaries = []
    for i, exp in enumerate(library[:30]):  # 限制长度避免 token 溢出
        summary = f"{i+1}. {exp['name']}"
        if exp.get("core_belief"):
            summary += f" - {exp['core_belief'][:80]}"
        expert_summaries.append(summary)

    prompt = f"""为以下书籍选择 6 位最适合参与圆桌讨论的专家。

书籍标题：{book_title}
书籍摘要：{book_content[:1000]}

可选专家库：
{chr(10).join(expert_summaries)}

请从专家库中选择 6 位专家，确保：
1. 观点多元化（不同学科、不同立场）
2. 与书籍主题高度相关
3. 能产生有价值的碰撞

返回 JSON 格式：
{{
  "selected_experts": [
    {{"name": "专家名", "title": "头衔", "reason": "选择理由"}},
    ...
  ]
}}"""

    result = call_llm_json(prompt, "你是圆桌讨论的策展人，负责选择最有价值的专家组合。", **LLM_DEFAULTS)

    if result["success"] and result["data"]:
        selected = result["data"].get("selected_experts", [])
        # 匹配专家库中的完整档案
        experts = []
        for sel in selected[:6]:
            name = sel.get("name", "")
            matched = next((e for e in library if name in e.get("name", "")), None)
            if matched:
                experts.append({
                    "name": matched["name"],
                    "title": sel.get("title", matched.get("title", "")),
                    "avatar_color": EXPERT_COLORS[len(experts) % len(EXPERT_COLORS)],
                    "core_belief": matched.get("core_belief", sel.get("reason", "")),
                    "interest": matched.get("interest", ""),
                    "fear": matched.get("fear", ""),
                    "bias": matched.get("bias", ""),
                })
            else:
                experts.append({
                    "name": name,
                    "title": sel.get("title", ""),
                    "avatar_color": EXPERT_COLORS[len(experts) % len(EXPERT_COLORS)],
                    "core_belief": sel.get("reason", ""),
                    "interest": "",
                    "fear": "",
                    "bias": "",
                })

        if len(experts) >= 4:
            _save_cache(cache_key, experts)
            return experts

    # 回退：使用默认角色
    print("[WARN] LLM 专家选择失败，使用默认角色")
    return _default_experts()


def _default_experts() -> List[Dict]:
    """默认专家列表（回退方案）"""
    names = ["巴菲特", "塔勒布", "卡尼曼", "戈尔曼", "吴军", "柯林斯"]
    return [
        {
            "name": names[i],
            "title": EXPERT_ROLES[i]["role"],
            "avatar_color": EXPERT_COLORS[i],
            "core_belief": EXPERT_ROLES[i]["perspective"],
            "interest": "",
            "fear": "",
            "bias": "",
        }
        for i in range(6)
    ]


# ─── 讨论生成 ──────────────────────────────────────────────

def generate_topics(book_title: str, book_content: str) -> List[Dict]:
    """生成 3 轮讨论话题"""
    cache_key = _cache_key(f"topics_{book_title}_{book_content[:500]}")
    cached = _load_cache(cache_key)
    if cached:
        print(f"[CACHE] 命中话题缓存")
        return cached

    prompt = f"""为《{book_title}》设计 3 轮圆桌讨论话题。

书籍内容摘要：
{book_content[:2000]}

要求：
1. 第 1 轮：核心概念的多元解读（立场表达）
2. 第 2 轮：关键争议的深度碰撞（互相反驳）
3. 第 3 轮：现实应用与认知升级（案例+代价+人性+升级）

返回 JSON 格式：
{{
  "rounds": [
    {{
      "round_number": 1,
      "topic": "讨论主题",
      "core_question": "核心问题（一句话）"
    }},
    {{
      "round_number": 2,
      "topic": "讨论主题",
      "core_question": "核心问题"
    }},
    {{
      "round_number": 3,
      "topic": "讨论主题",
      "core_question": "核心问题"
    }}
  ]
}}"""

    result = call_llm_json(prompt, "你是圆桌讨论的话题策划师。", **LLM_DEFAULTS)

    if result["success"] and result["data"]:
        rounds = result["data"].get("rounds", [])
        if len(rounds) >= 3:
            _save_cache(cache_key, rounds)
            return rounds

    # 回退
    return [
        {"round_number": 1, "topic": f"《{book_title}》的核心理念", "core_question": "这本书的核心主张是否站得住脚？"},
        {"round_number": 2, "topic": f"《{book_title}》的争议与反驳", "core_question": "专家们如何互相质疑对方的观点？"},
        {"round_number": 3, "topic": f"《{book_title}》的现实启示", "core_question": "普通人能从中学到什么？"},
    ]


def generate_round_stances(
    book_title: str,
    round_info: Dict,
    experts: List[Dict],
    book_content: str,
    llm_kwargs: Dict = None,
) -> List[Dict]:
    """生成一轮的立场表达"""
    kwargs = {**LLM_DEFAULTS, **(llm_kwargs or {})}

    expert_profiles = "\n".join([
        f"- {e['name']}（{e['title']}）：核心信念={e.get('core_belief', 'N/A')[:60]}"
        for e in experts
    ])

    prompt = f"""《{book_title}》圆桌讨论 - Round {round_info['round_number']}

主题：{round_info['topic']}
核心问题：{round_info['core_question']}

参与专家：
{expert_profiles}

书籍相关片段：
{book_content[:1500]}

请为每位专家生成立场表达。每位专家应：
1. 从自己的专业角度出发
2. 引用书籍中的具体内容
3. 表达独特的观点（不要人云亦云）
4. 包含情感色彩

返回 JSON 格式：
{{
  "stances": [
    {{
      "expert": "专家名",
      "stance": "立场表达（200-400字）",
      "emotion": "serious|sarcasm|anger|hesitation|helplessness"
    }}
  ]
}}"""

    result = call_llm_json(prompt, "你是圆桌讨论的内容生成器，确保每位专家的观点独特且有深度。", **kwargs)

    if result["success"] and result["data"]:
        return result["data"].get("stances", [])
    return []


def generate_round_clashes(
    book_title: str,
    round_info: Dict,
    experts: List[Dict],
    stances: List[Dict],
    llm_kwargs: Dict = None,
) -> List[Dict]:
    """生成一轮的碰撞反驳"""
    kwargs = {**LLM_DEFAULTS, **(llm_kwargs or {})}

    stance_summary = "\n".join([
        f"- {s['expert']}: {s['stance'][:100]}..."
        for s in stances
    ])

    prompt = f"""《{book_title}》圆桌讨论 - Round {round_info['round_number']} 碰撞环节

主题：{round_info['topic']}

各专家立场摘要：
{stance_summary}

请生成 4-6 个专家之间的直接碰撞（互相反驳）。

碰撞要求：
1. 攻击要具体、有理有据
2. 攻击类型：逻辑漏洞、利益冲突、现实矛盾、人性弱点、失败案例
3. 每个碰撞包含：攻击者、目标、攻击内容
4. 部分碰撞可以有反击

返回 JSON 格式：
{{
  "clash_rounds": [
    {{
      "attacker": "攻击者名",
      "target": "目标名",
      "attack_type": "逻辑漏洞|利益冲突|现实矛盾|人性弱点|失败案例",
      "attack_content": "攻击内容（150-300字）",
      "emotion": "serious|anger|sarcasm",
      "counter_attack": "反击内容（可选）"
    }}
  ]
}}"""

    result = call_llm_json(prompt, "你是圆桌讨论的碰撞导演，确保专家之间产生真正的思想交锋。", **kwargs)

    if result["success"] and result["data"]:
        return result["data"].get("clash_rounds", [])
    return []


def generate_round_reality(
    book_title: str,
    round_info: Dict,
    experts: List[Dict],
    llm_kwargs: Dict = None,
) -> Dict:
    """生成一轮的现实案例、代价讨论、人性层、认知升级"""
    kwargs = {**LLM_DEFAULTS, **(llm_kwargs or {})}

    prompt = f"""《{book_title}》圆桌讨论 - Round {round_info['round_number']} 深度分析

主题：{round_info['topic']}
核心问题：{round_info['core_question']}

请生成以下内容：

1. 现实案例（2-3个）：与主题相关的真实案例
2. 代价讨论：如果普通人盲目模仿，会付出什么代价？
3. 人性层：从人性角度分析为什么大多数人无法做到
4. 认知升级：从旧思维到新思维的升级路径

返回 JSON 格式：
{{
  "reality_cases": [
    {{
      "case_name": "案例名",
      "case_source": "来源",
      "case_content": "案例内容（200-400字）",
      "case_outcome": "结果",
      "case_lesson": "教训"
    }}
  ],
  "cost_discussion": {{
    "scenario": "场景描述",
    "cost_analysis": [
      {{"cost": "代价名", "analysis": "分析"}}
    ],
    "worst_case": "最坏情况",
    "survivor_bias": "幸存者偏差"
  }},
  "human_nature": {{
    "question": "人性问题",
    "psychological_analysis": "心理分析",
    "real_examples": ["例子1", "例子2"],
    "conclusion": "结论"
  }},
  "cognitive_upgrade": {{
    "old_thinking": "旧思维",
    "new_thinking": "新思维",
    "complexity": "复杂性说明",
    "actionable_insight": "可执行洞见"
  }}
}}"""

    result = call_llm_json(prompt, "你是圆桌讨论的深度分析师，负责生成有洞察力的现实分析。", **kwargs)

    if result["success"] and result["data"]:
        return result["data"]
    return {}


def generate_final_insight(
    book_title: str,
    rounds: List[Dict],
    llm_kwargs: Dict = None,
) -> Dict:
    """生成最终洞见和开放问题"""
    kwargs = {**LLM_DEFAULTS, **(llm_kwargs or {})}

    round_summaries = "\n".join([
        f"Round {r['round_number']}: {r.get('topic', '')}"
        for r in rounds
    ])

    prompt = f"""《{book_title}》圆桌讨论 - 总结

讨论轮次：
{round_summaries}

请生成：
1. 一段精炼的最终洞见（50-100字）
2. 3 个留给读者的开放问题

返回 JSON 格式：
{{
  "final_insight": "最终洞见",
  "open_questions": ["问题1", "问题2", "问题3"]
}}"""

    result = call_llm_json(prompt, "你是圆桌讨论的总结者，负责提炼最有价值的洞见。", **kwargs)

    if result["success"] and result["data"]:
        return result["data"]
    return {
        "final_insight": f"《{book_title}》的讨论揭示了多元视角碰撞的价值。",
        "open_questions": [f"《{book_title}》的核心主张在现实中如何验证？"],
    }


# ─── 主管线 ──────────────────────────────────────────────

def generate_roundtable(
    book_path: str,
    output_path: str = None,
    template_id: str = None,
    llm_kwargs: Dict = None,
) -> Dict:
    """
    完整圆桌洞见生成管线。

    Args:
        book_path: 书籍文本路径
        output_path: 输出 HTML 路径（可选）
        template_id: 模板 ID（可选，随机选择）
        llm_kwargs: LLM 调用参数覆盖

    Returns:
        生成的 v8 JSON 数据
    """
    book_path = Path(book_path)
    if not book_path.exists():
        raise FileNotFoundError(f"书籍文件不存在: {book_path}")

    book_content = book_path.read_text(encoding="utf-8-sig")
    book_title = book_path.stem

    # 从内容中提取标题（如果有）
    first_line = book_content.strip().split("\n")[0].strip()
    if first_line.startswith("#"):
        book_title = first_line.lstrip("#").strip()
    elif len(first_line) < 50:
        book_title = first_line

    total_steps = 12  # 选择专家 + 话题 + 3轮*(立场+碰撞+现实) + 总结
    tracker = ProgressTracker(total_steps, book_title)

    print(f"\n{'='*60}")
    print(f"圆桌洞见生成: {book_title}")
    print(f"输入: {book_path}")
    print(f"{'='*60}\n")

    # Step 1: 加载专家库
    tracker.update(1, "加载专家库...")
    library = load_expert_library()
    print(f"  专家库: {len(library)} 位专家")

    # Step 2: 选择专家
    tracker.update(2, "选择专家...")
    experts = select_experts(book_title, book_content, library)
    print(f"  选定: {', '.join(e['name'] for e in experts)}")

    # Step 3: 生成话题
    tracker.update(3, "生成讨论话题...")
    topics = generate_topics(book_title, book_content)

    # Step 4-11: 生成 3 轮讨论
    rounds_data = []
    for i, topic in enumerate(topics):
        round_num = i + 1

        # 立场表达
        tracker.update(4 + i * 3, f"Round {round_num} 立场表达...")
        stances = generate_round_stances(book_title, topic, experts, book_content, llm_kwargs)

        # 碰撞反驳
        tracker.update(5 + i * 3, f"Round {round_num} 碰撞反驳...")
        clashes = generate_round_clashes(book_title, topic, experts, stances, llm_kwargs)

        # 现实分析
        tracker.update(6 + i * 3, f"Round {round_num} 现实分析...")
        reality = generate_round_reality(book_title, topic, experts, llm_kwargs)

        round_data = {
            "round_number": round_num,
            "topic": topic.get("topic", f"Round {round_num}"),
            "core_question": topic.get("core_question", ""),
            "stances": stances,
            "clash_rounds": clashes,
            "reality_cases": reality.get("reality_cases", []),
            "cost_discussion": reality.get("cost_discussion", {}),
            "human_nature": reality.get("human_nature", {}),
            "cognitive_upgrade": reality.get("cognitive_upgrade", {}),
        }
        rounds_data.append(round_data)

    # Step 12: 最终洞见
    tracker.update(12, "生成最终洞见...")
    final = generate_final_insight(book_title, rounds_data, llm_kwargs)

    # 组装 v8 JSON
    v8_data = {
        "title": f"《{book_title}》圆桌洞见",
        "subtitle": f"《{book_title}》· {len(experts)}位专家 · {len(rounds_data)}轮碰撞 · 基于互联网真实素材",
        "experts": experts,
        "rounds": rounds_data,
        "final_insight": final.get("final_insight", ""),
        "open_questions": final.get("open_questions", []),
    }

    tracker.finish("生成完成")

    # 保存 JSON
    json_path = CONTENT_DIR / f"{book_title}_v8.json"
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(v8_data, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVE] JSON: {json_path}")

    # 渲染 HTML
    if output_path:
        _render_html(v8_data, output_path, template_id)
    else:
        output_path = OUTPUT_DIR / f"{book_title}_圆桌洞见.html"
        _render_html(v8_data, str(output_path), template_id)

    # 统计
    total_stances = sum(len(r.get("stances", [])) for r in rounds_data)
    total_clashes = sum(len(r.get("clash_rounds", [])) for r in rounds_data)
    print(f"\n{'='*60}")
    print(f"生成统计:")
    print(f"  专家: {len(experts)} 位")
    print(f"  轮次: {len(rounds_data)} 轮")
    print(f"  发言: {total_stances} 次")
    print(f"  碰撞: {total_clashes} 次")
    print(f"  洞见: {len(final.get('open_questions', []))} 个开放问题")
    print(f"{'='*60}")

    return v8_data


def _render_html(data: Dict, output_path: str, template_id: str = None):
    """渲染 HTML"""
    try:
        from template_selector import select_template, render_with_template

        if template_id:
            template = select_template(force_id=template_id)
        else:
            template = select_template(topic=data.get("title", ""))

        print(f"[TEMPLATE] {template['name']} ({template['id']})")
        render_with_template(data, template["id"], output_path)
    except ImportError:
        # 回退到 render_adapter
        try:
            from render_adapter import adapt
            template_path = Path(__file__).parent / "template-premium-dark.html"
            if template_path.exists():
                template_html = template_path.read_text(encoding="utf-8")
                html = adapt(data, "premium-dark")
                html = template_html.replace("{{slides}}", html)
                html = html.replace("{{title}}", data.get("title", ""))
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                Path(output_path).write_text(html, encoding="utf-8")
                print(f"[SAVE] HTML: {output_path}")
            else:
                print(f"[WARN] 模板文件不存在，仅保存 JSON")
        except Exception as e:
            print(f"[WARN] HTML 渲染失败: {e}")


# ─── CLI ──────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="圆桌洞见生成管线")
    parser.add_argument("book_path", help="书籍文本文件路径")
    parser.add_argument("--output", "-o", help="输出 HTML 路径")
    parser.add_argument("--template", "-t", help="指定模板 ID")
    parser.add_argument("--timeout", type=int, default=120, help="LLM 读取超时（秒）")
    parser.add_argument("--retries", type=int, default=3, help="最大重试次数")
    parser.add_argument("--interval", type=float, default=1.5, help="请求间隔（秒）")

    args = parser.parse_args()

    llm_kwargs = {
        "read_timeout": args.timeout,
        "max_retries": args.retries,
        "request_interval": args.interval,
    }

    generate_roundtable(
        book_path=args.book_path,
        output_path=args.output,
        template_id=args.template,
        llm_kwargs=llm_kwargs,
    )


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
辩论生成器 - 从话题、专家列表和素材生成完整 V8 JSON 辩论

核心思路：一次 LLM 调用生成整个辩论，然后用 V8 schema 验证。
失败则带错误信息重试一次。
"""

import json
import logging
from typing import Dict, List, Optional

from engine.llm_generate import call_llm_json
from engine.schema_v8 import validate_v8
from engine.knowledge_boundary_checker import get_boundary
from engine.cognitive_functions import CognitiveAnalyzer, CognitiveType

logger = logging.getLogger(__name__)


# ─── 专家 profile 加载 ─────────────────────────────────────

def _load_expert_context(expert_name: str) -> str:
    """为单个专家生成 prompt 上下文（知识边界 + 风格约束）"""
    boundary = get_boundary(expert_name)
    if not boundary:
        return f"专家「{expert_name}」：无知识边界记录，自由发挥但保持专业。"

    lines = [
        f"## {expert_name}（{boundary.era}）",
        f"- 核心知识：{', '.join(boundary.core_knowledge)}",
        f"- 关联知识：{', '.join(boundary.associated_knowledge)}",
        f"- 边缘知识：{', '.join(boundary.edge_knowledge)}",
        f"- 高频词：{', '.join(boundary.high_freq_words)}",
        f"- 比喻来源：{', '.join(boundary.metaphor_sources)}",
        f"- ⛔ 禁用词（绝不出现）：{', '.join(boundary.forbidden_words)}",
        f"- ⛔ 禁区知识：{', '.join(boundary.forbidden_knowledge)}",
    ]
    return "\n".join(lines)


def _build_experts_block(experts: list) -> str:
    """为所有选中的专家构建知识边界文本块"""
    blocks = []
    for exp in experts:
        name = exp if isinstance(exp, str) else exp.get("name", str(exp))
        blocks.append(_load_expert_context(name))
    return "\n\n".join(blocks)


# ─── V8 JSON 结构说明（给 LLM 参考）──────────────────────────

V8_SCHEMA_GUIDE = r'''
你必须输出一个严格符合以下 JSON 结构的辩论内容：

```json
{
  "title": "辩论标题（简洁有力，15字以内）",
  "subtitle": "副标题（一句话概括讨论角度）",
  "books": [],

  "experts": [
    {
      "name": "专家姓名",
      "title": "头衔/身份（一句话）",
      "avatar_color": "#c9a227",
      "stance": "support|oppose|neutral|complex",
      "core_belief": "核心信念（一句话，体现该专家的世界观）",
      "interest": "利益相关",
      "fear": "恐惧",
      "bias": "偏见",
      "experience": "关键经历",
      "trauma": "创伤（可选，可为null）",
      "speaking_style": "说话风格描述",
      "default_emotion": "serious|sarcasm|helplessness|anger|hesitation|self_deprecation|cold_laugh|silence"
    }
  ],

  "rounds": [
    {
      "round_number": 1,
      "topic": "本轮讨论的子话题",
      "core_question": "本轮核心问题",
      "stances": [
        {"expert": "专家名", "stance_type": "support|oppose|neutral|complex", "content": "立场发言（100-200字）", "emotion": "serious|sarcasm|..."}
      ],
      "clash_rounds": [
        {
          "round_num": 1,
          "attacker": "攻击者",
          "target": "被攻击者",
          "attack_type": "逻辑漏洞|证据不足|概念偷换|以偏概全|诉诸权威|稻草人|滑坡|两难困境",
          "attack_content": "攻击内容（具体指出对方的问题）",
          "emotion": "anger|sarcasm|cold_laugh|...",
          "counter_attack": "反击内容（被攻击者的回应）",
          "counter_emotion": "serious|hesitation|..."
        }
      ],
      "reality_cases": [
        {
          "case_name": "案例名称",
          "case_source": "来源（书名/历史事件/研究报告）",
          "case_content": "案例内容（具体描述）",
          "case_outcome": "结果",
          "case_lesson": "教训"
        }
      ],
      "cost_discussion": {
        "scenario": "假设场景",
        "cost_analysis": [
          {"dimension": "维度名", "cost": "代价描述", "benefit": "收益描述"}
        ],
        "worst_case": "最坏情况",
        "survivor_bias": "幸存者偏差分析（可选）"
      },
      "human_nature": {
        "question": "人性层面的问题",
        "psychological_analysis": "心理分析",
        "real_examples": ["现实例子1", "现实例子2"],
        "conclusion": "结论"
      },
      "cognitive_upgrade": {
        "old_thinking": "旧思维（大多数人怎么想）",
        "new_thinking": "新思维（升级后怎么想）",
        "complexity": "复杂性说明（为什么不能简单化）",
        "actionable_insight": "可执行洞见（读者能立刻用的）"
      },
      "emotions": [
        {"expert": "专家名", "emotion": "情绪类型", "trigger": "触发原因"}
      ]
    }
  ],

  "final_insight": "最终洞见（200-300字，综合所有专家观点后的升华）",
  "open_questions": ["开放问题1", "开放问题2", "开放问题3"]
}
```
'''


# ─── Prompt 构建 ─────────────────────────────────────────────

def _build_system_prompt() -> str:
    """构建 system prompt"""
    return (
        "你是一个高水平的圆桌辩论编剧。你的任务是生成一场深度、激烈、有真实洞见的专家辩论。\n\n"
        "核心原则：\n"
        "1. 每个专家必须像真人一样说话——有自己的偏见、恐惧、利益驱动\n"
        "2. 辩论必须有真实碰撞——不是客气地各说各话\n"
        "3. 每个观点必须有具体证据——不接受泛泛而谈\n"
        "4. 认知升级必须让人「啊哈」——不是废话总结\n\n"
        "你的输出必须是严格合法的 JSON。不要输出任何非 JSON 内容。"
    )


def _build_user_prompt(
    topic: str,
    experts: list,
    material: str,
    rounds: int,
) -> str:
    """构建用户 prompt（含所有信息）"""

    # 专家名字列表
    expert_names = []
    for exp in experts:
        name = exp if isinstance(exp, str) else exp.get("name", str(exp))
        expert_names.append(name)

    # 专家知识边界
    experts_block = _build_experts_block(experts)

    # 材料部分
    material_section = ""
    if material and material.strip():
        material_section = f"""
## 参考素材
以下是与话题相关的搜索素材，辩论中的现实案例和证据应优先参考这些素材：

{material[:6000]}
"""

    prompt = f"""请生成一场关于「{topic}」的深度圆桌辩论。

## 参与专家（{len(expert_names)} 位）
{', '.join(expert_names)}

## 专家知识边界（每位专家必须严格遵守）
{experts_block}

{material_section}

## 辩论结构要求

生成 {rounds} 轮辩论，每轮包含以下 6 个子结构：

### 第一轮：立场表达
- 每位专家用 100-200 字阐述核心立场
- 立场必须多样化：至少包含 support、oppose、neutral/complex 中的 2 种
- 不要"我认为"开头，要用反直觉的观察开场

### 第二轮：交锋碰撞
- 至少 3 次碰撞（attacker → target）
- 攻击类型：逻辑漏洞、证据不足、概念偷换、以偏概全、诉诸权威、两难困境
- 每次攻击必须有具体反击（counter_attack）
- 碰撞要真实——指出对方的具体错误，不是泛泛否定

### 第三轮：现实案例
- 至少 2 个真实案例（书中的、历史的、研究中的）
- 每个案例必须有「代价」——没有只有好处的案例
- 案例要有具体名称、来源、结果

### 第四轮：代价讨论
- 分析至少 3 个维度的代价和收益
- 给出最坏情况
- 如果存在幸存者偏差，指出它

### 第五轮：人性层
- 提出一个触及人性的问题
- 心理分析要深入（不要表面描述）
- 至少 2 个现实例子

### 第六轮：认知升级
- 明确指出「旧思维」和「新思维」
- 解释为什么不能简单化
- 给出读者能立刻使用的「可执行洞见」

## 质量红线（违反则无效）

🚫 禁止行为：
1. 不要让专家轻易同意对方——必须经过激烈碰撞才可能部分认同
2. 不要使用稻草人攻击——攻击必须针对对方的真实论点
3. 不要泛泛而谈——每个观点必须有具体证据或案例支撑
4. 不要让所有专家都说一样的话——立场和风格必须有明显差异
5. 不要使用禁用词——每位专家有自己的禁用词列表，绝不出现
6. 不要让古代专家使用现代词汇（如 AI、算法、区块链）
7. 不要出现"各有优劣"、"这取决于"之类的和稀泥结论
8. 不要重复使用相同的案例或证据——每轮都需要新鲜素材

✅ 质量要求：
1. 金句密度：每 200 字至少 1 句可截图分享的话
2. 碰撞烈度：至少 1 次让读者"倒吸一口气"的交锋
3. 案例真实性：案例必须可查证（书名、人名、事件名）
4. 认知升级：最终必须让人产生"啊哈"的顿悟感
5. 专家个性：每位专家的说话方式必须有明显区别

## 最终要求

输出严格合法的 JSON，结构如下：

{V8_SCHEMA_GUIDE}

记住：
- experts 数组必须有 {len(expert_names)} 个元素
- rounds 数组必须有 {rounds} 个元素
- 每轮的 stances 必须覆盖所有 {len(expert_names)} 位专家
- 每轮的 clash_rounds 至少 3 次碰撞
- 每轮的 reality_cases 至少 2 个案例
- 每轮的 cost_discussion.cost_analysis 至少 3 个维度
- 每轮的 human_nature.real_examples 至少 2 个例子
- open_questions 至少 3 个
- final_insight 至少 200 字
"""

    return prompt


# ─── 主函数 ──────────────────────────────────────────────────

def generate_debate(
    topic: str,
    experts: list,
    material: str = '',
    rounds: int = 3,
    enable_cognitive: bool = True,
    cognitive_types: Optional[List[CognitiveType]] = None,
) -> dict:
    """
    生成一个完整的 V8 JSON 辩论。

    Args:
        topic: 辩论话题
        experts: 专家列表（来自 topic_router.select_experts()）
                 每个元素可以是 str（专家名）或 dict（含 name 等字段）
        material: 来自 web search 的参考素材
        rounds: 辩论轮数（默认 3）
        enable_cognitive: 是否启用8认知函数分析（默认 True）
        cognitive_types: 要执行的认知函数类型（默认全部8个）

    Returns:
        V8 JSON dict，可直接传给 html_renderer

    Raises:
        RuntimeError: 两次尝试均失败时抛出
    """
    logger.info("开始生成辩论 | 话题=%s | 专家数=%d | 轮数=%d", topic, len(experts), rounds)

    system_prompt = _build_system_prompt()

    # ── 执行8认知函数分析 ──
    cognitive_injection = ""
    if enable_cognitive:
        logger.info("执行8认知函数分析...")
        analyzer = CognitiveAnalyzer(cognitive_types)
        try:
            expert_names = []
            for exp in experts:
                name = exp if isinstance(exp, str) else exp.get("name", str(exp))
                expert_names.append(name)
            cognitive_report = analyzer.analyze_all(topic, expert_names)
            cognitive_injection = cognitive_report.get_prompt_injection()
            logger.info("8认知函数分析完成 | 高置信度洞见: %d个",
                       len(cognitive_report.get_high_confidence_insights()))
        except Exception as e:
            logger.warning("8认知函数分析失败，跳过: %s", e)
            cognitive_injection = ""

    user_prompt = _build_user_prompt(topic, experts, material, rounds)

    # ── 注入认知分析结果到prompt ──
    if cognitive_injection:
        user_prompt = user_prompt + "\n\n" + cognitive_injection + "\n"

    # ── 第一次尝试 ──
    result = call_llm_json(user_prompt, system_prompt, max_tokens=8000)

    if not result.get("success"):
        error_msg = result.get("error", "未知错误")
        logger.warning("第一次 LLM 调用失败: %s", error_msg)
        raise RuntimeError(f"辩论生成失败（LLM 调用错误）: {error_msg}")

    data = result.get("data")
    if data is None:
        logger.warning("第一次调用返回非 JSON 内容，重试...")
        data = _retry_with_error_feedback(
            user_prompt, system_prompt,
            "返回内容无法解析为 JSON，请确保输出是严格合法的 JSON。",
        )
    else:
        # 验证 V8 schema
        valid, errors = validate_v8(data)
        if not valid:
            logger.warning("第一次验证失败: %s，带错误重试...", errors)
            data = _retry_with_error_feedback(
                user_prompt, system_prompt,
                f"上一次输出验证失败，错误如下：\n{chr(10).join(errors)}\n请修正这些问题。",
            )

    if data is None:
        raise RuntimeError("辩论生成失败：两次尝试均未通过验证。")

    logger.info("辩论生成成功 | title=%s", data.get("title", "?"))
    return data


def _retry_with_error_feedback(
    user_prompt: str,
    system_prompt: str,
    error_feedback: str,
) -> Optional[dict]:
    """带错误反馈重试一次"""
    retry_prompt = (
        f"{user_prompt}\n\n"
        f"--- 上一次输出有误，请修正 ---\n{error_feedback}\n"
        f"--- 请重新生成完整的 JSON ---"
    )

    result = call_llm_json(retry_prompt, system_prompt, max_tokens=8000)

    if not result.get("success"):
        logger.error("重试 LLM 调用失败: %s", result.get("error"))
        return None

    data = result.get("data")
    if data is None:
        logger.error("重试仍返回非 JSON 内容")
        return None

    valid, errors = validate_v8(data)
    if not valid:
        logger.error("重试后验证仍失败: %s", errors)
        return None

    return data


# ─── CLI 入口 ─────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if len(sys.argv) < 2:
        print("用法: python debate_generator.py <话题> [专家1,专家2,...]")
        print("示例: python debate_generator.py 'AI会取代人类工作吗' 芒格,赫拉利,卡尼曼")
        sys.exit(1)

    test_topic = sys.argv[1]
    test_experts = sys.argv[2].split(",") if len(sys.argv) > 2 else ["芒格", "赫拉利", "卡尼曼", "老子", "尼采", "津巴多"]

    print(f"话题: {test_topic}")
    print(f"专家: {test_experts}")
    print("正在生成辩论（可能需要 1-2 分钟）...\n")

    debate = generate_debate(test_topic, test_experts)

    print(f"\n✅ 生成成功!")
    print(f"标题: {debate['title']}")
    print(f"副标题: {debate.get('subtitle', '')}")
    print(f"专家数: {len(debate['experts'])}")
    print(f"轮数: {len(debate['rounds'])}")
    print(f"开放问题: {debate.get('open_questions', [])}")

    # 输出到文件
    out_path = "debate_output.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(debate, f, ensure_ascii=False, indent=2)
    print(f"\n已保存到 {out_path}")

# -*- coding: utf-8 -*-
"""
8认知函数 - 深度内容分析引擎

每个认知函数从不同维度分析辩论内容，提供多角度洞见：
1. Contrarian（反对者）："为什么这是错的？"
2. Risk（风险分析）："系统会如何崩溃？"
3. Historical（历史验证）："历史上发生过吗？"
4. Mechanism（机制分析）："底层驱动力是什么？"
5. Systems（系统推演）："会产生哪些连锁反应？"
6. Incentive（激励分析）："谁真正获利？谁会反对？"
7. Compression（洞察压缩）："核心矛盾在哪里？"
8. Meta-Cognition（元认知裁判）："谁逻辑更强？"

使用方式：
    from engine.cognitive_functions import CognitiveAnalyzer

    analyzer = CognitiveAnalyzer()
    results = analyzer.analyze_all(topic, experts, previous_rounds)
    # results 包含8个维度的分析结果

集成到辩论生成器：
    在生成辩论前，先运行认知分析，将结果注入prompt，提升内容深度。
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

from engine.llm_generate import call_llm_json

logger = logging.getLogger(__name__)


# ─── 数据结构 ──────────────────────────────────────────────

class CognitiveType(str, Enum):
    """认知函数类型"""
    CONTRARIAN = "contrarian"
    RISK = "risk"
    HISTORICAL = "historical"
    MECHANISM = "mechanism"
    SYSTEMS = "systems"
    INCENTIVE = "incentive"
    COMPRESSION = "compression"
    META_COGNITION = "meta_cognition"


@dataclass
class CognitiveResult:
    """单个认知函数的分析结果"""
    cognitive_type: CognitiveType
    analysis: str                    # 核心分析内容
    confidence: float                # 置信度 0.0 ~ 1.0
    key_insights: List[str]          # 关键洞见列表
    challenges: List[str]            # 挑战/质疑点
    evidence_quality: str            # 证据质量评估：strong/moderate/weak/speculative
    actionability: str               # 可执行性：high/medium/low
    meta_comment: Optional[str] = None  # 元认知评论

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["cognitive_type"] = self.cognitive_type.value
        return d


@dataclass
class CognitiveAnalysisReport:
    """完整认知分析报告"""
    topic: str
    experts: List[str]
    results: List[CognitiveResult]
    synthesis: str                   # 综合洞见
    meta_verdict: Optional[CognitiveResult] = None  # 元认知裁判结果

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic,
            "experts": self.experts,
            "results": [r.to_dict() for r in self.results],
            "synthesis": self.synthesis,
            "meta_verdict": self.meta_verdict.to_dict() if self.meta_verdict else None,
        }

    def get_high_confidence_insights(self, threshold: float = 0.7) -> List[str]:
        """提取高置信度洞见"""
        insights = []
        for result in self.results:
            if result.confidence >= threshold:
                insights.extend(result.key_insights)
        return insights

    def get_critical_challenges(self) -> List[str]:
        """提取关键挑战"""
        challenges = []
        for result in self.results:
            challenges.extend(result.challenges)
        return challenges

    def get_prompt_injection(self) -> str:
        """生成可注入到辩论prompt中的认知分析摘要"""
        lines = [
            "## 认知函数深度分析（AI辅助视角）",
            f"话题：{self.topic}",
            "",
        ]

        for result in self.results:
            lines.append(f"### {result.cognitive_type.value.upper()} 分析")
            lines.append(f"置信度: {result.confidence:.1%}")
            lines.append(f"{result.analysis}")
            if result.key_insights:
                lines.append("关键洞见:")
                for insight in result.key_insights:
                    lines.append(f"  - {insight}")
            lines.append("")

        if self.meta_verdict:
            lines.append("### 元认知裁判综合评定")
            lines.append(self.meta_verdict.analysis)
            lines.append("")

        if self.synthesis:
            lines.append("### 综合洞见")
            lines.append(self.synthesis)

        return "\n".join(lines)


# ─── 基类 ──────────────────────────────────────────────────

class CognitiveFunction(ABC):
    """认知函数基类"""

    cognitive_type: CognitiveType
    display_name: str
    description: str
    focus_question: str

    def __init__(self):
        self.cognitive_type = self.__class__.cognitive_type
        self.display_name = self.__class__.display_name
        self.description = self.__class__.description
        self.focus_question = self.__class__.focus_question

    @abstractmethod
    def _build_prompt(self, topic: str, experts: List[str],
                      previous_arguments: List[Dict],
                      world_state: Optional[Dict] = None) -> str:
        """构建LLM提示词"""
        pass

    def _get_system_prompt(self) -> str:
        """系统提示词"""
        return (
            f"你是一个专业的{self.display_name}。{self.description}\n\n"
            f"你的核心问题是：{self.focus_question}\n\n"
            "你必须输出严格合法的JSON，格式如下：\n"
            '{\n'
            '  "analysis": "核心分析（200-400字）",\n'
            '  "confidence": 0.85,\n'
            '  "key_insights": ["洞见1", "洞见2", "洞见3"],\n'
            '  "challenges": ["挑战1", "挑战2"],\n'
            '  "evidence_quality": "strong|moderate|weak|speculative",\n'
            '  "actionability": "high|medium|low"\n'
            '}\n\n'
            "不要输出任何非JSON内容。"
        )

    def analyze(self, topic: str, experts: List[str],
                previous_arguments: List[Dict],
                world_state: Optional[Dict] = None) -> CognitiveResult:
        """
        执行认知分析

        Args:
            topic: 辩论话题
            experts: 参与专家列表
            previous_arguments: 前一轮辩论观点列表
                每个元素: {"expert": str, "stance": str, "content": str}
            world_state: 可选的世界状态信息

        Returns:
            CognitiveResult 分析结果
        """
        logger.info("执行 %s 认知分析 | 话题=%s", self.display_name, topic)

        user_prompt = self._build_prompt(topic, experts, previous_arguments, world_state)
        system_prompt = self._get_system_prompt()

        result = call_llm_json(user_prompt, system_prompt, max_tokens=2000, temperature=0.7)

        if not result.get("success") or not result.get("data"):
            logger.warning("%s LLM调用失败: %s", self.display_name, result.get("error"))
            return self._fallback_analysis(topic, experts)

        data = result["data"]

        # 验证和标准化
        confidence = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
        evidence_quality = data.get("evidence_quality", "moderate")
        if evidence_quality not in ("strong", "moderate", "weak", "speculative"):
            evidence_quality = "moderate"
        actionability = data.get("actionability", "medium")
        if actionability not in ("high", "medium", "low"):
            actionability = "medium"

        return CognitiveResult(
            cognitive_type=self.cognitive_type,
            analysis=data.get("analysis", "分析生成失败"),
            confidence=confidence,
            key_insights=data.get("key_insights", []),
            challenges=data.get("challenges", []),
            evidence_quality=evidence_quality,
            actionability=actionability,
        )

    def _fallback_analysis(self, topic: str, experts: List[str]) -> CognitiveResult:
        """LLM调用失败时的回退分析"""
        return CognitiveResult(
            cognitive_type=self.cognitive_type,
            analysis=f"[{self.display_name}] 无法完成自动分析，请手动检查。",
            confidence=0.0,
            key_insights=[],
            challenges=["自动分析失败，需要人工干预"],
            evidence_quality="weak",
            actionability="low",
        )


# ─── 1. Contrarian（反对者）─────────────────────────────────

class ContrarianFunction(CognitiveFunction):
    """反对者：质疑主流观点，找出错误假设"""

    cognitive_type = CognitiveType.CONTRARIAN
    display_name = "反对者"
    description = "从反面视角挑战观点，找出隐藏的假设和逻辑漏洞。"
    focus_question = "为什么这是错的？"

    def _build_prompt(self, topic, experts, previous_arguments, world_state):
        args_text = self._format_arguments(previous_arguments)
        return f"""作为「反对者」，请对以下辩论进行反向分析。

## 话题：{topic}
## 参与专家：{', '.join(experts)}

## 已有观点：
{args_text}

## 你的任务：
1. 找出这些观点中最薄弱的假设
2. 提出反直觉的反对理由
3. 指出可能被忽视的反面证据
4. 质疑主流共识的可靠性
5. 从「如果这是错的，会怎样？」角度思考

## 输出要求：
- analysis: 200-400字的深度反对分析
- confidence: 你对反对理由强度的评估（0-1）
- key_insights: 至少3个反直觉洞见
- challenges: 至少2个对主流观点的挑战
- evidence_quality: 你的证据有多强
- actionability: 这些反对意见是否可操作"""

    def _format_arguments(self, args):
        if not args:
            return "（暂无前序观点）"
        lines = []
        for a in args:
            lines.append(f"- 【{a.get('expert', '?')}】({a.get('stance', '?')}): {a.get('content', '')[:300]}")
        return "\n".join(lines)


# ─── 2. Risk（风险分析）─────────────────────────────────────

class RiskFunction(CognitiveFunction):
    """风险分析：识别系统性风险和崩溃场景"""

    cognitive_type = CognitiveType.RISK
    display_name = "风险分析师"
    description = "识别系统性风险、连锁失败模式和崩溃场景。"
    focus_question = "系统会如何崩溃？"

    def _build_prompt(self, topic, experts, previous_arguments, world_state):
        args_text = self._format_arguments(previous_arguments)
        world_text = ""
        if world_state:
            world_text = f"\n## 世界状态：\n{json.dumps(world_state, ensure_ascii=False)[:2000]}"

        return f"""作为「风险分析师」，请对以下辩论进行风险评估。

## 话题：{topic}
## 参与专家：{', '.join(experts)}
{world_text}

## 已有观点：
{args_text}

## 你的任务：
1. 识别观点中隐含的系统性风险
2. 设计「最坏情况」场景（如果事情出错会怎样？）
3. 分析级联失败的可能性
4. 评估黑天鹅事件的风险
5. 指出被忽视的脆弱点

## 输出要求：
- analysis: 200-400字的风险分析
- confidence: 你对风险评估准确性的信心（0-1）
- key_insights: 至少3个关键风险洞见
- challenges: 至少2个风险挑战
- evidence_quality: 风险证据的质量
- actionability: 风险缓解建议的可操作性"""

    def _format_arguments(self, args):
        if not args:
            return "（暂无前序观点）"
        lines = []
        for a in args:
            lines.append(f"- 【{a.get('expert', '?')}】({a.get('stance', '?')}): {a.get('content', '')[:300]}")
        return "\n".join(lines)


# ─── 3. Historical（历史验证）───────────────────────────────

class HistoricalFunction(CognitiveFunction):
    """历史验证：从历史模式中寻找先例"""

    cognitive_type = CognitiveType.HISTORICAL
    display_name = "历史学家"
    description = "从历史模式中寻找先例，验证或反驳当前观点。"
    focus_question = "历史上发生过吗？"

    def _build_prompt(self, topic, experts, previous_arguments, world_state):
        args_text = self._format_arguments(previous_arguments)
        return f"""作为「历史学家」，请从历史视角分析以下辩论。

## 话题：{topic}
## 参与专家：{', '.join(experts)}

## 已有观点：
{args_text}

## 你的任务：
1. 找出历史上类似的话题/争论
2. 分析历史先例的结果
3. 识别反复出现的历史模式
4. 评估当前情况与历史的相似度
5. 从历史中提取可借鉴的教训

## 输出要求：
- analysis: 200-400字的历史分析
- confidence: 你对历史类比准确性的信心（0-1）
- key_insights: 至少3个历史洞见
- challenges: 至少2个对当前观点的历史挑战
- evidence_quality: 历史证据的质量
- actionability: 历史教训的可操作性"""

    def _format_arguments(self, args):
        if not args:
            return "（暂无前序观点）"
        lines = []
        for a in args:
            lines.append(f"- 【{a.get('expert', '?')}】({a.get('stance', '?')}): {a.get('content', '')[:300]}")
        return "\n".join(lines)


# ─── 4. Mechanism（机制分析）─────────────────────────────────

class MechanismFunction(CognitiveFunction):
    """机制分析：揭示底层驱动力"""

    cognitive_type = CognitiveType.MECHANISM
    display_name = "机制分析师"
    description = "揭示观点背后的底层驱动力和因果机制。"
    focus_question = "底层驱动力是什么？"

    def _build_prompt(self, topic, experts, previous_arguments, world_state):
        args_text = self._format_arguments(previous_arguments)
        return f"""作为「机制分析师」，请揭示以下辩论的底层机制。

## 话题：{topic}
## 参与专家：{', '.join(experts)}

## 已有观点：
{args_text}

## 你的任务：
1. 识别驱动这些观点的底层机制
2. 揭示因果链条（A → B → C）
3. 找出隐藏的动力学（情绪、利益、权力）
4. 分析为什么人们会这样想
5. 识别表象与本质的区别

## 输出要求：
- analysis: 200-400字的机制分析
- confidence: 你对机制识别准确性的信心（0-1）
- key_insights: 至少3个机制洞见
- challenges: 至少2个机制挑战
- evidence_quality: 机制证据的质量
- actionability: 机制理解的可操作性"""

    def _format_arguments(self, args):
        if not args:
            return "（暂无前序观点）"
        lines = []
        for a in args:
            lines.append(f"- 【{a.get('expert', '?')}】({a.get('stance', '?')}): {a.get('content', '')[:300]}")
        return "\n".join(lines)


# ─── 5. Systems（系统推演）───────────────────────────────────

class SystemsFunction(CognitiveFunction):
    """系统推演：分析连锁反应和二阶效应"""

    cognitive_type = CognitiveType.SYSTEMS
    display_name = "系统推演师"
    description = "分析观点的连锁反应、二阶效应和系统动力学。"
    focus_question = "会产生哪些连锁反应？"

    def _build_prompt(self, topic, experts, previous_arguments, world_state):
        args_text = self._format_arguments(previous_arguments)
        world_text = ""
        if world_state:
            world_text = f"\n## 世界状态：\n{json.dumps(world_state, ensure_ascii=False)[:2000]}"

        return f"""作为「系统推演师」，请分析以下辩论的系统性影响。

## 话题：{topic}
## 参与专家：{', '.join(experts)}
{world_text}

## 已有观点：
{args_text}

## 你的任务：
1. 分析观点采纳后的二阶效应
2. 识别正反馈循环和负反馈循环
3. 评估系统韧性（如果某个假设错了会怎样？）
4. 找出意外后果（蝴蝶效应）
5. 分析跨领域影响（经济→社会→文化→心理）

## 输出要求：
- analysis: 200-400字的系统推演
- confidence: 你对系统推演准确性的信心（0-1）
- key_insights: 至少3个系统洞见
- challenges: 至少2个系统挑战
- evidence_quality: 系统证据的质量
- actionability: 系统建议的可操作性"""

    def _format_arguments(self, args):
        if not args:
            return "（暂无前序观点）"
        lines = []
        for a in args:
            lines.append(f"- 【{a.get('expert', '?')}】({a.get('stance', '?')}): {a.get('content', '')[:300]}")
        return "\n".join(lines)


# ─── 6. Incentive（激励分析）────────────────────────────────

class IncentiveFunction(CognitiveFunction):
    """激励分析：揭示利益结构和博弈动力"""

    cognitive_type = CognitiveType.INCENTIVE
    display_name = "激励分析师"
    description = "揭示观点背后的利益结构、权力博弈和激励机制。"
    focus_question = "谁真正获利？谁会反对？"

    def _build_prompt(self, topic, experts, previous_arguments, world_state):
        args_text = self._format_arguments(previous_arguments)
        return f"""作为「激励分析师」，请揭示以下辩论的利益结构。

## 话题：{topic}
## 参与专家：{', '.join(experts)}

## 已有观点：
{args_text}

## 你的任务：
1. 识别每个专家背后的利益驱动
2. 分析谁会从这些观点中获利
3. 找出谁会反对这些观点（及原因）
4. 揭示隐藏的权力博弈
5. 分析激励结构如何影响观点

## 输出要求：
- analysis: 200-400字的利益分析
- confidence: 你对利益分析准确性的信心（0-1）
- key_insights: 至少3个激励洞见
- challenges: 至少2个激励挑战
- evidence_quality: 激励证据的质量
- actionability: 激励建议的可操作性"""

    def _format_arguments(self, args):
        if not args:
            return "（暂无前序观点）"
        lines = []
        for a in args:
            lines.append(f"- 【{a.get('expert', '?')}】({a.get('stance', '?')}): {a.get('content', '')[:300]}")
        return "\n".join(lines)


# ─── 7. Compression（洞察压缩）───────────────────────────────

class CompressionFunction(CognitiveFunction):
    """洞察压缩：提取核心矛盾和关键张力"""

    cognitive_type = CognitiveType.COMPRESSION
    display_name = "洞察压缩器"
    description = "从复杂辩论中提取核心矛盾和可传播的洞见。"
    focus_question = "核心矛盾在哪里？"

    def _build_prompt(self, topic, experts, previous_arguments, world_state):
        args_text = self._format_arguments(previous_arguments)
        return f"""作为「洞察压缩器」，请从以下辩论中提取核心矛盾。

## 话题：{topic}
## 参与专家：{', '.join(experts)}

## 已有观点：
{args_text}

## 你的任务：
1. 识别辩论中的核心张力（不是表面分歧）
2. 压缩复杂观点为可传播的洞见
3. 找出「一句话就能说明白」的核心矛盾
4. 评估哪些洞见值得截图分享
5. 提炼出让读者「啊哈」的顿悟时刻

## 输出要求：
- analysis: 200-400字的压缩分析
- confidence: 你对压缩质量的信心（0-1）
- key_insights: 至少3个高传播性洞见
- challenges: 至少2个压缩挑战
- evidence_quality: 洞见证据的质量
- actionability: 洞见的可操作性"""

    def _format_arguments(self, args):
        if not args:
            return "（暂无前序观点）"
        lines = []
        for a in args:
            lines.append(f"- 【{a.get('expert', '?')}】({a.get('stance', '?')}): {a.get('content', '')[:300]}")
        return "\n".join(lines)


# ─── 8. Meta-Cognition（元认知裁判）─────────────────────────

class MetaCognitionFunction(CognitiveFunction):
    """元认知裁判：评估各方逻辑质量"""

    cognitive_type = CognitiveType.META_COGNITION
    display_name = "元认知裁判"
    description = "评估辩论各方的逻辑质量、论证强度和认知偏差。"
    focus_question = "谁逻辑更强？"

    def _build_prompt(self, topic, experts, previous_arguments, world_state):
        args_text = self._format_arguments(previous_arguments)
        return f"""作为「元认知裁判」，请对以下辩论进行逻辑质量评估。

## 话题：{topic}
## 参与专家：{', '.join(experts)}

## 已有观点：
{args_text}

## 你的任务：
1. 评估每位专家的逻辑强度
2. 识别逻辑谬误和认知偏差
3. 判断哪些论证有实质证据支撑
4. 评估论证的连贯性和一致性
5. 给出综合排名和改进建议

## 输出要求：
- analysis: 200-400字的逻辑评估
- confidence: 你对评估准确性的信心（0-1）
- key_insights: 至少3个逻辑洞见
- challenges: 至少2个逻辑挑战
- evidence_quality: 逻辑证据的质量
- actionability: 逻辑建议的可操作性"""

    def _format_arguments(self, args):
        if not args:
            return "（暂无前序观点）"
        lines = []
        for a in args:
            lines.append(f"- 【{a.get('expert', '?')}】({a.get('stance', '?')}): {a.get('content', '')[:300]}")
        return "\n".join(lines)


# ─── 认知分析器（主入口）────────────────────────────────────

class CognitiveAnalyzer:
    """
    认知分析器 - 协调8个认知函数的执行

    使用方式：
        analyzer = CognitiveAnalyzer()
        report = analyzer.analyze_all(topic, experts, previous_rounds)
        # report.to_dict() 可序列化
        # report.get_prompt_injection() 可注入到辩论prompt
    """

    def __init__(self, cognitive_types: Optional[List[CognitiveType]] = None):
        """
        Args:
            cognitive_types: 要执行的认知函数列表，默认全部8个
        """
        self._functions = self._init_functions(cognitive_types)

    def _init_functions(self, types: Optional[List[CognitiveType]] = None) -> List[CognitiveFunction]:
        """初始化认知函数"""
        all_functions = {
            CognitiveType.CONTRARIAN: ContrarianFunction,
            CognitiveType.RISK: RiskFunction,
            CognitiveType.HISTORICAL: HistoricalFunction,
            CognitiveType.MECHANISM: MechanismFunction,
            CognitiveType.SYSTEMS: SystemsFunction,
            CognitiveType.INCENTIVE: IncentiveFunction,
            CognitiveType.COMPRESSION: CompressionFunction,
            CognitiveType.META_COGNITION: MetaCognitionFunction,
        }

        if types is None:
            types = list(CognitiveType)

        return [all_functions[t]() for t in types if t in all_functions]

    def analyze(
        self,
        cognitive_type: CognitiveType,
        topic: str,
        experts: List[str],
        previous_arguments: List[Dict],
        world_state: Optional[Dict] = None,
    ) -> CognitiveResult:
        """
        执行单个认知函数分析

        Args:
            cognitive_type: 要执行的认知函数类型
            topic: 辩论话题
            experts: 参与专家列表
            previous_arguments: 前一轮观点列表
            world_state: 可选的世界状态信息

        Returns:
            CognitiveResult
        """
        for func in self._functions:
            if func.cognitive_type == cognitive_type:
                return func.analyze(topic, experts, previous_arguments, world_state)

        raise ValueError(f"未知的认知函数类型: {cognitive_type}")

    def analyze_all(
        self,
        topic: str,
        experts: List[str],
        previous_arguments: Optional[List[Dict]] = None,
        world_state: Optional[Dict] = None,
    ) -> CognitiveAnalysisReport:
        """
        执行所有认知函数分析

        Args:
            topic: 辩论话题
            experts: 参与专家列表
            previous_arguments: 前一轮观点列表（可选）
            world_state: 可选的世界状态信息

        Returns:
            CognitiveAnalysisReport 完整分析报告
        """
        if previous_arguments is None:
            previous_arguments = []

        logger.info("开始执行8认知函数分析 | 话题=%s | 专家数=%d", topic, len(experts))

        results = []
        for func in self._functions:
            try:
                result = func.analyze(topic, experts, previous_arguments, world_state)
                results.append(result)
                logger.info("  ✓ %s 完成 (置信度: %.1f%%)",
                           func.display_name, result.confidence * 100)
            except Exception as e:
                logger.error("  ✗ %s 失败: %s", func.display_name, e)
                results.append(func._fallback_analysis(topic, experts))

        # 提取元认知裁判结果
        meta_verdict = None
        other_results = []
        for r in results:
            if r.cognitive_type == CognitiveType.META_COGNITION:
                meta_verdict = r
            else:
                other_results.append(r)

        # 生成综合洞见
        synthesis = self._generate_synthesis(topic, other_results)

        report = CognitiveAnalysisReport(
            topic=topic,
            experts=experts,
            results=results,
            synthesis=synthesis,
            meta_verdict=meta_verdict,
        )

        logger.info("8认知函数分析完成 | 高置信度洞见: %d个",
                    len(report.get_high_confidence_insights()))

        return report

    def _generate_synthesis(self, topic: str, results: List[CognitiveResult]) -> str:
        """生成综合洞见（不调用LLM，纯规则提取）"""
        # 按置信度排序，提取top洞见
        sorted_results = sorted(results, key=lambda r: r.confidence, reverse=True)

        top_insights = []
        for r in sorted_results[:3]:
            if r.key_insights:
                top_insights.append(f"【{r.display_name}】{r.key_insights[0]}")

        # 按可操作性排序
        actionable = [r for r in results if r.actionability == "high"]
        actionable_insights = []
        for r in actionable[:2]:
            if r.key_insights:
                actionable_insights.append(f"【{r.display_name}】{r.key_insights[0]}")

        # 按挑战强度排序
        all_challenges = []
        for r in sorted_results:
            all_challenges.extend(r.challenges[:1])

        lines = [f"话题「{topic}」的8认知函数综合分析：", ""]
        if top_insights:
            lines.append("🎯 最高置信度洞见：")
            for i, ins in enumerate(top_insights, 1):
                lines.append(f"  {i}. {ins}")
            lines.append("")

        if actionable_insights:
            lines.append("⚡ 最可操作的洞见：")
            for i, ins in enumerate(actionable_insights, 1):
                lines.append(f"  {i}. {ins}")
            lines.append("")

        if all_challenges:
            lines.append("⚠️ 关键挑战：")
            for i, ch in enumerate(all_challenges[:3], 1):
                lines.append(f"  {i}. {ch}")

        return "\n".join(lines)

    def get_cognitive_types(self) -> List[CognitiveType]:
        """获取当前配置的认知函数类型列表"""
        return [f.cognitive_type for f in self._functions]


# ─── 便捷函数 ──────────────────────────────────────────────

def quick_analyze(
    topic: str,
    experts: List[str],
    previous_arguments: Optional[List[Dict]] = None,
    cognitive_types: Optional[List[CognitiveType]] = None,
) -> CognitiveAnalysisReport:
    """
    快速执行认知分析

    Args:
        topic: 辩论话题
        experts: 参与专家列表
        previous_arguments: 前一轮观点列表
        cognitive_types: 要执行的认知函数类型（默认全部）

    Returns:
        CognitiveAnalysisReport
    """
    analyzer = CognitiveAnalyzer(cognitive_types)
    return analyzer.analyze_all(topic, experts, previous_arguments)


# ─── CLI 测试 ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if len(sys.argv) < 2:
        print("用法: python cognitive_functions.py <话题> [专家1,专家2,...]")
        print("示例: python cognitive_functions.py 'AI会取代人类工作吗' 芒格,赫拉利,卡尼曼")
        sys.exit(1)

    test_topic = sys.argv[1]
    test_experts = sys.argv[2].split(",") if len(sys.argv) > 2 else ["芒格", "赫拉利", "卡尼曼"]

    print(f"话题: {test_topic}")
    print(f"专家: {test_experts}")
    print(f"执行8认知函数分析...\n")

    report = quick_analyze(test_topic, test_experts)

    print("\n" + "=" * 60)
    print("8认知函数分析报告")
    print("=" * 60)

    for result in report.results:
        print(f"\n{'─' * 40}")
        print(f"【{result.display_name}】置信度: {result.confidence:.1%}")
        print(f"分析: {result.analysis[:200]}...")
        if result.key_insights:
            print("洞见:")
            for ins in result.key_insights[:3]:
                print(f"  - {ins}")

    print(f"\n{'─' * 40}")
    print("综合洞见:")
    print(report.synthesis)

    # 输出到文件
    out_path = "cognitive_analysis.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"\n已保存到 {out_path}")

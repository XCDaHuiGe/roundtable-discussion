# -*- coding: utf-8 -*-
"""V11 三轮圆桌训练记录与 Markdown 渲染。"""

from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass
class RoundScore:
    factual_robustness: int
    insight_delta: int
    conflict_strength: int
    persona_consistency: int
    structure: int
    practical_usefulness: int
    empty_talk_rate: int

    def lowest_dimension(self) -> str:
        values = {
            "factual_robustness": self.factual_robustness,
            "insight_delta": self.insight_delta,
            "conflict_strength": self.conflict_strength,
            "persona_consistency": self.persona_consistency,
            "structure": self.structure,
            "practical_usefulness": self.practical_usefulness,
            "empty_talk_rate": 10 - self.empty_talk_rate,
        }
        return min(values, key=values.get)

    def as_markdown(self) -> str:
        lines = []
        for field in fields(self):
            lines.append(f"- {field.name}: {getattr(self, field.name)}")
        return "\n".join(lines)


@dataclass
class TrainingRound:
    round_number: int
    purpose: str
    original: str
    score: RoundScore
    lowest_dimension: str
    rewrite_instruction: str
    rewritten: str


@dataclass
class TrainingTopic:
    title: str
    definition: str
    controversy_map: str
    experts: list[str]
    rounds: list[TrainingRound]
    final_insights: list[str]


def render_full_markdown(topic: TrainingTopic) -> str:
    parts = [
        f"# {topic.title} - 完整训练日志",
        "",
        "## 话题定义",
        topic.definition,
        "",
        "## 争议地图",
        topic.controversy_map,
        "",
        "## 入选专家",
        "\n".join(f"- {expert}" for expert in topic.experts),
    ]
    for item in topic.rounds:
        parts.extend(
            [
                "",
                f"## 第 {item.round_number} 轮：{item.purpose}",
                "",
                "### 原稿",
                item.original,
                "",
                "### Agent 评分",
                item.score.as_markdown(),
                "",
                "### 最低分项",
                item.lowest_dimension,
                "",
                "### 局部重写指令",
                item.rewrite_instruction,
                "",
                "### 重写稿",
                item.rewritten,
            ]
        )
    parts.extend(["", "## 最终洞见"])
    parts.extend(f"- {insight}" for insight in topic.final_insights)
    return "\n".join(parts).rstrip() + "\n"


def render_report_markdown(topic: TrainingTopic) -> str:
    parts = [
        f"# {topic.title} - 最终报告",
        "",
        "## 话题定义",
        topic.definition,
        "",
        "## 争议地图",
        topic.controversy_map,
        "",
        "## 入选专家",
        "\n".join(f"- {expert}" for expert in topic.experts),
    ]
    for item in topic.rounds:
        parts.extend(
            [
                "",
                f"## 第 {item.round_number} 轮：{item.purpose}",
                item.rewritten,
            ]
        )
    parts.extend(["", "## 关键洞见"])
    parts.extend(f"- {insight}" for insight in topic.final_insights)
    return "\n".join(parts).rstrip() + "\n"

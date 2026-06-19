# -*- coding: utf-8 -*-
from __future__ import annotations

import re

from engine.cognitive_model.schema import CognitiveModel, QualityIssue


def _is_placeholder_tension(tension_axis: str) -> bool:
    """检查张力轴是否是占位符（如"第N轮张力"）"""
    if not tension_axis:
        return False
    # 匹配 "第1轮张力"、"第2轮张力" 等占位符
    return bool(re.match(r"^第\d+轮张力$", tension_axis.strip()))


def validate_roundtable_quality(model: CognitiveModel) -> dict[str, object]:
    errors: list[QualityIssue] = []
    if not model.roundtable.participants:
        errors.append(QualityIssue("error", "missing_participants", "缺少专家参与者", "roundtable.participants"))

    total_rounds = len(model.roundtable.rounds)
    for round_index, round_data in enumerate(model.roundtable.rounds, start=1):
        path = f"roundtable.rounds[{round_index - 1}]"
        
        # 张力轴检查
        tension_axis = str(round_data.get("tension_axis") or "").strip()
        if not tension_axis:
            errors.append(QualityIssue("error", "missing_tension_axis", "每轮必须有张力轴", f"{path}.tension_axis"))
        elif _is_placeholder_tension(tension_axis):
            errors.append(QualityIssue("warning", "placeholder_tension_axis", "张力轴为占位符，未真正定义", f"{path}.tension_axis"))
        
        # 发言检查
        speeches = list(round_data.get("speeches") or [])
        for speech_index, speech in enumerate(speeches):
            speech_path = f"{path}.speeches[{speech_index}]"
            if not str(speech.get("action_type") or "").strip():
                errors.append(QualityIssue("error", "missing_action_type", "发言缺少行动类型", f"{speech_path}.action_type"))
            if speech_index > 0 and not speech.get("responds_to"):
                errors.append(QualityIssue("error", "missing_response_link", "非首条发言必须回应上一发言", f"{speech_path}.responds_to"))
        
        # 主持人检查
        moderator = round_data.get("moderator") or {}
        if not str(moderator.get("core_crack") or "").strip():
            errors.append(QualityIssue("error", "missing_moderator_crack", "主持人缺少裂缝提炼", f"{path}.moderator.core_crack"))
        
        # next_question 检查：最后一轮可以为空
        is_last_round = (round_index == total_rounds)
        next_question = str(moderator.get("next_question") or "").strip()
        if not next_question and not is_last_round:
            errors.append(QualityIssue("error", "missing_next_question", "主持人缺少下一问", f"{path}.moderator.next_question"))

    return {
        "ok": not any(issue.level == "error" for issue in errors),
        "errors": [issue.to_dict() for issue in errors],
    }

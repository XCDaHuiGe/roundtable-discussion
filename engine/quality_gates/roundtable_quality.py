# -*- coding: utf-8 -*-
from __future__ import annotations

from engine.cognitive_model.schema import CognitiveModel, QualityIssue


def validate_roundtable_quality(model: CognitiveModel) -> dict[str, object]:
    errors: list[QualityIssue] = []
    if not model.roundtable.participants:
        errors.append(QualityIssue("error", "missing_participants", "缺少专家参与者", "roundtable.participants"))

    for round_index, round_data in enumerate(model.roundtable.rounds, start=1):
        path = f"roundtable.rounds[{round_index - 1}]"
        if not str(round_data.get("tension_axis") or "").strip():
            errors.append(QualityIssue("error", "missing_tension_axis", "每轮必须有张力轴", f"{path}.tension_axis"))
        speeches = list(round_data.get("speeches") or [])
        for speech_index, speech in enumerate(speeches):
            speech_path = f"{path}.speeches[{speech_index}]"
            if not str(speech.get("action_type") or "").strip():
                errors.append(QualityIssue("error", "missing_action_type", "发言缺少行动类型", f"{speech_path}.action_type"))
            if speech_index > 0 and not speech.get("responds_to"):
                errors.append(QualityIssue("error", "missing_response_link", "非首条发言必须回应上一发言", f"{speech_path}.responds_to"))
        moderator = round_data.get("moderator") or {}
        if not str(moderator.get("core_crack") or "").strip():
            errors.append(QualityIssue("error", "missing_moderator_crack", "主持人缺少裂缝提炼", f"{path}.moderator.core_crack"))
        if not str(moderator.get("next_question") or "").strip():
            errors.append(QualityIssue("error", "missing_next_question", "主持人缺少下一问", f"{path}.moderator.next_question"))

    return {
        "ok": not errors,
        "errors": [issue.to_dict() for issue in errors],
    }

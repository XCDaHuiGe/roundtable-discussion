from engine.cognitive_model.schema import CognitiveModel, QualityIssue


def test_cognitive_model_defaults_to_v1_and_serializes_to_dict():
    model = CognitiveModel(title="测试书", source_type="book")

    data = model.to_dict()

    assert data["meta"]["title"] == "测试书"
    assert data["meta"]["source_type"] == "book"
    assert data["meta"]["version"] == "CognitiveModel.v1"
    assert data["book_spine"]["core_question"] == ""
    assert data["roundtable"]["rounds"] == []


def test_quality_issue_serializes_level_code_message_and_path():
    issue = QualityIssue(level="warning", code="missing_delta", message="缺少作者位移", path="book_spine.delta_sentence")

    assert issue.to_dict() == {
        "level": "warning",
        "code": "missing_delta",
        "message": "缺少作者位移",
        "path": "book_spine.delta_sentence",
    }


def test_cognitive_model_can_store_quality_issues():
    model = CognitiveModel(title="测试书", source_type="book")
    model.quality.checks.append(QualityIssue("warning", "partial_model", "旧数据只能形成部分模型", "meta"))

    assert model.to_dict()["quality"]["checks"][0]["code"] == "partial_model"

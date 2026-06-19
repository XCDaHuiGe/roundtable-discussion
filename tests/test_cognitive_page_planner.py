from engine.cognitive_model.schema import CognitiveModel
from engine.html_ppt_v13 import READING_LAYOUTS
from engine.html_ppt.cognitive_page_planner import plan_cognitive_pages


def sample_model():
    model = CognitiveModel(title="测试书")
    model.book_spine.core_question = "人为什么误把适应当命运？"
    model.book_spine.consensus_baseline = "旧共识把命运归因于意志。"
    model.book_spine.author_move = "作者把问题转向脑的适应机制。"
    model.book_spine.delta_sentence = "之前大家以为命运来自意志强弱，作者说命运来自脑的适应回路。"
    model.book_spine.signature_terms = ["适应回路", "神经可塑性"]
    model.book_spine.landing_sentence = "适应不是宿命，而是可训练的回路。"
    model.book_spine.carryaway = "面对类似问题时，先找问题轴、位移和根生成器。"
    
    model.source_understanding.material_map = [
        {"type": "核心章节", "content": "第三章：适应的神经机制"},
        {"type": "关键案例", "content": "伦敦出租车司机海马体研究"},
    ]
    model.source_understanding.author_problem = "作者试图回答：为什么我们误把适应当命运？"
    model.source_understanding.key_terms = ["适应回路", "神经可塑性", "习惯形成"]
    
    model.root_rank.root_generators = ["适应回路"]
    model.root_rank.candidate_generators = ["奖励回路", "注意力筛选"]
    model.root_rank.regeneration_matrix = [
        {"generator": "适应回路", "phenomenon": "习惯形成"},
        {"generator": "适应回路", "phenomenon": "情绪反应"},
        {"generator": "适应回路", "phenomenon": "学习迁移"},
    ]
    
    model.roundtable.participants = [
        {"name": "神经科学家", "role": "机制解释者", "function": "提供神经科学视角"},
        {"name": "哲学家", "role": "概念澄清者", "function": "提供哲学反思视角"},
        {"name": "心理学家", "role": "行为观察者", "function": "提供行为实验视角"},
    ]
    
    model.roundtable.rounds = [
        {
            "round_index": 1,
            "guiding_question": "适应是否能改变？",
            "tension_axis": "神经机制 / 行动选择",
            "speeches": [
                {"id": "r1s1", "expert": "神经科学家", "claim": "脑会重塑。", "action_type": "definition"},
                {"id": "r1s2", "expert": "哲学家", "claim": "选择需要意识。", "responds_to": "r1s1", "action_type": "response"},
            ],
            "moderator": {"core_crack": "机制解释不能替代行动选择。", "next_question": "训练从哪里开始？"},
            "cognitive_upgrade": {
                "old_thinking": "适应等于被动接受环境。",
                "new_thinking": "适应是可以训练的行动回路。",
                "complexity": "机制解释必须与行动选择同时成立。",
                "actionable_insight": "先识别环境触发器，再设计新的反馈回路。",
            },
            "clashes": [
                {"attacker": "哲学家", "attack_content": "神经机制不能解释自由意志。", "target": "神经科学家", "defense_content": "自由意志是涌现现象。"}
            ],
        }
    ]
    
    model.distillation.qa_chain = [
        {"question": "问题是什么？", "answer": {"conclusion": "适应被误读。", "boundary": "不解释全部人生。"}}
    ]
    model.distillation.insights = [{"title": "适应不是宿命", "content": "它是可被重新训练的回路。"}]
    model.distillation.future_bets = ["未来十年，神经反馈训练将成为主流。", "适应回路理论将改变教育模式。"]
    
    return model


def test_plan_cognitive_pages_includes_new_page_family():
    pages = plan_cognitive_pages(sample_model())
    types = [page.page_type for page in pages]

    assert types[0] == "cover"
    assert "core_question" in types
    assert "baseline_delta" in types
    assert "rank_map" in types
    assert "response_graph" in types
    assert "qa" in types
    assert types[-1] == "ending"


def test_planned_pages_use_v13_reading_page_contracts():
    pages = plan_cognitive_pages(sample_model())

    assert all(page.title for page in pages)
    assert all(page.takeaway for page in pages)
    assert all(page.layout in READING_LAYOUTS for page in pages)
    assert len({page.layout for page in pages}) >= 5


def test_new_page_types_included():
    """测试新增的 9 种页面类型是否正确生成"""
    model = sample_model()
    pages = plan_cognitive_pages(model)
    types = [page.page_type for page in pages]
    
    # 测试新增页面类型
    assert "source_map" in types, "source_map 页面应该被生成"
    assert "concept_anchor" in types, "concept_anchor 页面应该被生成"
    assert "experts" in types, "experts 页面应该被生成"
    assert "definition" in types, "definition 页面应该被生成"
    assert "round_opening" in types, "round_opening 页面应该被生成"
    assert "clash" in types, "clash 页面应该被生成"
    assert "cognitive_upgrade" in types, "cognitive_upgrade 页面应该被生成"
    assert "future_bets" in types, "future_bets 页面应该被生成"
    assert "library_lens" in types, "library_lens 页面应该被生成"


def test_page_order_correct():
    """测试页面顺序是否正确"""
    model = sample_model()
    pages = plan_cognitive_pages(model)
    types = [page.page_type for page in pages]
    
    # 验证基本顺序
    assert types[0] == "cover", "第一页应该是 cover"
    assert types[-1] == "ending", "最后一页应该是 ending"
    
    # 验证新页面类型的相对顺序
    type_to_index = {t: i for i, t in enumerate(types)}
    
    # source_map 应该在 core_question 之前
    if "source_map" in type_to_index and "core_question" in type_to_index:
        assert type_to_index["source_map"] < type_to_index["core_question"]
    
    # concept_anchor 应该在 baseline_delta 之后
    if "concept_anchor" in type_to_index and "baseline_delta" in type_to_index:
        assert type_to_index["baseline_delta"] < type_to_index["concept_anchor"]
    
    # definition 应该在 concept_anchor 之后
    if "definition" in type_to_index and "concept_anchor" in type_to_index:
        assert type_to_index["concept_anchor"] < type_to_index["definition"]
    
    # experts 应该在正式问题拆解之前，先交代解释框架
    if "experts" in type_to_index and "core_question" in type_to_index:
        assert type_to_index["experts"] < type_to_index["core_question"]
    
    # library_lens 应该在 experts 之后
    if "library_lens" in type_to_index and "experts" in type_to_index:
        assert type_to_index["experts"] < type_to_index["library_lens"]
    
    # open_questions / tension_map 应该在 insight 之后，形成结尾追问
    if "open_questions" in type_to_index and "insight" in type_to_index:
        assert type_to_index["insight"] < type_to_index["open_questions"]
    if "tension_map" in type_to_index and "insight" in type_to_index:
        assert type_to_index["insight"] < type_to_index["tension_map"]


def test_missing_fields_no_page():
    """测试缺失字段时不生成对应页面"""
    # 创建一个空模型
    model = CognitiveModel(title="空模型")
    pages = plan_cognitive_pages(model)
    types = [page.page_type for page in pages]
    
    # 只有 cover 和 ending 应该存在
    assert "cover" in types
    assert "ending" in types
    
    # 以下页面不应该存在（因为数据缺失）
    assert "source_map" not in types, "没有 material_map 和 author_problem 时不应该生成 source_map"
    assert "concept_anchor" not in types, "没有 key_terms 和 signature_terms 时不应该生成 concept_anchor"
    assert "experts" not in types, "没有 participants 时不应该生成 experts"
    assert "definition" not in types, "没有 signature_terms 时不应该生成 definition"
    assert "rank_map" not in types, "没有 root_generators 和 candidate_generators 时不应该生成 rank_map"
    assert "round_opening" not in types, "没有 rounds 时不应该生成 round_opening"
    assert "clash" not in types, "没有 clashes 时不应该生成 clash"
    assert "cognitive_upgrade" not in types, "没有 cognitive_upgrade 时不应该生成 cognitive_upgrade"
    assert "future_bets" not in types, "没有 future_bets 时不应该生成 future_bets"
    assert "library_lens" not in types, "没有核心字段时不应该生成 library_lens"


def test_empty_blocks_no_page():
    """测试空 blocks 时不生成页面"""
    model = CognitiveModel(title="空数据模型")
    
    # 设置空数据
    model.source_understanding.material_map = []
    model.source_understanding.key_terms = []
    model.book_spine.signature_terms = []
    model.roundtable.participants = []
    model.distillation.future_bets = []
    
    pages = plan_cognitive_pages(model)
    types = [page.page_type for page in pages]
    
    # 以下页面不应该存在（因为 blocks 为空）
    assert "source_map" not in types
    assert "concept_anchor" not in types
    assert "experts" not in types
    assert "definition" not in types
    assert "future_bets" not in types


def test_round_pages_with_clashes():
    """测试 round 页面与 clashes 的正确生成"""
    model = sample_model()
    pages = plan_cognitive_pages(model)
    
    # 找到 round 页面
    round_pages = [p for p in pages if p.page_type == "round_opening"]
    clash_pages = [p for p in pages if p.page_type == "clash"]
    
    assert len(round_pages) == 1, "应该生成 1 个 round_opening 页面"
    assert len(clash_pages) == 1, "应该生成 1 个 clash 页面"
    
    # 验证 round 页面内容
    round_page = round_pages[0]
    assert "本轮追问" in [b.title for b in round_page.blocks]
    assert "张力轴" in [b.title for b in round_page.blocks]
    
    # 验证 clash 页面内容
    clash_page = clash_pages[0]
    assert len(clash_page.blocks) > 0, "clash 页面应该有 blocks"


def test_cognitive_upgrade_page():
    """测试 cognitive_upgrade 页面的正确生成"""
    model = sample_model()
    pages = plan_cognitive_pages(model)
    
    moderator_pages = [p for p in pages if p.page_type == "cognitive_upgrade"]
    assert len(moderator_pages) == 1, "应该生成 1 个 cognitive_upgrade 页面"
    
    moderator_page = moderator_pages[0]
    assert "复杂性" in [b.title for b in moderator_page.blocks]


def test_source_map_with_material_map():
    """测试 source_map 页面使用 material_map 数据"""
    model = CognitiveModel(title="测试书")
    model.source_understanding.material_map = [
        {"type": "核心章节", "content": "第三章：适应的神经机制"},
        {"type": "关键案例", "content": "伦敦出租车司机研究"},
    ]
    
    pages = plan_cognitive_pages(model)
    source_map_pages = [p for p in pages if p.page_type == "source_map"]
    
    assert len(source_map_pages) == 1
    assert len(source_map_pages[0].blocks) == 2


def test_source_map_with_author_problem():
    """测试 source_map 页面使用 author_problem 数据"""
    model = CognitiveModel(title="测试书")
    model.source_understanding.author_problem = "作者试图回答：为什么我们误把适应当命运？"
    
    pages = plan_cognitive_pages(model)
    source_map_pages = [p for p in pages if p.page_type == "source_map"]
    
    assert len(source_map_pages) == 1
    assert len(source_map_pages[0].blocks) == 1


def test_definition_page():
    """测试 definition 页面的正确生成"""
    model = sample_model()
    pages = plan_cognitive_pages(model)
    
    definition_pages = [p for p in pages if p.page_type == "definition"]
    assert len(definition_pages) == 1, "应该生成 1 个 definition 页面"
    
    definition_page = definition_pages[0]
    assert "核心概念" in [b.title for b in definition_page.blocks]
    assert "概念定义" in [b.title for b in definition_page.blocks]
    assert "概念边界" in [b.title for b in definition_page.blocks]


def test_library_lens_page():
    """测试 library_lens 页面的正确生成"""
    model = sample_model()
    pages = plan_cognitive_pages(model)
    
    library_lens_pages = [p for p in pages if p.page_type == "library_lens"]
    assert len(library_lens_pages) == 1, "应该生成 1 个 library_lens 页面"
    
    library_lens_page = library_lens_pages[0]
    assert "问题轴" in [b.title for b in library_lens_page.blocks]
    assert "落点句" in [b.title for b in library_lens_page.blocks]
    assert "行囊" in [b.title for b in library_lens_page.blocks]

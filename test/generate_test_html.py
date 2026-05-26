#!/usr/bin/env python3
"""
测试生成器 V2 - 为每个模板生成高质量测试 HTML
采用高端科技杂志风格
"""

import json
from pathlib import Path

ENGINE_DIR = Path(__file__).parent.parent / "engine"
TEST_DIR = Path(__file__).parent
TEMPLATES_CONFIG = ENGINE_DIR / "templates.json"

MOCK_DATA = {
    "title": "AI与人类认知边界",
    "subtitle": "当算法超越直觉，我们如何定义智慧？",
    "experts": [
        {"name": "孔子", "role": "哲学家", "initial": "孔"},
        {"name": "塔勒布", "role": "风险分析师", "initial": "塔"},
        {"name": "凯文·凯利", "role": "科技预言家", "initial": "凯"},
        {"name": "芒格", "role": "投资智者", "initial": "芒"},
        {"name": "韩炳哲", "role": "文化批评家", "initial": "韩"},
        {"name": "项飙", "role": "社会学家", "initial": "项"}
    ],
    "rounds": [
        {
            "question": "AI能否真正理解人类的情感？",
            "stances": [
                {"speaker": "孔子", "role": "哲学家", "content": "情感是仁的核心。AI可以模拟情感表达，但无法理解情感的道德维度——那种对他人的真诚关怀。"},
                {"speaker": "塔勒布", "role": "风险分析师", "content": "理解情感需要经历极端事件。AI没有经历过黑天鹅，它的\"理解\"只是统计模式匹配。"},
                {"speaker": "凯文·凯利", "role": "科技预言家", "content": "AI的理解是另一种理解。它不需要经历，只需要足够的数据。人类的理解方式不是唯一的方式。"}
            ],
            "clashes": [
                {"speaker": "塔勒布", "content": "凯利，你说的\"另一种理解\"是危险的。没有经历的理解是脆弱的，会在极端情况下崩溃。"},
                {"speaker": "孔子", "content": "如果AI的情感理解只是模式匹配，那它如何处理道德困境？比如自动驾驶的伦理选择？"}
            ],
            "insight": {"core": "AI的情感理解是\"功能性理解\"，而非\"存在性理解\"", "explain": "AI可以识别和响应情感信号，但缺乏情感体验的道德维度。这种差异在极端情况下会暴露出来。"}
        },
        {
            "question": "算法决策会削弱人类的自主性吗？",
            "stances": [
                {"speaker": "芒格", "role": "投资智者", "content": "算法决策是认知外包。它节省了时间，但也剥夺了我们犯错和学习的机会。"},
                {"speaker": "韩炳哲", "role": "文化批评家", "content": "算法决策创造了新的\"透明监狱\"。我们看似自由选择，实则被算法的推荐系统操控。"},
                {"speaker": "项飙", "role": "社会学家", "content": "关键是谁控制算法。如果算法是公共工具，它可以增强自主性；如果是商业工具，它会削弱自主性。"}
            ],
            "clashes": [
                {"speaker": "芒格", "content": "项飙，你的\"公共工具\"理想很美好，但现实中算法都是商业公司的。这种区分有意义吗？"},
                {"speaker": "韩炳哲", "content": "芒格说的\"认知外包\"是倦怠社会的核心症状。我们因为疲惫而把决策交给算法，然后变得更疲惫。"}
            ],
            "insight": {"core": "算法决策的威胁不是技术本身，而是权力结构", "explain": "当算法由少数人控制并服务于商业利益时，它会削弱大多数人的自主性。解决方案不是拒绝算法，而是 democratize 算法。"}
        },
        {
            "question": "人类与AI协作的未来是什么？",
            "stances": [
                {"speaker": "凯文·凯利", "role": "科技预言家", "content": "未来是\"人机共生\"。AI处理信息，人类处理意义。这不是竞争，是分工。"},
                {"speaker": "孔子", "role": "哲学家", "content": "共生需要\"和而不同\"。AI必须保持工具属性，人类必须保持主体地位。"},
                {"speaker": "塔勒布", "role": "风险分析师", "content": "共生是脆弱的。过度依赖AI会让系统在黑天鹅事件中崩溃。我们需要冗余和备份。"}
            ],
            "clashes": [
                {"speaker": "塔勒布", "content": "凯利，你的\"分工\"假设太乐观了。当AI的能力边界不断扩展，人类的\"意义处理\"领域会越来越小。"},
                {"speaker": "孔子", "content": "塔勒布的担忧有道理，但凯利的愿景也有价值。关键是建立\"边界协议\"——明确哪些领域必须由人类主导。"}
            ],
            "insight": {"core": "人机协作的核心是\"边界意识\"", "explain": "我们需要明确AI的能力边界和人类的主体边界。没有边界意识的协作，最终会变成人类的自我消解。"}
        }
    ],
    "conclusions": [
        "AI的情感理解是功能性的，而非存在性的",
        "算法决策的威胁来自权力结构，而非技术本身",
        "人机协作需要明确的边界协议",
        "保持人类的主体性是技术发展的底线"
    ],
    "openQuestions": [
        "如果AI的情感理解只是模式匹配，那它能否发展出真正的道德判断？",
        "算法决策的\"透明监狱\"如何被打破？",
        "人机协作的边界协议应该由谁来制定？",
        "在AI时代，\"智慧\"的定义是否需要重新审视？"
    ],
    "closingTitle": "AI不是人类的替代，而是人类的延伸",
    "closingNote": "关键在于我们如何定义边界。这场圆桌洞见揭示了AI与人类认知的核心张力。答案不在技术本身，而在我们如何与技术相处。",
    "stats": {"experts": 6, "rounds": 3, "clashes": 6, "insights": 3}
}

AVATAR_CLASSES = ["", "alt", "alt2", "alt3", "alt4", "alt5"]

def generate_slides_html() -> str:
    """生成高质量 slides 内容"""
    slides = []
    
    # Hero Section
    slides.append(f'''
<section class="section hero visible">
  <div class="container">
    <div class="hero-badge animate">圆桌洞见 V5.0</div>
    <h1 class="hero-title animate delay-1">{MOCK_DATA["title"]}</h1>
    <p class="hero-sub animate delay-2">{MOCK_DATA["subtitle"]}</p>
    <div class="hero-stats animate delay-3">
      <div class="stat"><div class="stat-num">{MOCK_DATA["stats"]["experts"]}</div><div class="stat-label">专家</div></div>
      <div class="stat"><div class="stat-num">{MOCK_DATA["stats"]["rounds"]}</div><div class="stat-label">轮次</div></div>
      <div class="stat"><div class="stat-num">{MOCK_DATA["stats"]["clashes"]}+</div><div class="stat-label">碰撞</div></div>
      <div class="stat"><div class="stat-num">{MOCK_DATA["stats"]["insights"]}</div><div class="stat-label">洞见</div></div>
    </div>
  </div>
</section>
''')
    
    # Experts Section
    expert_cards = ""
    for i, e in enumerate(MOCK_DATA["experts"]):
        avatar_class = AVATAR_CLASSES[i % len(AVATAR_CLASSES)]
        expert_cards += f'''
    <div class="expert-card">
      <div class="expert-avatar {avatar_class}">{e["initial"]}</div>
      <div class="expert-name">{e["name"]}</div>
      <div class="expert-role">{e["role"]}</div>
    </div>'''
    
    slides.append(f'''
<section class="section experts-section">
  <div class="container">
    <div class="experts-grid">{expert_cards}
    </div>
  </div>
</section>
''')
    
    # Rounds
    for i, round_data in enumerate(MOCK_DATA["rounds"]):
        round_num = i + 1
        
        # Round Header
        slides.append(f'''
<section class="section round-section">
  <div class="container">
    <div class="round-header">
      <span class="round-tag">Round {round_num}</span>
      <span class="round-num">/ {MOCK_DATA["stats"]["rounds"]}</span>
    </div>
    <h2 class="round-title">{round_data["question"]}</h2>
''')
        
        # Speeches
        for j, s in enumerate(round_data["stances"]):
            avatar_class = AVATAR_CLASSES[j % len(AVATAR_CLASSES)]
            slides.append(f'''
    <div class="speech-block">
      <div class="speech-header">
        <div class="speech-avatar {avatar_class}">{s["speaker"][0]}</div>
        <div><div class="speech-name">{s["speaker"]}</div><div class="speech-role">{s["role"]}</div></div>
      </div>
      <div class="speech-content">{s["content"]}</div>
    </div>
''')
        
        # Clashes
        if round_data["clashes"]:
            slides.append(f'''
    <div class="clash-block">
      <div class="clash-label">碰撞交锋</div>
''')
            for c in round_data["clashes"]:
                slides.append(f'''
      <div class="clash-item">
        <div class="clash-speaker">{c["speaker"]}</div>
        <div class="clash-text">{c["content"]}</div>
      </div>
''')
            slides.append('''    </div>\n''')
        
        # Insight
        slides.append(f'''
    <div class="insight-block">
      <div class="insight-label">核心洞见</div>
      <div class="insight-core">{round_data["insight"]["core"]}</div>
      <div class="insight-explain">{round_data["insight"]["explain"]}</div>
    </div>
  </div>
</section>
''')
    
    # Conclusions
    conclusion_cards = ""
    for i, c in enumerate(MOCK_DATA["conclusions"]):
        conclusion_cards += f'''
    <div class="conclusion-card">
      <div class="conclusion-num">{i+1}</div>
      <div class="conclusion-text">{c}</div>
    </div>'''
    
    slides.append(f'''
<section class="section">
  <div class="container">
    <div class="round-header">
      <span class="round-tag">结论</span>
    </div>
    <div class="conclusions-grid">{conclusion_cards}
    </div>
  </div>
</section>
''')
    
    # Open Questions
    question_cards = ""
    for i, q in enumerate(MOCK_DATA["openQuestions"]):
        question_cards += f'''
    <div class="question-card">
      <span class="question-num">Q{i+1}</span>
      <span class="question-text">{q}</span>
    </div>'''
    
    slides.append(f'''
<section class="section questions-section">
  <div class="container">
    <div class="round-header">
      <span class="round-tag">开放问题</span>
    </div>
    {question_cards}
  </div>
</section>
''')
    
    # Closing
    slides.append(f'''
<section class="section closing">
  <div class="container">
    <h2 class="closing-title">{MOCK_DATA["closingTitle"]}</h2>
    <p class="closing-note">{MOCK_DATA["closingNote"]}</p>
  </div>
</section>
''')
    
    return "\n".join(slides)

def generate_test_html(template_file: Path) -> str:
    """为模板生成测试 HTML"""
    template_content = template_file.read_text(encoding="utf-8")
    slides_html = generate_slides_html()
    
    html = template_content.replace("{{slides}}", slides_html)
    html = html.replace("{{title}}", MOCK_DATA["title"])
    html = html.replace("{{subtitle}}", MOCK_DATA["subtitle"])
    
    return html

def main():
    """生成所有测试 HTML"""
    TEST_DIR.mkdir(exist_ok=True)
    
    # 使用新的 premium-dark 模板
    premium_template = ENGINE_DIR / "template-premium-dark.html"
    
    if premium_template.exists():
        output_file = TEST_DIR / "test_premium-dark.html"
        html = generate_test_html(premium_template)
        output_file.write_text(html, encoding="utf-8")
        print(f"✅ premium-dark → {output_file.name}")
    
    # 更新 templates.json
    with open(TEMPLATES_CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # 添加新模板到配置
    new_template = {
        "id": "premium-dark",
        "name": "高端科技杂志风格",
        "file": "template-premium-dark.html",
        "description": "Apple官网风格，极简主义，深色模式，高级感",
        "origin": "optimized",
        "theme": {"bg": "#0d0d0d", "accent": "#ff6b35", "insight": "#00d4aa"}
    }
    
    if not any(t["id"] == "premium-dark" for t in config["templates"]):
        config["templates"].append(new_template)
        with open(TEMPLATES_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print("✅ 已添加 premium-dark 到 templates.json")
    
    # 保存模拟数据
    mock_json = TEST_DIR / "mock_data.json"
    with open(mock_json, "w", encoding="utf-8") as f:
        json.dump(MOCK_DATA, f, ensure_ascii=False, indent=2)
    print(f"📄 模拟数据: {mock_json.name}")
    
    print(f"\n📊 测试文件已生成到: {TEST_DIR}")

if __name__ == "__main__":
    main()
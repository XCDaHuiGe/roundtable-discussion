#!/usr/bin/env python3
"""
测试生成器 - 为每个模板生成测试 HTML
"""

import json
import random
from pathlib import Path

ENGINE_DIR = Path(__file__).parent.parent / "engine"
TEST_DIR = Path(__file__).parent
TEMPLATES_CONFIG = ENGINE_DIR / "templates.json"

MOCK_DATA = {
    "title": "AI与人类认知边界",
    "subtitle": "当算法超越直觉，我们如何定义智慧？",
    "experts": [
        {"name": "孔子", "role": "哲学家", "description": "儒家思想创始人，强调仁义礼智信"},
        {"name": "塔勒布", "role": "风险分析师", "description": "黑天鹅理论提出者，关注不确定性"},
        {"name": "凯文·凯利", "role": "科技预言家", "description": "《必然》作者，洞察技术趋势"},
        {"name": "芒格", "role": "投资智者", "description": "伯克希尔副董事长，多元思维模型"},
        {"name": "韩炳哲", "role": "文化批评家", "description": "《倦怠社会》作者，批判数字资本主义"},
        {"name": "项飙", "role": "社会学家", "description": "牛津大学教授，关注附近与悬浮"}
    ],
    "rounds": [
        {
            "question": "AI能否真正理解人类的情感？",
            "stances": [
                {"speaker": "孔子", "name": "孔子", "role": "哲学家", "stance": "情感是仁的核心。AI可以模拟情感表达，但无法理解情感的道德维度——那种对他人的真诚关怀。", "content": "情感是仁的核心。AI可以模拟情感表达，但无法理解情感的道德维度——那种对他人的真诚关怀。"},
                {"speaker": "塔勒布", "name": "塔勒布", "role": "风险分析师", "stance": "理解情感需要经历极端事件。AI没有经历过黑天鹅，它的\"理解\"只是统计模式匹配。", "content": "理解情感需要经历极端事件。AI没有经历过黑天鹅，它的\"理解\"只是统计模式匹配。"},
                {"speaker": "凯文·凯利", "name": "凯文·凯利", "role": "科技预言家", "stance": "AI的理解是另一种理解。它不需要经历，只需要足够的数据。人类的理解方式不是唯一的方式。", "content": "AI的理解是另一种理解。它不需要经历，只需要足够的数据。人类的理解方式不是唯一的方式。"}
            ],
            "clashes": [
                {"speaker": "塔勒布", "type": "反驳", "content": "凯利，你说的\"另一种理解\"是危险的。没有经历的理解是脆弱的，会在极端情况下崩溃。"},
                {"speaker": "孔子", "type": "追问", "content": "如果AI的情感理解只是模式匹配，那它如何处理道德困境？比如自动驾驶的伦理选择？"}
            ],
            "insight": {
                "core": "AI的情感理解是\"功能性理解\"，而非\"存在性理解\"",
                "explain": "AI可以识别和响应情感信号，但缺乏情感体验的道德维度。这种差异在极端情况下会暴露出来。"
            }
        },
        {
            "question": "算法决策会削弱人类的自主性吗？",
            "stances": [
                {"speaker": "芒格", "name": "芒格", "role": "投资智者", "stance": "算法决策是认知外包。它节省了时间，但也剥夺了我们犯错和学习的机会。", "content": "算法决策是认知外包。它节省了时间，但也剥夺了我们犯错和学习的机会。"},
                {"speaker": "韩炳哲", "name": "韩炳哲", "role": "文化批评家", "stance": "算法决策创造了新的\"透明监狱\"。我们看似自由选择，实则被算法的推荐系统操控。", "content": "算法决策创造了新的\"透明监狱\"。我们看似自由选择，实则被算法的推荐系统操控。"},
                {"speaker": "项飙", "name": "项飙", "role": "社会学家", "stance": "关键是谁控制算法。如果算法是公共工具，它可以增强自主性；如果是商业工具，它会削弱自主性。", "content": "关键是谁控制算法。如果算法是公共工具，它可以增强自主性；如果是商业工具，它会削弱自主性。"}
            ],
            "clashes": [
                {"speaker": "芒格", "type": "质疑", "content": "项飙，你的\"公共工具\"理想很美好，但现实中算法都是商业公司的。这种区分有意义吗？"},
                {"speaker": "韩炳哲", "type": "延伸", "content": "芒格说的\"认知外包\"是倦怠社会的核心症状。我们因为疲惫而把决策交给算法，然后变得更疲惫。"}
            ],
            "insight": {
                "core": "算法决策的威胁不是技术本身，而是权力结构",
                "explain": "当算法由少数人控制并服务于商业利益时，它会削弱大多数人的自主性。解决方案不是拒绝算法，而是 democratize 算法。"
            }
        },
        {
            "question": "人类与AI协作的未来是什么？",
            "stances": [
                {"speaker": "凯文·凯利", "name": "凯文·凯利", "role": "科技预言家", "stance": "未来是\"人机共生\"。AI处理信息，人类处理意义。这不是竞争，是分工。", "content": "未来是\"人机共生\"。AI处理信息，人类处理意义。这不是竞争，是分工。"},
                {"speaker": "孔子", "name": "孔子", "role": "哲学家", "stance": "共生需要\"和而不同\"。AI必须保持工具属性，人类必须保持主体地位。", "content": "共生需要\"和而不同\"。AI必须保持工具属性，人类必须保持主体地位。"},
                {"speaker": "塔勒布", "name": "塔勒布", "role": "风险分析师", "stance": "共生是脆弱的。过度依赖AI会让系统在黑天鹅事件中崩溃。我们需要冗余和备份。", "content": "共生是脆弱的。过度依赖AI会让系统在黑天鹅事件中崩溃。我们需要冗余和备份。"}
            ],
            "clashes": [
                {"speaker": "塔勒布", "type": "警告", "content": "凯利，你的\"分工\"假设太乐观了。当AI的能力边界不断扩展，人类的\"意义处理\"领域会越来越小。"},
                {"speaker": "孔子", "type": "调和", "content": "塔勒布的担忧有道理，但凯利的愿景也有价值。关键是建立\"边界协议\"——明确哪些领域必须由人类主导。"}
            ],
            "insight": {
                "core": "人机协作的核心是\"边界意识\"",
                "explain": "我们需要明确AI的能力边界和人类的主体边界。没有边界意识的协作，最终会变成人类的自我消解。"
            }
        }
    ],
    "conclusions": [
        {"content": "AI的情感理解是功能性的，而非存在性的"},
        {"content": "算法决策的威胁来自权力结构，而非技术本身"},
        {"content": "人机协作需要明确的边界协议"},
        {"content": "保持人类的主体性是技术发展的底线"}
    ],
    "openQuestions": [
        "如果AI的情感理解只是模式匹配，那它能否发展出真正的道德判断？",
        "算法决策的\"透明监狱\"如何被打破？",
        "人机协作的边界协议应该由谁来制定？",
        "在AI时代，\"智慧\"的定义是否需要重新审视？"
    ],
    "conclusion": "AI不是人类的替代，而是人类的延伸。关键在于我们如何定义边界。",
    "closingNote": "这场圆桌洞见揭示了AI与人类认知的核心张力。答案不在技术本身，而在我们如何与技术相处。",
    "expertCount": 6,
    "roundCount": 3,
    "clashCount": 6,
    "insightCount": 3
}

def generate_mock_html(template_id: str, template_file: Path) -> str:
    """为模板生成测试 HTML"""
    content = template_file.read_text(encoding="utf-8")
    
    # Handlebars 模板用简单替换
    if "{{#each" in content:
        # 简化处理：直接替换关键变量
        html = content.replace("{{title}}", MOCK_DATA["title"])
        html = html.replace("{{subtitle}}", MOCK_DATA["subtitle"])
        html = html.replace("{{expertCount}}", str(MOCK_DATA["expertCount"]))
        html = html.replace("{{roundCount}}", str(MOCK_DATA["roundCount"]))
        html = html.replace("{{clashCount}}", str(MOCK_DATA["clashCount"]))
        html = html.replace("{{insightCount}}", str(MOCK_DATA["insightCount"]))
        return html
    
    # Adapter 模板生成 slides
    slides_html = generate_slides_html(template_id)
    html = content.replace("{{slides}}", slides_html)
    html = html.replace("{{title}}", MOCK_DATA["title"])
    html = html.replace("{{subtitle}}", MOCK_DATA["subtitle"])
    
    return html

def generate_slides_html(template_id: str) -> str:
    """生成 slides 内容"""
    colors = ["#c23b22", "#4a6a9a", "#3a8a5c", "#d4a843", "#8a4aaa", "#e85d3a"]
    
    slides = []
    
    # 封面
    slides.append(f'''
<div class="slide slide-cover">
  <div class="cover-badge">圆桌洞见 V5.0</div>
  <h1 class="cover-title">{MOCK_DATA["title"]}</h1>
  <p class="cover-sub">{MOCK_DATA["subtitle"]}</p>
  <div class="cover-stats">
    <div class="cover-stat"><div class="cover-stat-num">{MOCK_DATA["expertCount"]}</div><div class="cover-stat-label">专家</div></div>
    <div class="cover-stat"><div class="cover-stat-num">{MOCK_DATA["roundCount"]}</div><div class="cover-stat-label">轮次</div></div>
    <div class="cover-stat"><div class="cover-stat-num">{MOCK_DATA["clashCount"]}+</div><div class="cover-stat-label">碰撞</div></div>
    <div class="cover-stat"><div class="cover-stat-num">{MOCK_DATA["insightCount"]}</div><div class="cover-stat-label">洞见</div></div>
  </div>
</div>
''')
    
    # 专家介绍
    expert_cards = ""
    for i, e in enumerate(MOCK_DATA["experts"][:6]):
        color = colors[i % len(colors)]
        expert_cards += f'''
    <div class="expert-card">
      <div class="expert-avatar" style="background:{color}">{e["name"][0]}</div>
      <div class="expert-name">{e["name"]}</div>
      <div class="expert-role">{e["role"]}</div>
      <div class="expert-desc">{e["description"][:30]}...</div>
    </div>'''
    
    slides.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">专家阵容</div>
  <h2 class="slide-title">{MOCK_DATA["title"]}</h2>
  <div class="experts-grid">{expert_cards}
  </div>
</div>
''')
    
    # 轮次
    for i, round_data in enumerate(MOCK_DATA["rounds"]):
        round_num = i + 1
        
        # 标题页
        slides.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">Round {round_num} / {MOCK_DATA["roundCount"]}</div>
  <h2 class="slide-title">{round_data["question"]}</h2>
</div>
''')
        
        # 发言页
        speech_cards = ""
        for j, s in enumerate(round_data["stances"][:3]):
            color = colors[j % len(colors)]
            speech_cards += f'''
    <div class="speech-card">
      <div class="speech-meta">
        <div class="speaker-avatar" style="background:{color}">{s["speaker"][0]}</div>
        <div><div class="speaker-name">{s["speaker"]}</div><div class="speaker-role">{s["role"]}</div></div>
      </div>
      <div class="speech-content">{s["content"]}</div>
    </div>'''
        
        slides.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">Round {round_num} 发言</div>
  <div class="speech-cards">{speech_cards}
  </div>
</div>
''')
        
        # 碰撞页
        clash_items = ""
        for c in round_data["clashes"]:
            clash_items += f'''
    <div class="clash-item">
      <div class="clash-speaker">{c["speaker"]}</div>
      <div class="clash-text">{c["content"]}</div>
    </div>'''
        
        slides.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">Round {round_num} 碰撞</div>
  <div class="clash-block">{clash_items}
  </div>
</div>
''')
        
        # 洞见页
        slides.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">Round {round_num} 洞见</div>
  <div class="insight-block">
    <div class="insight-q">{round_data["insight"]["core"]}</div>
    <div class="insight-a">{round_data["insight"]["explain"]}</div>
  </div>
</div>
''')
    
    # 结论页
    conclusion_items = ""
    for i, c in enumerate(MOCK_DATA["conclusions"]):
        conclusion_items += f'''
    <div class="conclusion-item">
      <div class="conclusion-num">{i+1}</div>
      <div class="conclusion-text">{c["content"]}</div>
    </div>'''
    
    slides.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">核心结论</div>
  <h2 class="slide-title">圆桌洞见总结</h2>
  <div class="conclusions-grid">{conclusion_items}
  </div>
</div>
''')
    
    # 开放问题页
    question_items = ""
    for i, q in enumerate(MOCK_DATA["openQuestions"]):
        question_items += f'''
    <div class="question-card">
      <span class="question-number">Q{i+1}</span>
      <span class="question-text">{q}</span>
    </div>'''
    
    slides.append(f'''
<div class="slide slide-white">
  <div class="breadcrumb">留给读者</div>
  <h2 class="slide-title">开放问题</h2>
  {question_items}
</div>
''')
    
    # 结语页
    slides.append(f'''
<div class="slide slide-cover">
  <h2 class="cover-title">{MOCK_DATA["conclusion"]}</h2>
  <p class="cover-sub">{MOCK_DATA["closingNote"]}</p>
</div>
''')
    
    return "\n".join(slides)

def main():
    """生成所有测试 HTML"""
    with open(TEMPLATES_CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    TEST_DIR.mkdir(exist_ok=True)
    
    print("\n🧪 测试 HTML 生成器\n")
    print("=" * 60)
    
    for t in config["templates"]:
        template_file = ENGINE_DIR / t["file"]
        output_file = TEST_DIR / f"test_{t['id']}.html"
        
        html = generate_mock_html(t["id"], template_file)
        output_file.write_text(html, encoding="utf-8")
        
        print(f"✅ {t['id']:<20} → {output_file.name}")
    
    print("\n" + "=" * 60)
    print(f"\n📊 生成了 {len(config['templates'])} 个测试文件")
    print(f"📁 目录: {TEST_DIR}")
    
    # 保存模拟数据
    mock_json = TEST_DIR / "mock_data.json"
    with open(mock_json, "w", encoding="utf-8") as f:
        json.dump(MOCK_DATA, f, ensure_ascii=False, indent=2)
    print(f"📄 模拟数据: {mock_json.name}")

if __name__ == "__main__":
    main()
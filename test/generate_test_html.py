#!/usr/bin/env python3
"""
测试生成器 V4 - 为每个模板生成精确匹配CSS类名的测试HTML
每个模板有独立的生成函数，确保类名与模板CSS完全对应
跳过 Handlebars 模板（v3-magazine, v2-starry），它们需要 render_v8.py 渲染
"""

import json
from pathlib import Path

ENGINE_DIR = Path(__file__).parent.parent / "engine"
TEST_DIR = Path(__file__).parent

MOCK_DATA = {
    "title": "AI与人类认知边界",
    "subtitle": "当算法超越直觉，我们如何定义智慧？",
    "expertCount": 6,
    "roundCount": 3,
    "clashCount": 6,
    "insightCount": 3,
    "experts": [
        {"name": "孔子", "role": "哲学家", "roleLabel": "哲学家", "initial": "孔", "color": "#ff6b35"},
        {"name": "塔勒布", "role": "风险分析师", "roleLabel": "风险分析师", "initial": "塔", "color": "#ff4757"},
        {"name": "凯文·凯利", "role": "科技预言家", "roleLabel": "科技预言家", "initial": "凯", "color": "#00d4aa"},
        {"name": "芒格", "role": "投资智者", "roleLabel": "投资智者", "initial": "芒", "color": "#6366f1"},
        {"name": "韩炳哲", "role": "文化批评家", "roleLabel": "文化批评家", "initial": "韩", "color": "#f59e0b"},
        {"name": "项飙", "role": "社会学家", "roleLabel": "社会学家", "initial": "项", "color": "#ec4899"}
    ],
    "rounds": [
        {
            "question": "AI能否真正理解人类的情感？",
            "stances": [
                {"name": "孔子", "role": "leader", "roleLabel": "哲学家", "initial": "孔", "color": "#ff6b35", "content": "情感是仁的核心。AI可以模拟情感表达，但无法理解情感的道德维度——那种对他人的真诚关怀。"},
                {"name": "塔勒布", "role": "challenger", "roleLabel": "风险分析师", "initial": "塔", "color": "#ff4757", "content": "理解情感需要经历极端事件。AI没有经历过黑天鹅，它的\"理解\"只是统计模式匹配。"},
                {"name": "凯文·凯利", "role": "observer", "roleLabel": "科技预言家", "initial": "凯", "color": "#00d4aa", "content": "AI的理解是另一种理解。它不需要经历，只需要足够的数据。人类的理解方式不是唯一的方式。"}
            ],
            "clashes": [
                {"speaker": "塔勒布", "type": "反驳", "content": "凯利，你说的\"另一种理解\"是危险的。没有经历的理解是脆弱的，会在极端情况下崩溃。"},
                {"speaker": "孔子", "type": "追问", "content": "如果AI的情感理解只是模式匹配，那它如何处理道德困境？比如自动驾驶的伦理选择？"}
            ],
            "insight": {"core": "AI的情感理解是\"功能性理解\"，而非\"存在性理解\"", "explain": "AI可以识别和响应情感信号，但缺乏情感体验的道德维度。这种差异在极端情况下会暴露出来。"}
        },
        {
            "question": "算法决策会削弱人类的自主性吗？",
            "stances": [
                {"name": "芒格", "role": "leader", "roleLabel": "投资智者", "initial": "芒", "color": "#6366f1", "content": "算法决策是认知外包。它节省了时间，但也剥夺了我们犯错和学习的机会。"},
                {"name": "韩炳哲", "role": "challenger", "roleLabel": "文化批评家", "initial": "韩", "color": "#f59e0b", "content": "算法决策创造了新的\"透明监狱\"。我们看似自由选择，实则被算法的推荐系统操控。"},
                {"name": "项飙", "role": "observer", "roleLabel": "社会学家", "initial": "项", "color": "#ec4899", "content": "关键是谁控制算法。如果算法是公共工具，它可以增强自主性；如果是商业工具，它会削弱自主性。"}
            ],
            "clashes": [
                {"speaker": "芒格", "type": "质疑", "content": "项飙，你的\"公共工具\"理想很美好，但现实中算法都是商业公司的。这种区分有意义吗？"},
                {"speaker": "韩炳哲", "type": "延伸", "content": "芒格说的\"认知外包\"是倦怠社会的核心症状。我们因为疲惫而把决策交给算法，然后变得更疲惫。"}
            ],
            "insight": {"core": "算法决策的威胁不是技术本身，而是权力结构", "explain": "当算法由少数人控制并服务于商业利益时，它会削弱大多数人的自主性。解决方案不是拒绝算法，而是 democratize 算法。"}
        },
        {
            "question": "人类与AI协作的未来是什么？",
            "stances": [
                {"name": "凯文·凯利", "role": "leader", "roleLabel": "科技预言家", "initial": "凯", "color": "#00d4aa", "content": "未来是\"人机共生\"。AI处理信息，人类处理意义。这不是竞争，是分工。"},
                {"name": "孔子", "role": "challenger", "roleLabel": "哲学家", "initial": "孔", "color": "#ff6b35", "content": "共生需要\"和而不同\"。AI必须保持工具属性，人类必须保持主体地位。"},
                {"name": "塔勒布", "role": "observer", "roleLabel": "风险分析师", "initial": "塔", "color": "#ff4757", "content": "共生是脆弱的。过度依赖AI会让系统在黑天鹅事件中崩溃。我们需要冗余和备份。"}
            ],
            "clashes": [
                {"speaker": "塔勒布", "type": "反驳", "content": "凯利，你的\"分工\"假设太乐观了。当AI的能力边界不断扩展，人类的\"意义处理\"领域会越来越小。"},
                {"speaker": "孔子", "type": "整合", "content": "塔勒布的担忧有道理，但凯利的愿景也有价值。关键是建立\"边界协议\"——明确哪些领域必须由人类主导。"}
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
    "conclusion": "AI不是人类的替代，而是人类的延伸",
    "closingNote": "关键在于我们如何定义边界。这场圆桌洞见揭示了AI与人类认知的核心张力。答案不在技术本身，而在我们如何与技术相处。"
}

SKIP_TEMPLATES = {"template-v3-magazine.html", "template-v2-starry.html"}


def _expert_cards_standard(experts):
    h = ""
    for e in experts:
        h += f'''<div class="expert-card"><div class="expert-avatar">{e["initial"]}</div><div class="expert-name">{e["name"]}</div><div class="expert-role">{e["role"]}</div></div>'''
    return h


def generate_slides_premium_dark():
    d = MOCK_DATA
    slides = []

    slides.append(f'''<section class="section hero visible">
  <div class="container">
    <div class="hero-badge animate">圆桌洞见 V5.0</div>
    <h1 class="hero-title animate delay-1">{d["title"]}</h1>
    <p class="hero-sub animate delay-2">{d["subtitle"]}</p>
    <div class="hero-stats animate delay-3">
      <div class="stat"><div class="stat-num">{d["expertCount"]}</div><div class="stat-label">专家</div></div>
      <div class="stat"><div class="stat-num">{d["roundCount"]}</div><div class="stat-label">轮次</div></div>
      <div class="stat"><div class="stat-num">{d["clashCount"]}+</div><div class="stat-label">碰撞</div></div>
      <div class="stat"><div class="stat-num">{d["insightCount"]}</div><div class="stat-label">洞见</div></div>
    </div>
  </div>
</section>''')

    slides.append(f'''<section class="section experts-section">
  <div class="container">
    <div class="experts-grid">{_expert_cards_standard(d["experts"])}</div>
  </div>
</section>''')

    for i, r in enumerate(d["rounds"]):
        speeches = ""
        for s in r["stances"]:
            speeches += f'''<div class="speech-block">
      <div class="speech-header"><div class="speech-avatar">{s["initial"]}</div><div><div class="speech-name">{s["name"]}</div><div class="speech-role">{s["roleLabel"]}</div></div></div>
      <div class="speech-content">{s["content"]}</div>
    </div>'''
        clash_items = ""
        for c in r["clashes"]:
            clash_items += f'''<div class="clash-item"><div class="clash-speaker">{c["speaker"]}</div><div class="clash-text">{c["content"]}</div></div>'''
        slides.append(f'''<section class="section round-section">
  <div class="container">
    <div class="round-header"><span class="round-tag">Round {i+1}</span><span class="round-num">/ {d["roundCount"]}</span></div>
    <h2 class="round-title">{r["question"]}</h2>
    {speeches}
    <div class="clash-block"><div class="clash-label">碰撞交锋</div>{clash_items}</div>
    <div class="insight-block"><div class="insight-label">核心洞见</div><div class="insight-core">{r["insight"]["core"]}</div><div class="insight-explain">{r["insight"]["explain"]}</div></div>
  </div>
</section>''')

    cc = ""
    for i, c in enumerate(d["conclusions"]):
        cc += f'''<div class="conclusion-card"><div class="conclusion-num">{i+1}</div><div class="conclusion-text">{c}</div></div>'''
    slides.append(f'''<section class="section"><div class="container"><div class="round-header"><span class="round-tag">结论</span></div><div class="conclusions-grid">{cc}</div></div></section>''')

    qc = ""
    for i, q in enumerate(d["openQuestions"]):
        qc += f'''<div class="question-card"><span class="question-num">Q{i+1}</span><span class="question-text">{q}</span></div>'''
    slides.append(f'''<section class="section questions-section"><div class="container"><div class="round-header"><span class="round-tag">开放问题</span></div>{qc}</div></section>''')

    slides.append(f'''<section class="section closing"><div class="container"><h2 class="closing-title">{d["conclusion"]}</h2><p class="closing-note">{d["closingNote"]}</p></div></section>''')
    return "\n".join(slides)


def generate_slides_clean_review():
    d = MOCK_DATA
    slides = []

    slides.append(f'''<div class="slide slide-cover visible">
  <div class="cover">
    <div class="cover-badge">圆桌洞见 V5.0</div>
    <h1 class="cover-title">{d["title"]}</h1>
    <p class="cover-sub">{d["subtitle"]}</p>
    <div class="cover-stats">
      <div class="cover-stat"><div class="cover-stat-num">{d["expertCount"]}</div><div class="cover-stat-label">专家</div></div>
      <div class="cover-stat"><div class="cover-stat-num">{d["roundCount"]}</div><div class="cover-stat-label">轮次</div></div>
      <div class="cover-stat"><div class="cover-stat-num">{d["clashCount"]}+</div><div class="cover-stat-label">碰撞</div></div>
      <div class="cover-stat"><div class="cover-stat-num">{d["insightCount"]}</div><div class="cover-stat-label">洞见</div></div>
    </div>
  </div>
</div>''')

    slides.append(f'''<div class="slide experts-section">
  <div class="experts-grid">{_expert_cards_standard(d["experts"])}</div>
</div>''')

    for i, r in enumerate(d["rounds"]):
        speeches = ""
        for s in r["stances"]:
            speeches += f'''<div class="review-card"><div class="review-header"><div class="review-avatar">{s["initial"]}</div><div class="review-meta"><div class="review-name">{s["name"]}</div><div class="review-role">{s["roleLabel"]}</div></div></div><div class="review-content">{s["content"]}</div></div>'''
        clash_text = " ".join(f'{c["speaker"]}：{c["content"]}' for c in r["clashes"])
        slides.append(f'''<div class="slide round-section">
  <div class="round-card">
    <div class="round-tag">Round {i+1}</div>
    <h2 class="round-question">{r["question"]}</h2>
    {speeches}
    <div class="clash-block"><div class="clash-label">碰撞交锋</div><div class="clash-text">{clash_text}</div></div>
    <div class="insight-card"><div class="insight-label">核心洞见</div><div class="insight-text">{r["insight"]["core"]}</div></div>
  </div>
</div>''')

    cc = ""
    for i, c in enumerate(d["conclusions"]):
        cc += f'''<div class="conclusion-item"><div class="conclusion-num">{i+1}</div><div class="conclusion-text">{c}</div></div>'''
    slides.append(f'''<div class="slide"><div class="conclusions-section"><div class="conclusions">{cc}</div></div></div>''')

    qc = ""
    for i, q in enumerate(d["openQuestions"]):
        qc += f'''<div class="question-card"><div class="question-header"><div class="question-title">{q}</div><div class="question-icon">+</div></div><div class="question-answer">这是一个值得深入探讨的开放性问题。</div></div>'''
    slides.append(f'''<div class="slide">{qc}</div>''')

    slides.append(f'''<div class="slide"><div class="final-conclusion"><div class="final-conclusion-text">{d["conclusion"]}</div></div></div>''')
    return "\n".join(slides)


def generate_slides_editorial():
    d = MOCK_DATA
    slides = []

    slides.append(f'''<div class="slide active" id="s1">
  <div class="frame">
    <div class="left">
      <div class="issue">Roundtable Insights</div>
      <div class="version-badge"><span>V5.0</span></div>
      <div class="mega">{d["title"]}</div>
      <div class="subtext">{d["subtitle"]}</div>
    </div>
    <div class="right">
      <div class="article-row"><div class="art-num">01</div><div class="art-title">AI能否理解情感？</div><div class="art-body">情感理解的功能性与存在性之争</div></div>
      <div class="article-row"><div class="art-num">02</div><div class="art-title">算法与自主性</div><div class="art-body">权力结构如何塑造技术的影响</div></div>
      <div class="article-row"><div class="art-num">03</div><div class="art-title">人机协作的未来</div><div class="art-body">边界意识是协作的核心</div></div>
    </div>
  </div>
</div>''')

    slides.append(f'''<div class="slide">
  <div class="frame">
    <div class="content">
      <div class="head-block"><div class="head-tag">Panel</div><div class="head-title">专家阵容</div></div>
      <div class="stats-grid">
        <div class="stat-item"><div class="stat-num">{d["expertCount"]}</div><div class="stat-label">Experts</div></div>
        <div class="stat-item"><div class="stat-num">{d["roundCount"]}</div><div class="stat-label">Rounds</div></div>
        <div class="stat-item"><div class="stat-num">{d["clashCount"]}+</div><div class="stat-label">Clashes</div></div>
      </div>
      <div class="experts-grid">{_expert_cards_standard(d["experts"])}</div>
    </div>
  </div>
</div>''')

    for i, r in enumerate(d["rounds"]):
        clash_content = " ".join(f'{c["speaker"]}：{c["content"]}' for c in r["clashes"])
        slides.append(f'''<div class="slide">
  <div class="frame">
    <div class="content">
      <div class="head-block"><div class="head-tag">Round {i+1}</div><div class="head-title">{r["question"]}</div></div>
      <div class="round-block"><div class="round-title">{r["question"]}</div></div>
      <div class="clash-block"><div class="clash-title">碰撞交锋</div><div class="clash-content">{clash_content}</div></div>
      <div class="insight-block"><div class="insight-title">核心洞见</div><div class="insight-content">{r["insight"]["explain"]}<span class="insight-core">{r["insight"]["core"]}</span></div></div>
    </div>
  </div>
</div>''')

    slides.append(f'''<div class="slide">
  <div class="frame">
    <div class="content">
      <div class="head-block"><div class="head-tag">Conclusion</div><div class="head-title">结论</div></div>
      <div class="conclusion-card"><div class="conclusion-text">{d["conclusion"]}</div></div>
    </div>
  </div>
</div>''')

    qc = ""
    for i, q in enumerate(d["openQuestions"]):
        qc += f'''<div class="question-card"><div class="question-header"><div class="question-text">{q}</div><div class="question-toggle">+</div></div><div class="question-answer"><div class="question-answer-inner">这是一个值得深入探讨的开放性问题。</div></div></div>'''
    slides.append(f'''<div class="slide">
  <div class="frame">
    <div class="content">
      <div class="head-block"><div class="head-tag">Questions</div><div class="head-title">开放问题</div></div>
      {qc}
    </div>
  </div>
</div>''')
    return "\n".join(slides)


def generate_slides_geek_report():
    d = MOCK_DATA
    slides = []

    slides.append(f'''<div class="frame"><div class="inner"><div class="slides">
<div class="slide active">
  <div class="meta-line top"><span>Roundtable Insights</span><span>V5.0</span></div>
  <div class="hero-zone">
    <div class="version-badge"><span>V5.0</span></div>
    <div class="hero-label">// ROUNDTABLE</div>
    <div class="hero-title">{d["title"]}</div>
    <div class="hero-sub">{d["subtitle"]}</div>
  </div>
  <div class="stats-grid">
    <div class="stat-item"><div class="stat-num">{d["expertCount"]}</div><div class="stat-label">Experts</div></div>
    <div class="stat-item"><div class="stat-num">{d["roundCount"]}</div><div class="stat-label">Rounds</div></div>
    <div class="stat-item"><div class="stat-num">{d["clashCount"]}+</div><div class="stat-label">Clashes</div></div>
  </div>
  <div class="meta-line bottom"><span>AI &amp; Cognition</span><span>2026</span></div>
</div>''')

    slides.append(f'''<div class="slide">
  <div class="experts-grid">{_expert_cards_standard(d["experts"])}</div>
</div>''')

    for i, r in enumerate(d["rounds"]):
        statements = ""
        for s in r["stances"]:
            statements += f'''<div class="statement-block"><div class="statement-meta"><div class="statement-speaker">{s["name"]}</div><div class="statement-role">{s["roleLabel"]}</div></div><div class="statement-text">{s["content"]}</div></div>'''
        clash_content = " ".join(f'{c["speaker"]}：{c["content"]}' for c in r["clashes"])
        slides.append(f'''<div class="slide">
  <div class="meta-line top"><span>Round {i+1}</span><span>{d["roundCount"]}</span></div>
  <div class="round-block"><div class="round-title">{r["question"]}</div></div>
  <div class="statements-grid">{statements}</div>
  <div class="clash-block"><div class="clash-title">碰撞交锋</div><div class="clash-content">{clash_content}</div></div>
  <div class="insight-block"><div class="insight-title">核心洞见</div><div class="insight-content">{r["insight"]["explain"]}<span class="insight-core">{r["insight"]["core"]}</span></div></div>
  <div class="meta-line bottom"><span>AI &amp; Cognition</span><span>{i+1}/{d["roundCount"]}</span></div>
</div>''')

    slides.append(f'''<div class="slide">
  <div class="conclusion-card"><div class="conclusion-text">{d["conclusion"]}</div></div>
</div>''')

    qc = ""
    for i, q in enumerate(d["openQuestions"]):
        qc += f'''<div class="question-card"><div class="question-header"><div class="question-text">{q}</div><div class="question-toggle">+</div></div><div class="question-answer"><div class="question-answer-inner">这是一个值得深入探讨的开放性问题。</div></div></div>'''
    slides.append(f'''<div class="slide">
  <div class="meta-line top"><span>Questions</span><span>Open</span></div>
  {qc}
  <div class="meta-line bottom"><span>AI &amp; Cognition</span><span>?</span></div>
</div>''')

    slides.append('''</div></div></div>''')
    return "\n".join(slides)


def generate_slides_consulting_report():
    d = MOCK_DATA
    slides = []

    slides.append(f'''<div class="slide slide-cover visible">
  <div class="cover-badge">圆桌洞见 V5.0</div>
  <div class="cover-body">
    <h1 class="cover-title">{d["title"]}</h1>
    <p class="cover-sub">{d["subtitle"]}</p>
    <div class="cover-stats">
      <div class="cover-stat"><div class="cover-stat-num">{d["expertCount"]}</div><div class="cover-stat-label">专家</div></div>
      <div class="cover-stat"><div class="cover-stat-num">{d["roundCount"]}</div><div class="cover-stat-label">轮次</div></div>
      <div class="cover-stat"><div class="cover-stat-num">{d["clashCount"]}+</div><div class="cover-stat-label">碰撞</div></div>
      <div class="cover-stat"><div class="cover-stat-num">{d["insightCount"]}</div><div class="cover-stat-label">洞见</div></div>
    </div>
  </div>
</div>''')

    ec = ""
    for e in d["experts"]:
        ec += f'''<div class="expert-card"><div class="expert-avatar role-{e["role"]}">{e["initial"]}</div><div class="expert-name">{e["name"]}</div><div class="expert-role">{e["roleLabel"]}</div></div>'''
    slides.append(f'''<div class="slide"><div class="experts-grid">{ec}</div></div>''')

    for i, r in enumerate(d["rounds"]):
        speeches = ""
        for s in r["stances"]:
            speeches += f'''<div class="speech-card"><div class="speech-meta"><div class="speaker-avatar role-{s["role"]}">{s["initial"]}</div><div><div class="speaker-name">{s["name"]}</div><div class="speaker-role">{s["roleLabel"]}</div></div></div><div class="speech-content">{s["content"]}</div></div>'''
        clash_items = ""
        for c in r["clashes"]:
            clash_items += f'''<div class="clash-item"><div class="clash-speaker">{c["speaker"]}</div><div class="clash-text">{c["content"]}</div></div>'''
        slides.append(f'''<div class="slide">
  <div class="round-block"><div class="round-tag">Round {i+1}</div><div class="round-title">{r["question"]}</div></div>
  <div class="speech-cards">{speeches}</div>
  <div class="clash-block"><div class="clash-label">碰撞交锋</div>{clash_items}</div>
  <div class="insight-block"><div class="insight-label">核心洞见</div><div class="insight-core">{r["insight"]["core"]}</div><div class="insight-explain">{r["insight"]["explain"]}</div></div>
</div>''')

    cc = ""
    for i, c in enumerate(d["conclusions"]):
        cc += f'''<div class="conclusion-item"><div class="conclusion-num">{i+1}</div><div class="conclusion-text">{c}</div></div>'''
    slides.append(f'''<div class="slide"><div class="conclusions-grid">{cc}</div></div>''')

    qc = ""
    for i, q in enumerate(d["openQuestions"]):
        qc += f'''<div class="question-card"><div class="question-number">Q{i+1}</div><div class="question-text">{q}</div><div class="question-expand">这是一个值得深入探讨的开放性问题。</div></div>'''
    slides.append(f'''<div class="slide">{qc}</div>''')
    return "\n".join(slides)


def generate_slides_rain_notes():
    d = MOCK_DATA
    slides = []

    slides.append(f'''<div class="slide slide-cover visible">
  <div class="cover">
    <div class="cover-date">2026.05</div>
    <h1 class="cover-title">{d["title"]}</h1>
    <div class="cover-meta">{d["subtitle"]}</div>
    <div class="cover-stats">
      <div class="cover-stat"><div class="cover-stat-num">{d["expertCount"]}</div><div class="cover-stat-label">专家</div></div>
      <div class="cover-stat"><div class="cover-stat-num">{d["roundCount"]}</div><div class="cover-stat-label">轮次</div></div>
      <div class="cover-stat"><div class="cover-stat-num">{d["clashCount"]}+</div><div class="cover-stat-label">碰撞</div></div>
      <div class="cover-stat"><div class="cover-stat-num">{d["insightCount"]}</div><div class="cover-stat-label">洞见</div></div>
    </div>
  </div>
</div>''')

    slides.append(f'''<div class="slide experts-section">
  <div class="section-header"><div class="section-tag">Panel</div><div class="section-title">专家阵容</div></div>
  <div class="experts-grid">{_expert_cards_standard(d["experts"])}</div>
</div>''')

    for i, r in enumerate(d["rounds"]):
        notes = ""
        for s in r["stances"]:
            notes += f'''<div class="note-entry"><div class="note-speaker">{s["name"]}</div><div class="note-content">{s["content"]}</div></div>'''
        clash_text = " ".join(f'{c["speaker"]}：{c["content"]}' for c in r["clashes"])
        slides.append(f'''<div class="slide note-section">
  <div class="note-header"><div class="note-round">Round {i+1}</div><div class="note-question">{r["question"]}</div></div>
  <div class="notes-container">{notes}</div>
  <div class="clash-block"><div class="clash-label">碰撞交锋</div><div class="clash-text">{clash_text}</div></div>
  <div class="rain-insight"><div class="insight-marker">核心洞见</div><div class="insight-text">{r["insight"]["core"]}</div></div>
</div>''')

    cc = ""
    for i, c in enumerate(d["conclusions"]):
        cc += f'''<div class="conclusion-item"><div class="conclusion-num">{i+1}</div><div class="conclusion-text">{c}</div></div>'''
    slides.append(f'''<div class="slide"><div class="conclusions-section"><div class="conclusions">{cc}</div></div></div>''')

    qc = ""
    for i, q in enumerate(d["openQuestions"]):
        qc += f'''<div class="question-card"><div class="question-header"><div class="question-title">{q}</div><div class="question-icon">+</div></div><div class="question-answer">这是一个值得深入探讨的开放性问题。</div></div>'''
    slides.append(f'''<div class="slide">{qc}</div>''')

    slides.append(f'''<div class="slide"><div class="final-conclusion"><div class="final-conclusion-text">{d["conclusion"]}</div></div></div>''')
    return "\n".join(slides)


def _generate_slides_sunrise_pixel():
    d = MOCK_DATA
    slides = []

    slides.append(f'''<div class="slide slide-cover visible">
  <div class="cover-badge">圆桌洞见 V5.0</div>
  <h1 class="cover-title">{d["title"]}</h1>
  <p class="cover-sub">{d["subtitle"]}</p>
  <div class="cover-stats">
    <div class="cover-stat"><div class="cover-stat-num">{d["expertCount"]}</div><div class="cover-stat-label">专家</div></div>
    <div class="cover-stat"><div class="cover-stat-num">{d["roundCount"]}</div><div class="cover-stat-label">轮次</div></div>
    <div class="cover-stat"><div class="cover-stat-num">{d["clashCount"]}+</div><div class="cover-stat-label">碰撞</div></div>
    <div class="cover-stat"><div class="cover-stat-num">{d["insightCount"]}</div><div class="cover-stat-label">洞见</div></div>
  </div>
</div>''')

    slides.append(f'''<div class="slide">
  <div class="section-header"><div class="section-tag">Panel</div><div class="section-title">专家阵容</div></div>
  <div class="experts-grid">{_expert_cards_standard(d["experts"])}</div>
</div>''')

    for i, r in enumerate(d["rounds"]):
        speeches = ""
        for s in r["stances"]:
            speeches += f'''<div class="speech-block"><div class="speech-header"><div class="speech-avatar">{s["initial"]}</div><div><div class="speech-name">{s["name"]}</div><div class="speech-role">{s["roleLabel"]}</div></div></div><div class="speech-content">{s["content"]}</div></div>'''
        clash_content = " ".join(f'{c["speaker"]}：{c["content"]}' for c in r["clashes"])
        slides.append(f'''<div class="slide slide-content">
  <div class="round-card"><div class="round-header"><div class="round-badge">Round {i+1}</div></div><div class="round-title">{r["question"]}</div></div>
  {speeches}
  <div class="clash-block"><div class="clash-content">{clash_content}</div></div>
  <div class="insight-block"><div class="insight-label">核心洞见</div><div class="insight-text">{r["insight"]["core"]}</div></div>
</div>''')

    slides.append(f'''<div class="slide"><div class="conclusion-card"><div class="conclusion-title">结论</div><div class="conclusion-text">{d["conclusion"]}</div></div></div>''')

    qc = ""
    for i, q in enumerate(d["openQuestions"]):
        qc += f'''<div class="question-card"><div class="question-header"><div class="question-title">{q}</div><div class="question-icon">+</div></div><div class="question-content"><div class="question-text">这是一个值得深入探讨的开放性问题。</div></div></div>'''
    slides.append(f'''<div class="slide">{qc}</div>''')
    return "\n".join(slides)


def generate_slides_sunrise():
    return _generate_slides_sunrise_pixel()


def generate_slides_pixel_report():
    return _generate_slides_sunrise_pixel()


def _generate_slides_dot_matrix():
    d = MOCK_DATA
    slides = []

    slides.append(f'''<section class="section section-cover visible">
  <div class="frame">
    <div class="main-title">{d["title"]}</div>
    <div class="subtitle">{d["subtitle"]}</div>
    <div class="stats-row">
      <div class="stat-item"><div class="stat-number">{d["expertCount"]}</div><div class="stat-label">专家</div></div>
      <div class="stat-item"><div class="stat-number">{d["roundCount"]}</div><div class="stat-label">轮次</div></div>
      <div class="stat-item"><div class="stat-number">{d["clashCount"]}+</div><div class="stat-label">碰撞</div></div>
      <div class="stat-item"><div class="stat-number">{d["insightCount"]}</div><div class="stat-label">洞见</div></div>
    </div>
  </div>
</section>''')

    ec = ""
    for e in d["experts"]:
        ec += f'''<div class="expert-card"><div class="expert-avatar">{e["initial"]}</div><div class="expert-name">{e["name"]}</div><div class="expert-title">{e["role"]}</div></div>'''
    slides.append(f'''<section class="section"><div class="frame"><div class="experts-grid">{ec}</div></div></section>''')

    for i, r in enumerate(d["rounds"]):
        speeches = ""
        for s in r["stances"]:
            speeches += f'''<div class="speech-block"><div class="speech-meta"><div class="speech-speaker">{s["name"]}</div><div class="speech-tag">{s["roleLabel"]}</div></div><div class="speech-content">{s["content"]}</div></div>'''
        clash_content = " ".join(f'{c["speaker"]}：{c["content"]}' for c in r["clashes"])
        slides.append(f'''<section class="section section-round">
  <div class="frame">
    <div class="round-header"><div class="round-label">Round {i+1}</div><div class="round-title">{r["question"]}</div></div>
    {speeches}
    <div class="clash-block"><div class="clash-header">碰撞交锋</div><div class="clash-content">{clash_content}</div></div>
    <div class="insight-block"><div class="insight-header">核心洞见</div><div class="insight-core">{r["insight"]["core"]}</div><div class="insight-detail">{r["insight"]["explain"]}</div></div>
  </div>
</section>''')

    slides.append(f'''<section class="section"><div class="frame"><div class="conclusion-card"><div class="conclusion-title">结论</div><div class="conclusion-text">{d["conclusion"]}</div></div></div></section>''')

    qc = ""
    for i, q in enumerate(d["openQuestions"]):
        qc += f'''<div class="question-card"><div class="q-text">{q}</div><div class="q-answer">这是一个值得深入探讨的开放性问题。</div></div>'''
    slides.append(f'''<section class="section"><div class="frame">{qc}</div></section>''')
    return "\n".join(slides)


def generate_slides_dot_matrix():
    return _generate_slides_dot_matrix()


def generate_slides_dot_matrix_light():
    return _generate_slides_dot_matrix()


def _generate_slides_shiny_tiles():
    d = MOCK_DATA
    slides = []

    slides.append(f'''<div class="slide slide-cover visible">
  <div class="frame">
    <div class="cover-badge">圆桌洞见 V5.0</div>
    <h1 class="cover-title">{d["title"]}</h1>
    <p class="cover-subtitle">{d["subtitle"]}</p>
    <div class="cover-stats">
      <div class="stat-item"><div class="stat-number">{d["expertCount"]}</div><div class="stat-label">专家</div></div>
      <div class="stat-item"><div class="stat-number">{d["roundCount"]}</div><div class="stat-label">轮次</div></div>
      <div class="stat-item"><div class="stat-number">{d["clashCount"]}+</div><div class="stat-label">碰撞</div></div>
      <div class="stat-item"><div class="stat-number">{d["insightCount"]}</div><div class="stat-label">洞见</div></div>
    </div>
  </div>
</div>''')

    slides.append(f'''<div class="slide slide-content">
  <div class="section-header"><div class="section-label">Panel</div><div class="section-title">专家阵容</div></div>
  <div class="experts-grid">{_expert_cards_standard(d["experts"])}</div>
</div>''')

    for i, r in enumerate(d["rounds"]):
        speeches = ""
        for s in r["stances"]:
            speeches += f'''<div class="speech-block"><div class="speech-header"><div class="speech-avatar">{s["initial"]}</div><div><div class="speech-name">{s["name"]}</div><div class="speech-role">{s["roleLabel"]}</div></div></div><div class="speech-content">{s["content"]}</div></div>'''
        clash_content = " ".join(f'{c["speaker"]}：{c["content"]}' for c in r["clashes"])
        slides.append(f'''<div class="slide slide-content">
  <div class="round-card"><div class="round-header"><div class="round-badge">Round {i+1}</div></div><div class="round-title">{r["question"]}</div></div>
  {speeches}
  <div class="clash-block"><div class="clash-label">碰撞交锋</div><div class="clash-content">{clash_content}</div></div>
  <div class="insight-block"><div class="insight-label">核心洞见</div><div class="insight-text">{r["insight"]["explain"]}</div><div class="insight-core">{r["insight"]["core"]}</div></div>
</div>''')

    slides.append(f'''<div class="slide slide-content"><div class="conclusion-card"><div class="conclusion-label">结论</div><div class="conclusion-text">{d["conclusion"]}</div></div></div>''')

    qc = ""
    for i, q in enumerate(d["openQuestions"]):
        qc += f'''<div class="question-card"><div class="question-header"><div class="question-text">{q}</div><div class="question-icon">+</div></div><div class="question-expand"><div class="question-answer">这是一个值得深入探讨的开放性问题。</div></div></div>'''
    slides.append(f'''<div class="slide slide-content">{qc}</div>''')
    return "\n".join(slides)


def generate_slides_shiny_tiles():
    return _generate_slides_shiny_tiles()


def generate_slides_studio_photo():
    d = MOCK_DATA
    slides = []

    slides.append(f'''<div class="slide slide-cover visible">
  <div class="frame">
    <div class="cover-badge">圆桌洞见 V5.0</div>
    <h1 class="cover-title">{d["title"]}</h1>
    <p class="cover-subtitle">{d["subtitle"]}</p>
    <div class="cover-stats">
      <div class="stat-item"><div class="stat-number">{d["expertCount"]}</div><div class="stat-label">专家</div></div>
      <div class="stat-item"><div class="stat-number">{d["roundCount"]}</div><div class="stat-label">轮次</div></div>
      <div class="stat-item"><div class="stat-number">{d["clashCount"]}+</div><div class="stat-label">碰撞</div></div>
      <div class="stat-item"><div class="stat-number">{d["insightCount"]}</div><div class="stat-label">洞见</div></div>
    </div>
  </div>
</div>''')

    slides.append(f'''<div class="slide slide-ice">
  <div class="frame">
    <div class="section-header"><div class="section-label">Panel</div><div class="section-title">专家阵容</div></div>
    <div class="experts-grid">{_expert_cards_standard(d["experts"])}</div>
  </div>
</div>''')

    for i, r in enumerate(d["rounds"]):
        photo_cards = ""
        for s in r["stances"]:
            photo_cards += f'''<div class="photo-card"><div class="photo-placeholder">PHOTO</div><div class="photo-body"><div class="photo-speaker">{s["name"]}</div><div class="photo-role">{s["roleLabel"]}</div><div class="photo-content">{s["content"]}</div></div></div>'''
        clash_content = " ".join(f'{c["speaker"]}：{c["content"]}' for c in r["clashes"])
        slides.append(f'''<div class="slide slide-dark">
  <div class="frame">
    <div class="round-card"><div class="round-header"><div class="round-badge">Round {i+1}</div></div><div class="round-title">{r["question"]}</div></div>
    {photo_cards}
    <div class="clash-block"><div class="clash-label">碰撞交锋</div><div class="clash-content">{clash_content}</div></div>
    <div class="studio-insight"><div class="studio-label">核心洞见</div><div class="studio-text">{r["insight"]["core"]}</div></div>
  </div>
</div>''')

    slides.append(f'''<div class="slide slide-ice"><div class="frame"><div class="conclusion-card"><div class="conclusion-label">结论</div><div class="conclusion-text">{d["conclusion"]}</div></div></div></div>''')

    qc = ""
    for i, q in enumerate(d["openQuestions"]):
        qc += f'''<div class="question-card"><div class="question-header"><div class="question-text">{q}</div><div class="question-icon">+</div></div><div class="question-expand"><div class="question-answer">这是一个值得深入探讨的开放性问题。</div></div></div>'''
    slides.append(f'''<div class="slide slide-dark"><div class="frame">{qc}</div></div>''')
    return "\n".join(slides)


def _generate_slides_story_field():
    d = MOCK_DATA
    slides = []

    slides.append(f'''<div class="slide slide-cover visible">
  <div class="frame">
    <div class="main-title">{d["title"]}</div>
    <div class="main-subtitle">{d["subtitle"]}</div>
    <div class="stats-row">
      <div class="stat-item"><div class="stat-number">{d["expertCount"]}</div><div class="stat-label">专家</div></div>
      <div class="stat-item"><div class="stat-number">{d["roundCount"]}</div><div class="stat-label">轮次</div></div>
      <div class="stat-item"><div class="stat-number">{d["clashCount"]}+</div><div class="stat-label">碰撞</div></div>
      <div class="stat-item"><div class="stat-number">{d["insightCount"]}</div><div class="stat-label">洞见</div></div>
    </div>
  </div>
</div>''')

    slides.append(f'''<div class="slide slide-content">
  <div class="frame">
    <div class="experts-grid">{_expert_cards_standard(d["experts"])}</div>
  </div>
</div>''')

    for i, r in enumerate(d["rounds"]):
        speeches = ""
        for s in r["stances"]:
            speeches += f'''<div class="speech-block"><div class="speech-speaker">{s["name"]}<span class="speech-role">{s["roleLabel"]}</span></div><div class="speech-content">{s["content"]}</div></div>'''
        clash_content = " ".join(f'{c["speaker"]}：{c["content"]}' for c in r["clashes"])
        slides.append(f'''<div class="slide slide-content">
  <div class="frame">
    <div class="round-card"><div class="round-header"><div class="round-badge">Round {i+1}</div></div><div class="round-theme">{r["question"]}</div></div>
    {speeches}
    <div class="clash-block"><div class="clash-label">碰撞交锋</div><div class="clash-content">{clash_content}</div></div>
    <div class="insight-block"><div class="insight-label">核心洞见</div><div class="insight-core">{r["insight"]["core"]}</div><div class="insight-detail">{r["insight"]["explain"]}</div></div>
  </div>
</div>''')

    slides.append(f'''<div class="slide slide-content"><div class="frame"><div class="conclusion-card"><div class="conclusion-label">结论</div><div class="conclusion-text">{d["conclusion"]}</div></div></div></div>''')

    qc = ""
    for i, q in enumerate(d["openQuestions"]):
        qc += f'''<div class="question-card"><div class="question-header"><div class="question-title">{q}</div><div class="question-icon">+</div></div><div class="question-body"><div class="question-text">这是一个值得深入探讨的开放性问题。</div></div></div>'''
    slides.append(f'''<div class="slide slide-content"><div class="frame">{qc}</div></div>''')
    return "\n".join(slides)


def generate_slides_story_field():
    return _generate_slides_story_field()


def generate_slides_y2k_brand():
    d = MOCK_DATA
    slides = []

    slides.append(f'''<div class="slide slide-cover visible">
  <div class="frame">
    <div class="glitch-badge">ROUNDTABLE V5.0</div>
    <div class="main-title">{d["title"]}</div>
    <div class="main-subtitle">{d["subtitle"]}</div>
    <div class="stats-row">
      <div class="stat-item"><div class="stat-number">{d["expertCount"]}</div><div class="stat-label">专家</div></div>
      <div class="stat-item"><div class="stat-number">{d["roundCount"]}</div><div class="stat-label">轮次</div></div>
      <div class="stat-item"><div class="stat-number">{d["clashCount"]}+</div><div class="stat-label">碰撞</div></div>
      <div class="stat-item"><div class="stat-number">{d["insightCount"]}</div><div class="stat-label">洞见</div></div>
    </div>
  </div>
</div>''')

    slides.append(f'''<div class="slide slide-content">
  <div class="frame">
    <div class="experts-grid">{_expert_cards_standard(d["experts"])}</div>
  </div>
</div>''')

    for i, r in enumerate(d["rounds"]):
        speeches = ""
        for s in r["stances"]:
            speeches += f'''<div class="speech-block"><div class="speech-speaker">{s["name"]}<span class="speech-role">{s["roleLabel"]}</span></div><div class="speech-content">{s["content"]}</div></div>'''
        clash_content = " ".join(f'{c["speaker"]}：{c["content"]}' for c in r["clashes"])
        slides.append(f'''<div class="slide slide-content">
  <div class="frame">
    <div class="window"><div class="window-header"><div class="window-title">Round {i+1}</div><div class="window-dots"><div class="window-dot"></div><div class="window-dot"></div><div class="window-dot"></div></div></div><div class="window-body">
      <div class="round-card"><div class="round-header"><div class="round-badge">Round {i+1}</div></div><div class="round-theme">{r["question"]}</div></div>
      {speeches}
      <div class="clash-block"><div class="clash-label">碰撞交锋</div><div class="clash-content">{clash_content}</div></div>
      <div class="insight-block"><div class="insight-label">核心洞见</div><div class="insight-core">{r["insight"]["core"]}</div><div class="insight-detail">{r["insight"]["explain"]}</div></div>
    </div></div>
  </div>
</div>''')

    slides.append(f'''<div class="slide slide-content"><div class="frame"><div class="conclusion-card"><div class="conclusion-label">结论</div><div class="conclusion-text">{d["conclusion"]}</div></div></div></div>''')

    qc = ""
    for i, q in enumerate(d["openQuestions"]):
        qc += f'''<div class="question-card"><div class="question-header"><div class="question-title">{q}</div><div class="question-icon">+</div></div><div class="question-body"><div class="question-text">这是一个值得深入探讨的开放性问题。</div></div></div>'''
    slides.append(f'''<div class="slide slide-content"><div class="frame">{qc}</div></div>''')
    return "\n".join(slides)


GENERATORS = {
    "template-premium-dark.html": generate_slides_premium_dark,
    "template-clean-review.html": generate_slides_clean_review,
    "template-editorial.html": generate_slides_editorial,
    "template-geek-report.html": generate_slides_geek_report,
    "template-consulting-report.html": generate_slides_consulting_report,
    "template-rain-notes.html": generate_slides_rain_notes,
    "template-sunrise.html": generate_slides_sunrise,
    "template-pixel-report.html": generate_slides_pixel_report,
    "template-dot-matrix.html": generate_slides_dot_matrix,
    "template-dot-matrix-light.html": generate_slides_dot_matrix_light,
    "template-shiny-tiles.html": generate_slides_shiny_tiles,
    "template-studio-photo.html": generate_slides_studio_photo,
    "template-story-field.html": generate_slides_story_field,
    "template-y2k-brand.html": generate_slides_y2k_brand,
}


def generate_test_html(template_file: Path, template_name: str) -> str:
    template_content = template_file.read_text(encoding="utf-8")
    generator = GENERATORS.get(template_name)
    if not generator:
        return None
    slides_html = generator()
    html = template_content.replace("{{slides}}", slides_html)
    html = html.replace("{{title}}", MOCK_DATA["title"])
    html = html.replace("{{subtitle}}", MOCK_DATA["subtitle"])
    html = html.replace("{{expertCount}}", str(MOCK_DATA["expertCount"]))
    html = html.replace("{{roundCount}}", str(MOCK_DATA["roundCount"]))
    html = html.replace("{{clashCount}}", str(MOCK_DATA["clashCount"]))
    html = html.replace("{{insightCount}}", str(MOCK_DATA["insightCount"]))
    html = html.replace("{{conclusion}}", MOCK_DATA["conclusion"])
    html = html.replace("{{closingNote}}", MOCK_DATA["closingNote"])
    return html


def main():
    TEST_DIR.mkdir(exist_ok=True)
    all_templates = sorted(ENGINE_DIR.glob("template-*.html"))
    generated = 0
    skipped = 0

    for template_file in all_templates:
        template_name = template_file.name
        if template_name in SKIP_TEMPLATES:
            print(f"⏭️ {template_name} (Handlebars模板，跳过)")
            skipped += 1
            continue
        if template_name not in GENERATORS:
            print(f"⚠️ {template_name} (无对应生成器，跳过)")
            skipped += 1
            continue

        output_name = template_name.replace("template-", "test_")
        output_file = TEST_DIR / output_name
        html = generate_test_html(template_file, template_name)
        if html:
            output_file.write_text(html, encoding="utf-8")
            print(f"✅ {template_name} → {output_file.name}")
            generated += 1
        else:
            print(f"❌ {template_name} 生成失败")
            skipped += 1

    mock_json = TEST_DIR / "mock_data.json"
    with open(mock_json, "w", encoding="utf-8") as f:
        json.dump(MOCK_DATA, f, ensure_ascii=False, indent=2)
    print(f"📄 模拟数据: {mock_json.name}")
    print(f"\n📊 共生成 {generated} 个测试文件，跳过 {skipped} 个，输出到: {TEST_DIR}")


if __name__ == "__main__":
    main()

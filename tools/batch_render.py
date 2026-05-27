# -*- coding: utf-8 -*-
"""批量渲染5个新话题的讨论JSON到HTML"""

import json
import os

def convert_to_render_format(input_path: str, output_path: str):
    """将讨论JSON转换为render_roundtable.js期望的格式"""

    with open(input_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    # 提取专家信息
    experts = []
    expert_names = set()
    for round_data in data.get("rounds", []):
        for speaker in round_data.get("speakers", []):
            name = speaker.get("name", "")
            if name and name not in expert_names:
                expert_names.add(name)
                role = speaker.get("role", "")
                color = speaker.get("avatar_color", "#4a6a9a")

                # 为每个专家分配一个emoji作为头像
                emojis = ["🎓", "📚", "💡", "🔍", "⚖️", "🎯"]
                avatar_idx = len(experts) % len(emojis)

                experts.append({
                    "id": name,
                    "name": name,
                    "title": role,
                    "avatar": emojis[avatar_idx],
                    "color": color
                })

    # 构建轮次
    rounds = []
    for i, round_data in enumerate(data.get("rounds", [])):
        discussions = []
        for speaker in round_data.get("speakers", []):
            discussions.append({
                "expert_id": speaker.get("name", ""),
                "stance": round_data.get("question", ""),
                "content": speaker.get("content", ""),
                "quotes": [],
                "citations": []
            })

        collision = round_data.get("clashes", [])
        collision_content = ""
        if collision:
            c = collision[0]
            collision_content = f"{c.get('expert', '')}：{c.get('content', '')}"

        rounds.append({
            "title": round_data.get("topic", ""),
            "description": round_data.get("question", ""),
            "discussions": discussions,
            "collision": {
                "title": f"第{i+1}轮碰撞",
                "content": collision_content
            }
        })

    # 提取洞见
    key_insights = []
    for i, round_data in enumerate(data.get("rounds", [])):
        insight = round_data.get("insight", {})
        if insight:
            key_insights.append({
                "expert": f"第{i+1}轮综合",
                "title": insight.get("statement", "")[:100],
                "summary": insight.get("explanation", "")[:300]
            })

    output = {
        "title": data.get("title", ""),
        "subtitle": data.get("subtitle", ""),
        "date": "2026-05-26",
        "experts": experts,
        "rounds": rounds,
        "key_insights": key_insights
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Converted: {input_path} -> {output_path}")
    return output


def render_html(json_path: str, output_path: str):
    """使用Node.js渲染HTML"""
    import subprocess

    # 创建一个临时的渲染脚本
    script_content = f'''const fs = require('fs');
const path = require('path');

const jsonPath = path.join(__dirname, '..', 'content', '{os.path.basename(json_path)}');
const outputPath = path.join(__dirname, '..', 'output', '{os.path.basename(output_path)}');

const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

function escapeHtml(str) {{
  if (!str) return '';
  return str.replace(/&/g, '&amp;')
             .replace(/</g, '&lt;')
             .replace(/>/g, '&gt;')
             .replace(/"/g, '&quot;')
             .replace(/'/g, '&#039;');
}}

function getExpertById(id) {{
  return data.experts.find(e => e.id === id) || {{}};
}}

function generateSpeakerCard(expertId, stance, content, quotes = [], citations = []) {{
  const expert = getExpertById(expertId);
  const avatar = expert.avatar || '💬';
  const name = expert.name || expertId;
  const title = expert.title || '';
  const color = expert.color || 'var(--accent)';

  let quotesHtml = '';
  if (quotes && quotes.length > 0) {{
    quotesHtml = `<div style="margin-top:1.5vh;display:flex;flex-direction:column;gap:.5vh">`;
    quotes.forEach(q => {{
      quotesHtml += `<div style="font-family:var(--serif-zh);font-size:.88rem;font-style:italic;color:var(--gold);padding-left:1vw;border-left:2px solid rgba(var(--gold-rgb),.4);margin-bottom:.5vh">"${{escapeHtml(q)}}"</div>`;
    }});
    quotesHtml += `</div>`;
  }}

  let citationsHtml = '';
  if (citations && citations.length > 0) {{
    citationsHtml = `<div style="margin-top:1.5vh;font-family:var(--mono);font-size:10px;color:rgba(var(--paper-rgb),.35);letter-spacing:.05em">📌 ${{citations.map(c => escapeHtml(c)).join(' · ')}}</div>`;
  }}

  return `<div class="sp" style="border-left-color:${{color}}">
    <div class="sh">
      <div class="speaker-avatar" style="background:${{color}}">${{avatar}}</div>
      <div>
        <div class="sn">${{escapeHtml(name)}}</div>
        <div class="sr">${{escapeHtml(title)}}</div>
      </div>
    </div>
    ${{stance ? `<div style="font-size:.9rem;font-weight:600;color:var(--gold);margin-bottom:1.5vh;padding-bottom:1vh;border-bottom:1px solid rgba(var(--paper-rgb),.08)">▸ ${{escapeHtml(stance)}}</div>` : ''}}
    <div class="st">${{content.split('\\n').map(p => `<p style="margin-bottom:1.2vh;line-height:1.9">${{escapeHtml(p)}}</p>`).join('')}}</div>
    ${{quotesHtml}}
    ${{citationsHtml}}
  </div>`;
}}

function generateCollision(collision) {{
  if (!collision) return '';

  const parts = collision.content.split('\\n').filter(p => p.trim());

  return `<div style="background:rgba(var(--accent-rgb),.06);border:1px solid rgba(var(--accent-rgb),.15);border-radius:var(--radius);padding:3vh 2.5vw;margin-top:2vh">
    <div style="font-family:var(--mono);font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);margin-bottom:2vh;font-weight:700">⚡ 专家交锋</div>
    <div style="font-family:var(--serif-zh);font-size:1.05rem;font-weight:600;margin-bottom:2vh;line-height:1.6">${{escapeHtml(collision.title)}}</div>
    <div class="st">${{parts.map(p => `<p style="margin-bottom:1.2vh;line-height:1.9">${{escapeHtml(p)}}</p>`).join('')}}</div>
  </div>`;
}}

function generateInsightsPage() {{
  let insightsHtml = '<div class="grid-2">';
  data.key_insights.forEach((insight, i) => {{
    insightsHtml += `<div class="insight-c" style="animation-delay:${{i * 0.1}}s">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:2vh">
        <span style="font-family:var(--mono);font-size:1.5rem;font-weight:900;color:var(--accent);opacity:.5">0${{i+1}}</span>
        <span style="font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--gold);padding:3px 8px;background:rgba(var(--gold-rgb),.1);border-radius:3px">${{escapeHtml(insight.expert)}}</span>
      </div>
      <div class="insight-q">${{escapeHtml(insight.title)}}</div>
      <div class="insight-a">${{escapeHtml(insight.summary)}}</div>
    </div>`;
  }});
  insightsHtml += '</div>';
  return insightsHtml;
}}

function generateDiscussionPage(round) {{
  let html = '';

  round.discussions.forEach((d, i) => {{
    html += generateSpeakerCard(d.expert_id, d.stance, d.content, d.quotes, d.citations);
  }});

  html += generateCollision(round.collision);

  return html;
}}

let slidesHtml = '';

// Slide 0: Cover
slidesHtml += `<div class="slide hero title-slide" data-title="${{escapeHtml(data.title)}}">
  <div class="frame">
    <div class="slide-content" style="justify-content:center;align-items:center;text-align:center">
      <div class="cover-badge" data-anim>圆桌洞见</div>
      <div class="cover-title" data-anim>${{escapeHtml(data.title)}}</div>
      <div class="cover-sub" data-anim>${{escapeHtml(data.subtitle)}}</div>
      <div class="gold-line" data-anim></div>
      <div class="cover-stats" data-anim>
        <div class="cover-stat">
          <div class="cover-stat-num">6</div>
          <div class="cover-stat-label">专家</div>
        </div>
        <div class="cover-stat">
          <div class="cover-stat-num">3</div>
          <div class="cover-stat-label">轮讨论</div>
        </div>
        <div class="cover-stat">
          <div class="cover-stat-num">${{data.rounds.reduce((sum, r) => sum + r.discussions.length, 0)}}</div>
          <div class="cover-stat-label">发言</div>
        </div>
        <div class="cover-stat">
          <div class="cover-stat-num">${{data.key_insights.length}}</div>
          <div class="cover-stat-label">洞见</div>
        </div>
      </div>
      <div class="meta-row" data-anim>
        ${{data.experts.map(e => `<span>${{e.avatar}} ${{escapeHtml(e.name)}}</span>`).join(' · ')}}
      </div>
    </div>
  </div>
</div>`;

// Slide 1: Key Insights Overview
slidesHtml += `<div class="slide" data-title="核心洞见">
  <div class="frame">
    <div class="kicker" data-anim>KEY INSIGHTS</div>
    <div class="h-xl" data-anim style="margin-bottom:4vh">核心洞见</div>
    ${{generateInsightsPage()}}
    <div class="deck-footer">${{data.key_insights.length}}个核心观点</div>
  </div>
</div>`;

// Discussion Rounds
data.rounds.forEach((round, roundIdx) => {{
  const roundNum = roundIdx + 1;

  // Round Title Slide
  slidesHtml += `<div class="slide title-slide" data-title="第${{roundNum}}轮：${{escapeHtml(round.title)}}">
    <div class="frame">
      <div class="hero-dark">
        <div class="kicker" data-anim>ROUND ${{roundNum}}</div>
        <div class="h-hero" data-anim style="background:linear-gradient(135deg,var(--paper) 0%,var(--gold) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">${{escapeHtml(round.title)}}</div>
        <div class="quote-large" data-anim style="max-width:700px;margin-top:3vh">${{escapeHtml(round.description)}}</div>
      </div>
    </div>
  </div>`;

  // Discussion Content
  slidesHtml += `<div class="slide" data-title="第${roundNum}轮：专家发言">
    <div class="frame">
      <div class="kicker" data-anim>ROUND ${roundNum} · 专家发言</div>
      <div class="h-lg" data-anim style="margin-bottom:3vh">${escapeHtml(round.title)}</div>
      ${generateDiscussionPage(round)}
      <div class="deck-footer">第 ${roundNum}/3 轮 · ${round.discussions.length} 位专家发言</div>
    </div>
  </div>`;
}});

// Final Slide
slidesHtml += `<div class="slide hero title-slide" data-title="结语">
  <div class="frame">
    <div class="slide-content" style="justify-content:center;align-items:center;text-align:center">
      <div class="kicker" data-anim>CONCLUSION</div>
      <div class="h-hero" data-anim style="margin-bottom:4vh">${{escapeHtml(data.title)}}</div>
      <div class="quote-large" data-anim style="max-width:800px;margin-bottom:4vh">
        ${{escapeHtml(data.key_insights[0]?.summary || '圆桌洞见 · 多元视角的碰撞与融合')}}
      </div>
      <div class="gold-line" data-anim></div>
      <div class="meta-row" data-anim>
        ${{data.experts.map(e => `<span>${{e.avatar}} ${{escapeHtml(e.name)}}</span>`).join(' · ')}}
      </div>
      <div style="margin-top:4vh;font-family:var(--mono);font-size:11px;letter-spacing:.15em;text-transform:uppercase;opacity:.4" data-anim>
        圆桌洞见 · ${{data.date}}
      </div>
    </div>
  </div>
</div>`;

// Read template and inject slides
const templatePath = path.join(__dirname, '..', 'assets', 'roundtable-template.html');
let template = fs.readFileSync(templatePath, 'utf-8');

template = template.replace('__BOOK_TITLE__', data.title);
template = template.replace('<!-- SLIDES_HERE -->', slidesHtml);

fs.writeFileSync(outputPath, template, 'utf-8');
console.log(`HTML generated: ${{outputPath}}`);
'''

    # 写入临时脚本
    script_path = os.path.join(os.path.dirname(json_path), '_temp_render.js')
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)

    # 运行Node.js脚本
    try:
        result = subprocess.run(
            ['node', script_path],
            cwd=os.path.dirname(json_path),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"Failed to run Node.js: {e}")
    finally:
        # 删除临时脚本
        if os.path.exists(script_path):
            os.remove(script_path)


def main():
    content_dir = "content"
    output_dir = "output"

    topics = [
        ("算法情感_金融信任套利_讨论.json", "算法情感_金融信任套利_圆桌洞见.html"),
        ("多巴胺_叙事降级_讨论.json", "多巴胺_叙事降级_圆桌洞见.html"),
        ("数字农奴_生活殖民化_讨论.json", "数字农奴_生活殖民化_圆桌洞见.html"),
        ("银幕景观_底层债务_讨论.json", "银幕景观_底层债务_圆桌洞见.html"),
        ("人机协作_权力倒挂_讨论.json", "人机协作_权力倒挂_圆桌洞见.html"),
    ]

    for input_file, output_file in topics:
        input_path = os.path.join(content_dir, input_file)
        output_path = os.path.join(output_dir, output_file)

        if os.path.exists(input_path):
            print(f"\n{'='*50}")
            print(f"Processing: {input_file}")

            # 转换格式
            temp_json = input_path.replace('.json', '_temp.json')
            convert_to_render_format(input_path, temp_json)

            # 渲染HTML
            render_html(temp_json, output_path)

            # 删除临时JSON
            if os.path.exists(temp_json):
                os.remove(temp_json)
        else:
            print(f"File not found: {input_path}")

    print("\n" + "="*50)
    print("All topics processed!")


if __name__ == "__main__":
    main()

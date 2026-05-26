# -*- coding: utf-8 -*-
"""圆桌会议HTML渲染引擎 - 负责将JSON内容渲染为HTML"""

import json
import os
from typing import Dict, Any
from schema import RoundtablePPT, validate_content


class RoundtableRenderer:
    """圆桌会议渲染器"""
    
    def __init__(self, template_dir: str):
        self.template_dir = template_dir
        self.base_template = self._load_template("base.html")
        self.css = self._load_template("css/style.css")
        self.js = self._load_template("js/app.js")
    
    def _load_template(self, filename: str) -> str:
        """加载模板文件"""
        path = os.path.join(self.template_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def render_cover(self, ppt: RoundtablePPT) -> str:
        """渲染封面"""
        return f'''
<div class="slide hero active" data-title="封面">
  <div class="frame">
    <div class="cover-badge">圆桌洞见 V3.0</div>
    <h1 class="cover-title">{ppt.title}</h1>
    <p class="cover-sub">{ppt.subtitle}</p>
    <div class="cover-stats">
      <div class="cover-stat">
        <div class="cover-stat-num">{ppt.dashboard.total_experts}</div>
        <div class="cover-stat-label">参与专家</div>
      </div>
      <div class="cover-stat">
        <div class="cover-stat-num">{ppt.dashboard.total_rounds}</div>
        <div class="cover-stat-label">讨论轮次</div>
      </div>
      <div class="cover-stat">
        <div class="cover-stat-num">{ppt.dashboard.total_clashes}+</div>
        <div class="cover-stat-label">碰撞交锋</div>
      </div>
      <div class="cover-stat">
        <div class="cover-stat-num">{ppt.dashboard.total_insights}</div>
        <div class="cover-stat-label">核心洞见</div>
      </div>
    </div>
  </div>
</div>
'''
    
    def render_speaker(self, speaker) -> str:
        """渲染发言块"""
        return f'''
    <div class="sp" data-anim>
      <div class="sh">
        <div class="speaker-avatar" style="background:{speaker.avatar_color}">{speaker.name[0]}</div>
        <span class="sn">{speaker.name}</span>
        <span class="sr">{speaker.role}</span>
      </div>
      <div class="st">{speaker.content}</div>
    </div>'''
    
    def render_clash(self, clash) -> str:
        """渲染碰撞块"""
        color_map = {
            "情节反驳": "red",
            "细节挑战": "blue",
            "逻辑追问": "purple",
            "框架质疑": "orange",
            "反例引入": "green"
        }
        color = color_map.get(clash.type, "red")
        return f'''
    <div class="cb {color}" data-anim>
      <div class="cl {color}">{clash.type}</div>
      <div class="sh"><span class="sn">{clash.expert}</span></div>
      <div class="st">{clash.content}</div>
    </div>'''
    
    def render_insight(self, insight) -> str:
        """渲染洞见卡"""
        return f'''
    <div class="insight-c" data-anim>
      <div class="insight-q">{insight.statement}</div>
      <div class="insight-a">{insight.explanation}</div>
    </div>'''
    
    def render_round(self, round_data, is_first: bool = False) -> str:
        """渲染一个完整轮次"""
        slides = []
        
        # 标题页
        slides.append(f'''
<div class="slide title-slide" data-title="Round {round_data.round_number}: {round_data.topic}">
  <div class="frame">
    <div class="kicker">Round {round_data.round_number}</div>
    <h2 class="h-xl">{round_data.topic}</h2>
    <p class="lead">{round_data.question}</p>
  </div>
</div>''')
        
        # 发言页（每2-3人一页）
        speakers = round_data.speakers
        for i in range(0, len(speakers), 2):
            chunk = speakers[i:i+2]
            speaker_html = "\n".join([self.render_speaker(s) for s in chunk])
            slides.append(f'''
<div class="slide" data-title="R{round_data.round_number} 发言">
  <div class="frame">
    <div class="kicker">Round {round_data.round_number} 发言</div>
{speaker_html}
  </div>
</div>''')
        
        # 碰撞页
        if round_data.clashes:
            clash_html = "\n".join([self.render_clash(c) for c in round_data.clashes])
            insight_html = self.render_insight(round_data.insight) if round_data.insight else ""
            slides.append(f'''
<div class="slide" data-title="R{round_data.round_number} 碰撞">
  <div class="frame">
    <div class="kicker">Round {round_data.round_number} 碰撞</div>
    <h3 class="h-md">碰撞交锋</h3>
{clash_html}
{insight_html}
  </div>
</div>''')
        
        return "\n".join(slides)
    
    def render(self, content: Dict[str, Any]) -> str:
        """渲染完整HTML"""
        # 验证内容
        ppt = validate_content(content)
        
        # 渲染所有slides
        slides = []
        
        # 封面
        slides.append(self.render_cover(ppt))
        
        # 各轮次
        for round_data in ppt.rounds:
            slides.append(self.render_round(round_data))
        
        # 开放问题
        if ppt.open_questions:
            questions_html = "\n".join([
                f'<div class="oq" data-anim><div class="oq-num">Q{i+1}</div><div class="oq-text">{q.question}</div></div>'
                for i, q in enumerate(ppt.open_questions)
            ])
            slides.append(f'''
<div class="slide" data-title="开放问题">
  <div class="frame">
    <div class="kicker">留给读者</div>
    <h2 class="h-xl">开放问题</h2>
{questions_html}
  </div>
</div>''')
        
        # 结语
        if ppt.conclusion:
            slides.append(f'''
<div class="slide title-slide" data-title="结语">
  <div class="frame">
    <div class="kicker">结语</div>
    <h2 class="h-xl">{ppt.conclusion}</h2>
  </div>
</div>''')
        
        slides_html = "\n".join(slides)
        
        # 替换模板占位符
        html = self.base_template.replace("{{SLIDES}}", slides_html)
        html = html.replace("{{TITLE}}", ppt.title)
        html = html.replace("{{CSS}}", self.css)
        html = html.replace("{{JS}}", self.js)
        
        return html


def render_from_json(json_path: str, output_path: str, template_dir: str):
    """从JSON文件渲染HTML"""
    # 读取JSON
    with open(json_path, 'r', encoding='utf-8-sig') as f:
        content = json.load(f)
    
    # 渲染
    renderer = RoundtableRenderer(template_dir)
    html = renderer.render(content)
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Rendered: {output_path}")
    print(f"Size: {os.path.getsize(output_path)} bytes")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python render.py <json_path> <output_path> <template_dir>")
        sys.exit(1)
    
    render_from_json(sys.argv[1], sys.argv[2], sys.argv[3])
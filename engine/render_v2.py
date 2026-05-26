# -*- coding: utf-8 -*-
"""圆桌会议HTML渲染引擎 V2 - 使用book-distillation高质量模板"""

import json
import os
import re
from typing import Dict, Any


class RoundtableRendererV2:
    """圆桌会议渲染器 V2 - 使用book-distillation模板"""
    
    def __init__(self, template_dir: str):
        self.template_dir = template_dir
        self.base_template = self._load_template("book-distillation-template.html")
    
    def _load_template(self, filename: str) -> str:
        """加载模板文件"""
        path = os.path.join(self.template_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def render_cover(self, data: Dict) -> str:
        """渲染封面"""
        return f'''
  <div class="slide is-active" data-title="封面">
    <div class="slide-content hero-dark">
      <div class="section-label anim-in">ROUNDTABLE DISCUSSION V3.0</div>
      <h1 class="title-main anim-in anim-delay-1">{data["title"]}</h1>
      <div class="title-sub anim-in anim-delay-2">{data.get("subtitle", "")}</div>
      <div class="gold-line anim-in anim-delay-3"></div>
      <div class="stats-row anim-in anim-delay-4">
        <div class="stat-item"><div class="stat-num">{data["dashboard"]["total_experts"]}</div><div class="stat-label">参与专家</div></div>
        <div class="stat-item"><div class="stat-num">{data["dashboard"]["total_rounds"]}</div><div class="stat-label">讨论轮次</div></div>
        <div class="stat-item"><div class="stat-num">{data["dashboard"]["total_clashes"]}+</div><div class="stat-label">碰撞交锋</div></div>
        <div class="stat-item"><div class="stat-num">{data["dashboard"]["total_insights"]}</div><div class="stat-label">核心洞见</div></div>
      </div>
    </div>
    <div class="deck-footer">{data["title"]} | 圆桌讨论</div>
    <div class="slide-number">01 / {self._count_slides(data)}</div>
  </div>'''
    
    def render_speaker(self, speaker: Dict) -> str:
        """渲染发言块"""
        avatar_color = speaker.get("avatar_color", "#c9a227")
        initial = speaker["name"][0] if speaker["name"] else "?"
        return f'''
      <div class="card card-rise anim-in">
        <div class="speaker-header">
          <div class="speaker-avatar" style="background:{avatar_color}">{initial}</div>
          <div>
            <div class="speaker-name neon-gold">{speaker["name"]}</div>
            <div class="speaker-role">{speaker["role"]}</div>
          </div>
        </div>
        <div class="speaker-content">{speaker["content"]}</div>
      </div>'''
    
    def render_clash(self, clash: Dict) -> str:
        """渲染碰撞块"""
        color_map = {
            "情节反驳": "neon-red",
            "细节挑战": "neon-cyan",
            "逻辑追问": "neon-purple",
            "框架质疑": "neon-orange",
            "反例引入": "neon-green"
        }
        color_class = color_map.get(clash["type"], "neon-gold")
        return f'''
      <div class="card card-clash anim-in">
        <div class="clash-type {color_class}">{clash["type"]}</div>
        <div class="speaker-name">{clash["expert"]}</div>
        <div class="clash-content">{clash["content"]}</div>
      </div>'''
    
    def render_insight(self, insight: Dict) -> str:
        """渲染洞见卡"""
        return f'''
      <div class="card card-insight anim-in">
        <div class="insight-label neon-gold">核心洞见</div>
        <div class="insight-statement">{insight["statement"]}</div>
        <div class="insight-explanation">{insight["explanation"]}</div>
      </div>'''
    
    def render_round(self, round_data: Dict, slide_num: int, total_slides: int) -> str:
        """渲染一个完整轮次"""
        slides = []
        
        # 标题页
        slides.append(f'''
  <div class="slide" data-title="Round {round_data["round_number"]}: {round_data["topic"]}">
    <div class="slide-content">
      <div class="section-label anim-in">ROUND {round_data["round_number"]}</div>
      <h2 class="quote-large anim-in anim-delay-1">{round_data["topic"]}</h2>
      <div class="gold-line anim-in anim-delay-2"></div>
      <p class="anim-in anim-delay-3" style="color:var(--text-dim);font-size:16px;">{round_data["question"]}</p>
    </div>
    <div class="deck-footer">Round {round_data["round_number"]} | {round_data["topic"]}</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
        slide_num += 1
        
        # 发言页
        speakers_html = "\n".join([self.render_speaker(s) for s in round_data["speakers"]])
        slides.append(f'''
  <div class="slide" data-title="R{round_data["round_number"]} 发言">
    <div class="slide-content">
      <div class="section-label anim-in">EXPERT PERSPECTIVES</div>
      <h3 class="anim-in anim-delay-1" style="margin-bottom:24px;">专家发言</h3>
      <div class="grid-2">
{speakers_html}
      </div>
    </div>
    <div class="deck-footer">Round {round_data["round_number"]} | 发言</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
        slide_num += 1
        
        # 碰撞页
        if round_data.get("clashes"):
            clashes_html = "\n".join([self.render_clash(c) for c in round_data["clashes"]])
            slides.append(f'''
  <div class="slide" data-title="R{round_data["round_number"]} 碰撞">
    <div class="slide-content">
      <div class="section-label anim-in">CLASH & DEBATE</div>
      <h3 class="anim-in anim-delay-1" style="margin-bottom:24px;">碰撞交锋</h3>
{clashes_html}
    </div>
    <div class="deck-footer">Round {round_data["round_number"]} | 碰撞</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
            slide_num += 1
        
        # 洞见页
        if round_data.get("insight"):
            insight_html = self.render_insight(round_data["insight"])
            slides.append(f'''
  <div class="slide" data-title="R{round_data["round_number"]} 洞见">
    <div class="slide-content">
      <div class="section-label anim-in">INSIGHT</div>
      <h3 class="anim-in anim-delay-1" style="margin-bottom:24px;">本轮洞见</h3>
{insight_html}
    </div>
    <div class="deck-footer">Round {round_data["round_number"]} | 洞见</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
            slide_num += 1
        
        return "\n".join(slides), slide_num
    
    def _count_slides(self, data: Dict) -> int:
        """计算总slide数"""
        count = 1  # 封面
        for r in data["rounds"]:
            count += 1  # 标题
            count += 1  # 发言
            if r.get("clashes"):
                count += 1  # 碰撞
            if r.get("insight"):
                count += 1  # 洞见
        if data.get("open_questions"):
            count += 1
        if data.get("conclusion"):
            count += 1
        return count
    
    def render(self, content: Dict) -> str:
        """渲染完整HTML"""
        slides = []
        slide_num = 1
        total_slides = self._count_slides(content)
        
        # 封面
        slides.append(self.render_cover(content))
        slide_num += 1
        
        # 各轮次
        for round_data in content["rounds"]:
            round_slides, slide_num = self.render_round(round_data, slide_num, total_slides)
            slides.append(round_slides)
        
        # 开放问题
        if content.get("open_questions"):
            questions_html = "\n".join([
                f'<div class="headline-item anim-in"><strong>Q{i+1}:</strong> {q["question"]}</div>'
                for i, q in enumerate(content["open_questions"])
            ])
            slides.append(f'''
  <div class="slide" data-title="开放问题">
    <div class="slide-content">
      <div class="section-label anim-in">OPEN QUESTIONS</div>
      <h3 class="anim-in anim-delay-1" style="margin-bottom:24px;">留给读者的问题</h3>
{questions_html}
    </div>
    <div class="deck-footer">开放问题</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
            slide_num += 1
        
        # 结语
        if content.get("conclusion"):
            slides.append(f'''
  <div class="slide" data-title="结语">
    <div class="slide-content">
      <div class="section-label anim-in">CONCLUSION</div>
      <div class="quote-large anim-in anim-delay-1">{content["conclusion"]}</div>
    </div>
    <div class="deck-footer">结语</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
        
        slides_html = "\n".join(slides)
        
        # 替换模板中的slides占位符
        # 找到第一个slide的位置，在它之前插入我们的slides
        html = self.base_template
        
        # 删除原有的所有slide
        html = re.sub(r'<div class="slide[^"]*".*?</div>\s*</div>\s*</div>', '', html, flags=re.DOTALL)
        
        # 在deck-container中插入新slides
        html = html.replace('<!-- SLIDES_PLACEHOLDER -->', slides_html)
        
        # 如果没有占位符，在deck-container的开头插入
        if '<!-- SLIDES_PLACEHOLDER -->' not in self.base_template:
            # 找到deck-container的位置
            deck_match = re.search(r'<div class="deck-container"[^>]*>', html)
            if deck_match:
                insert_pos = deck_match.end()
                html = html[:insert_pos] + '\n' + slides_html + '\n' + html[insert_pos:]
        
        return html


def render_from_json(json_path: str, output_path: str, template_dir: str):
    """从JSON文件渲染HTML"""
    with open(json_path, 'r', encoding='utf-8-sig') as f:
        content = json.load(f)
    
    renderer = RoundtableRendererV2(template_dir)
    html = renderer.render(content)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Rendered: {output_path}")
    print(f"Size: {os.path.getsize(output_path)} bytes")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python render_v2.py <json_path> <output_path> <template_dir>")
        sys.exit(1)
    
    render_from_json(sys.argv[1], sys.argv[2], sys.argv[3])
# -*- coding: utf-8 -*-
"""圆桌会议V8级渲染引擎 - 从知识讨论到生存博弈"""

import json
import os
import re
from typing import Dict, Any, List


class RoundtableRendererV8:
    """V8级渲染器 - 支持深度内容结构"""
    
    def __init__(self, template_dir: str):
        self.template_dir = template_dir
        self.base_template = self._load_template("book-distillation-clean.html")
    
    def _load_template(self, filename: str) -> str:
        path = os.path.join(self.template_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def render_expert_card(self, expert: Dict) -> str:
        """渲染专家档案卡"""
        return f'''
      <div class="card card-rise anim-in">
        <div class="speaker-header">
          <div class="speaker-avatar" style="background:{expert['avatar_color']}">{expert['name'][0]}</div>
          <div>
            <div class="speaker-name neon-gold">{expert['name']}</div>
            <div class="speaker-role">{expert['title']}</div>
          </div>
        </div>
        <div class="expert-profile">
          <div class="profile-item"><span class="profile-label">核心信念：</span>{expert['core_belief']}</div>
          <div class="profile-item"><span class="profile-label">利益相关：</span>{expert['interest']}</div>
          <div class="profile-item"><span class="profile-label">恐惧：</span>{expert['fear']}</div>
          <div class="profile-item"><span class="profile-label">偏见：</span>{expert['bias']}</div>
        </div>
      </div>'''
    
    def render_stance(self, stance: Dict) -> str:
        """渲染立场表达"""
        emotion_class = self._get_emotion_class(stance.get('emotion', 'serious'))
        return f'''
      <div class="stance-item anim-in">
        <div class="stance-expert neon-gold">{stance['expert']}</div>
        <div class="stance-content {emotion_class}">{stance['stance']}</div>
      </div>'''
    
    def render_clash(self, clash: Dict) -> str:
        """渲染碰撞轮次"""
        attack_type_class = self._get_attack_type_class(clash['attack_type'])
        emotion_class = self._get_emotion_class(clash.get('emotion', 'serious'))
        
        counter_html = ""
        if clash.get('counter_attack'):
            counter_emotion_class = self._get_emotion_class(clash.get('counter_emotion', 'serious'))
            counter_html = f'''
          <div class="counter-attack">
            <div class="counter-label neon-cyan">反击</div>
            <div class="counter-content {counter_emotion_class}">{clash['counter_attack']}</div>
          </div>'''
        
        return f'''
      <div class="clash-round anim-in">
        <div class="clash-header">
          <span class="clash-attacker neon-red">{clash['attacker']}</span>
          <span class="clash-arrow">→</span>
          <span class="clash-target neon-cyan">{clash['target']}</span>
        </div>
        <div class="clash-type {attack_type_class}">{clash['attack_type']}</div>
        <div class="clash-content {emotion_class}">{clash['attack_content']}</div>
        {counter_html}
      </div>'''
    
    def render_reality_case(self, case: Dict) -> str:
        """渲染现实案例"""
        return f'''
      <div class="reality-case anim-in">
        <div class="case-header">
          <div class="case-name neon-orange">{case['case_name']}</div>
          <div class="case-source">{case['case_source']}</div>
        </div>
        <div class="case-content">{case['case_content']}</div>
        <div class="case-outcome neon-red">代价：{case['case_outcome']}</div>
        <div class="case-lesson neon-gold">教训：{case['case_lesson']}</div>
      </div>'''
    
    def render_cost_discussion(self, cost: Dict) -> str:
        """渲染代价讨论"""
        costs_html = ""
        for c in cost['cost_analysis']:
            costs_html += f'''
          <div class="cost-item">
            <div class="cost-name neon-red">{c['cost']}</div>
            <div class="cost-analysis">{c['analysis']}</div>
          </div>'''
        
        survivor_html = ""
        if cost.get('survivor_bias'):
            survivor_html = f'''
          <div class="survivor-bias">
            <div class="survivor-label neon-purple">幸存者偏差</div>
            <div class="survivor-content">{cost['survivor_bias']}</div>
          </div>'''
        
        return f'''
      <div class="cost-discussion anim-in">
        <div class="cost-scenario neon-gold">{cost['scenario']}</div>
        <div class="cost-list">
          {costs_html}
        </div>
        <div class="worst-case">
          <div class="worst-label neon-red">最坏情况</div>
          <div class="worst-content">{cost['worst_case']}</div>
        </div>
        {survivor_html}
      </div>'''
    
    def render_human_nature(self, human: Dict) -> str:
        """渲染人性层"""
        examples_html = ""
        for ex in human['real_examples']:
            examples_html += f'''
          <div class="example-item">• {ex}</div>'''
        
        return f'''
      <div class="human-nature anim-in">
        <div class="human-question neon-purple">{human['question']}</div>
        <div class="human-analysis">{human['psychological_analysis']}</div>
        <div class="human-examples">
          <div class="examples-label">现实例子</div>
          {examples_html}
        </div>
        <div class="human-conclusion neon-gold">{human['conclusion']}</div>
      </div>'''
    
    def render_cognitive_upgrade(self, upgrade: Dict) -> str:
        """渲染认知升级"""
        return f'''
      <div class="cognitive-upgrade anim-in">
        <div class="upgrade-comparison">
          <div class="old-thinking">
            <div class="thinking-label neon-red">旧思维</div>
            <div class="thinking-content">{upgrade['old_thinking']}</div>
          </div>
          <div class="upgrade-arrow">→</div>
          <div class="new-thinking">
            <div class="thinking-label neon-green">新思维</div>
            <div class="thinking-content">{upgrade['new_thinking']}</div>
          </div>
        </div>
        <div class="complexity">
          <div class="complexity-label neon-cyan">复杂性</div>
          <div class="complexity-content">{upgrade['complexity']}</div>
        </div>
        <div class="actionable">
          <div class="actionable-label neon-gold">可执行洞见</div>
          <div class="actionable-content">{upgrade['actionable_insight']}</div>
        </div>
      </div>'''
    
    def _get_emotion_class(self, emotion: str) -> str:
        """获取情绪CSS类"""
        emotion_map = {
            "sarcasm": "emotion-sarcasm",
            "helplessness": "emotion-helplessness",
            "anger": "emotion-anger",
            "hesitation": "emotion-hesitation",
            "self_deprecation": "emotion-self-deprecation",
            "cold_laugh": "emotion-cold-laugh",
            "silence": "emotion-silence",
            "serious": "emotion-serious"
        }
        return emotion_map.get(emotion, "emotion-serious")
    
    def _get_attack_type_class(self, attack_type: str) -> str:
        """获取攻击类型CSS类"""
        type_map = {
            "逻辑漏洞": "attack-logic",
            "利益冲突": "attack-interest",
            "现实矛盾": "attack-reality",
            "人性弱点": "attack-human",
            "失败案例": "attack-failure"
        }
        return type_map.get(attack_type, "attack-logic")
    
    def render_round(self, round_data: Dict, slide_num: int, total_slides: int) -> tuple:
        """渲染一个完整轮次（V8级结构）"""
        slides = []
        
        # 标题页
        slides.append(f'''
  <div class="slide" data-title="Round {round_data['round_number']}: {round_data['topic']}">
    <div class="slide-content">
      <div class="section-label anim-in">ROUND {round_data['round_number']}</div>
      <h2 class="quote-large anim-in anim-delay-1">{round_data['topic']}</h2>
      <div class="gold-line anim-in anim-delay-2"></div>
      <p class="anim-in anim-delay-3" style="color:var(--text-dim);font-size:16px;">{round_data['core_question']}</p>
    </div>
    <div class="deck-footer">Round {round_data['round_number']} | {round_data['topic']}</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
        slide_num += 1
        
        # Round1: 立场表达
        stances_html = "\n".join([self.render_stance(s) for s in round_data['stances']])
        slides.append(f'''
  <div class="slide" data-title="R{round_data['round_number']} 立场">
    <div class="slide-content">
      <div class="section-label anim-in">ROUND 1: STANCES</div>
      <h3 class="anim-in anim-delay-1" style="margin-bottom:24px;">立场表达</h3>
      <div class="stances-grid">
        {stances_html}
      </div>
    </div>
    <div class="deck-footer">Round {round_data['round_number']} | 立场</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
        slide_num += 1
        
        # Round2: 互相反驳
        clashes_html = "\n".join([self.render_clash(c) for c in round_data['clash_rounds']])
        slides.append(f'''
  <div class="slide" data-title="R{round_data['round_number']} 碰撞">
    <div class="slide-content">
      <div class="section-label anim-in">ROUND 2: CLASH</div>
      <h3 class="anim-in anim-delay-1" style="margin-bottom:24px;">互相反驳</h3>
      <div class="clash-container">
        {clashes_html}
      </div>
    </div>
    <div class="deck-footer">Round {round_data['round_number']} | 碰撞</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
        slide_num += 1
        
        # Round3: 现实案例
        cases_html = "\n".join([self.render_reality_case(c) for c in round_data['reality_cases']])
        slides.append(f'''
  <div class="slide" data-title="R{round_data['round_number']} 案例">
    <div class="slide-content">
      <div class="section-label anim-in">ROUND 3: REALITY</div>
      <h3 class="anim-in anim-delay-1" style="margin-bottom:24px;">现实案例</h3>
      <div class="cases-container">
        {cases_html}
      </div>
    </div>
    <div class="deck-footer">Round {round_data['round_number']} | 案例</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
        slide_num += 1
        
        # Round4: 代价讨论
        cost_html = self.render_cost_discussion(round_data['cost_discussion'])
        slides.append(f'''
  <div class="slide" data-title="R{round_data['round_number']} 代价">
    <div class="slide-content">
      <div class="section-label anim-in">ROUND 4: COST</div>
      <h3 class="anim-in anim-delay-1" style="margin-bottom:24px;">代价讨论</h3>
      {cost_html}
    </div>
    <div class="deck-footer">Round {round_data['round_number']} | 代价</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
        slide_num += 1
        
        # Round5: 人性层
        human_html = self.render_human_nature(round_data['human_nature'])
        slides.append(f'''
  <div class="slide" data-title="R{round_data['round_number']} 人性">
    <div class="slide-content">
      <div class="section-label anim-in">ROUND 5: HUMAN NATURE</div>
      <h3 class="anim-in anim-delay-1" style="margin-bottom:24px;">人性层</h3>
      {human_html}
    </div>
    <div class="deck-footer">Round {round_data['round_number']} | 人性</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
        slide_num += 1
        
        # Round6: 认知升级
        upgrade_html = self.render_cognitive_upgrade(round_data['cognitive_upgrade'])
        slides.append(f'''
  <div class="slide" data-title="R{round_data['round_number']} 升级">
    <div class="slide-content">
      <div class="section-label anim-in">ROUND 6: COGNITIVE UPGRADE</div>
      <h3 class="anim-in anim-delay-1" style="margin-bottom:24px;">认知升级</h3>
      {upgrade_html}
    </div>
    <div class="deck-footer">Round {round_data['round_number']} | 升级</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
        slide_num += 1
        
        return "\n".join(slides), slide_num
    
    def _count_slides(self, data: Dict) -> int:
        """计算总slide数"""
        count = 1  # 封面
        count += 1  # 专家档案
        for r in data['rounds']:
            count += 7  # 标题 + 立场 + 碰撞 + 案例 + 代价 + 人性 + 升级
        count += 1  # 最终洞见
        count += 1  # 开放问题
        return count
    
    def render(self, content: Dict) -> str:
        """渲染完整HTML"""
        slides = []
        slide_num = 1
        total_slides = self._count_slides(content)
        
        # 封面
        slides.append(f'''
  <div class="slide is-active" data-title="封面">
    <div class="slide-content hero-dark">
      <div class="section-label anim-in">ROUNDTABLE DISCUSSION V8.0</div>
      <h1 class="title-main anim-in anim-delay-1">{content['title']}</h1>
      <div class="title-sub anim-in anim-delay-2">{content.get('subtitle', '')}</div>
      <div class="gold-line anim-in anim-delay-3"></div>
      <p style="font-size:14px;color:var(--text-dim);letter-spacing:0.1em;" class="anim-in anim-delay-4">从知识讨论到生存博弈</p>
    </div>
    <div class="deck-footer">{content['title']} | V8级圆桌讨论</div>
    <div class="slide-number">01 / {total_slides}</div>
  </div>''')
        slide_num += 1
        
        # 专家档案
        experts_html = "\n".join([self.render_expert_card(e) for e in content['experts']])
        slides.append(f'''
  <div class="slide" data-title="专家档案">
    <div class="slide-content">
      <div class="section-label anim-in">EXPERT PROFILES</div>
      <h3 class="anim-in anim-delay-1" style="margin-bottom:24px;">专家档案</h3>
      <div class="grid-2">
        {experts_html}
      </div>
    </div>
    <div class="deck-footer">专家档案</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
        slide_num += 1
        
        # 各轮次
        for round_data in content['rounds']:
            round_slides, slide_num = self.render_round(round_data, slide_num, total_slides)
            slides.append(round_slides)
        
        # 最终洞见
        slides.append(f'''
  <div class="slide" data-title="最终洞见">
    <div class="slide-content">
      <div class="section-label anim-in">FINAL INSIGHT</div>
      <div class="quote-large anim-in anim-delay-1">{content['final_insight']}</div>
    </div>
    <div class="deck-footer">最终洞见</div>
    <div class="slide-number">{str(slide_num).zfill(2)} / {total_slides}</div>
  </div>''')
        slide_num += 1
        
        # 开放问题
        questions_html = "\n".join([
            f'<div class="headline-item anim-in"><strong>Q{i+1}:</strong> {q}</div>'
            for i, q in enumerate(content['open_questions'])
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
        
        slides_html = "\n".join(slides)
        
        # 替换模板
        html = self.base_template
        
        # 删除模板中所有的slide（保留deck-container结构）
        # 找到deck-container的开始位置
        deck_match = re.search(r'<div class="deck-container"[^>]*>', html)
        if deck_match:
            deck_start = deck_match.end()
            
            # 找到第一个footer的位置（slide内容结束的标志）
            footer_match = re.search(r'<div class="deck-footer"', html[deck_start:])
            if footer_match:
                # 删除从deck_start到第一个footer之间的所有内容（即所有slide）
                delete_end = deck_start + footer_match.start()
                html = html[:deck_start] + '\n' + slides_html + '\n' + html[delete_end:]
            else:
                # 如果找不到footer，直接在deck_start后插入
                html = html[:deck_start] + '\n' + slides_html + '\n' + html[deck_start:]
        
        return html


def render_from_json(json_path: str, output_path: str, template_dir: str):
    """从JSON文件渲染HTML"""
    with open(json_path, 'r', encoding='utf-8-sig') as f:
        content = json.load(f)
    
    renderer = RoundtableRendererV8(template_dir)
    html = renderer.render(content)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Rendered: {output_path}")
    print(f"Size: {os.path.getsize(output_path)} bytes")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python render_v8.py <json_path> <output_path> <template_dir>")
        sys.exit(1)
    
    render_from_json(sys.argv[1], sys.argv[2], sys.argv[3])
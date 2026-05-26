import json
import os
import re

with open('content/算法信用_人性异化_讨论.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

with open('assets/roundtable-template.html', 'r', encoding='utf-8') as f:
    template = f.read()

colors = {'luo-xian': '#1a237e', 'xiang-biao': '#0d47a1', 'nassim-taleb': '#b71c1c', 'wu-jun': '#1b5e20', 'feng-tang': '#e65100', 'dou-wen-tao': '#4a148c'}
expert_map = {e['id']: e for e in data['experts']}

slides = []
slides.append('''<section class="slide hero active" data-title="封面">
  <div class="slide-content hero-dark">
    <div class="section-label anim-in">ROUNDTABLE DISCUSSION</div>
    <h1 class="title-main anim-in anim-delay-1">''' + data['title'] + '''</h1>
    <div class="title-sub anim-in anim-delay-2">''' + data['subtitle'] + '''</div>
    <div class="gold-line anim-in anim-delay-3"></div>
    <p class="anim-in anim-delay-4">6位专家 · 3轮碰撞 · 深度洞见</p>
  </div>
  <div class="deck-footer">''' + data['title'] + '''</div>
  <div class="slide-number">01</div>
</section>''')

experts_html = []
for e in data['experts']:
    color = colors.get(e['id'], '#333333')
    experts_html.append('''<div class="card card-rise anim-in">
      <div class="speaker-header">
        <div class="speaker-avatar" style="background:''' + color + '''">''' + e['avatar'] + '''</div>
        <div><div class="speaker-name neon-gold">''' + e['name'] + '''</div>
        <div class="speaker-role">''' + e['title'] + '''</div></div>
      </div>
    </div>''')
slides.append('''<section class="slide" data-title="专家档案">
  <div class="slide-content">
    <div class="section-label anim-in">EXPERT PROFILES</div>
    <h3 class="anim-in anim-delay-1">六位专家</h3>
    <div class="grid-2">''' + ''.join(experts_html) + '''</div>
  </div>
  <div class="deck-footer">专家档案</div>
  <div class="slide-number">02</div>
</section>''')

for r_idx, r in enumerate(data['rounds']):
    slides.append('''<section class="slide" data-title="Round ''' + str(r['round']) + '''">
  <div class="slide-content">
    <div class="section-label anim-in">ROUND ''' + str(r['round']) + '''</div>
    <h2 class="quote-large anim-in anim-delay-1">''' + r['title'] + '''</h2>
    <div class="gold-line anim-in anim-delay-2"></div>
    <p class="anim-in anim-delay-3" style="color:#888;font-size:16px;">''' + r['description'] + '''</p>
  </div>
  <div class="deck-footer">Round ''' + str(r['round']) + ''' | ''' + r['title'] + '''</div>
  <div class="slide-number">''' + str(3 + r_idx * 5).zfill(2) + '''</div>
</section>''')
    
    for d in r['discussions']:
        expert = expert_map[d['expertId']]
        color = colors.get(d['expertId'], '#333333')
        content_html = d['content'].replace('\\n', '<br>')
        slides.append('''<section class="slide" data-title="''' + expert['name'] + '''发言">
  <div class="slide-content">
    <div class="speaker-header anim-in" style="margin-bottom:32px;">
      <div class="speaker-avatar" style="background:''' + color + ''';width:64px;height:64px;font-size:28px;">''' + expert['avatar'] + '''</div>
      <div><div class="speaker-name neon-gold" style="font-size:24px;">''' + expert['name'] + '''</div>
      <div class="speaker-role">''' + expert['title'] + '''</div></div>
    </div>
    <div class="stance-content emotion-serious" style="font-size:18px;line-height:1.8;">''' + content_html + '''</div>
  </div>
  <div class="deck-footer">Round ''' + str(r['round']) + ''' | ''' + expert['name'] + '''</div>
  <div class="slide-number">''' + str(4 + r_idx * 5).zfill(2) + '''</div>
</section>''')
    
    if r.get('collision'):
        clashes_html = []
        for c in r['collision']['discussions']:
            speaker = expert_map[c['speakerId']]
            target = expert_map[c['targetId']]
            sc = colors.get(c['speakerId'], '#333333')
            tc = colors.get(c['targetId'], '#333333')
            content_html = c['content'].replace('\\n', '<br>')
            clashes_html.append('''<div class="clash-round anim-in">
          <div class="clash-header">
            <span class="clash-attacker" style="color:''' + sc + '''">''' + speaker['name'] + '''</span>
            <span class="clash-arrow">→</span>
            <span class="clash-target" style="color:''' + tc + '''">''' + target['name'] + '''</span>
          </div>
          <div class="clash-type attack-logic">观点碰撞</div>
          <div class="clash-content emotion-serious">''' + content_html + '''</div>
        </div>''')
        slides.append('''<section class="slide" data-title="碰撞">
  <div class="slide-content">
    <div class="section-label anim-in">COLLISION</div>
    <h3 class="anim-in anim-delay-1">''' + r['collision']['title'] + '''</h3>
    <div class="clash-container">''' + ''.join(clashes_html) + '''</div>
  </div>
  <div class="deck-footer">Round ''' + str(r['round']) + ''' | 碰撞</div>
  <div class="slide-number">''' + str(5 + r_idx * 5).zfill(2) + '''</div>
</section>''')

insights_html = []
for i, ins in enumerate(data.get('insights', [])):
    insights_html.append('''<div class="card anim-in" style="margin-bottom:16px;">
      <div class="speaker-header">
        <div class="speaker-avatar" style="background:#ffd700;font-size:14px;">''' + str(i+1) + '''</div>
        <div><div class="speaker-name neon-gold">''' + ins['title'] + '''</div></div>
      </div>
      <p style="color:#888;font-size:16px;line-height:1.6;margin-top:12px;">''' + ins['content'] + '''</p>
    </div>''')
slides.append('''<section class="slide" data-title="洞见">
  <div class="slide-content">
    <div class="section-label anim-in">FINAL INSIGHTS</div>
    <h3 class="anim-in anim-delay-1">五大洞见</h3>
    <div>''' + ''.join(insights_html) + '''</div>
  </div>
  <div class="deck-footer">洞见总结</div>
  <div class="slide-number">18</div>
</section>''')

slides_html = ''.join(slides)
html = template.replace('<!-- SLIDES_HERE -->', slides_html)
html = re.sub(r'<title>[^<]*</title>', '<title>' + data['title'] + ' 圆桌洞见</title>', html, count=1)

output_path = 'output/算法信用_人性异化_圆桌洞见.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print('Rendered:', output_path)
print('Size:', os.path.getsize(output_path), 'bytes')

const fs = require('fs');
const path = require('path');

const jsonPath = path.join(__dirname, '..', 'content', '科幻叙事_投资泡沫_讨论.json');
const outputPath = path.join(__dirname, '..', 'output', '科幻叙事_投资泡沫_圆桌洞见.html');

const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;')
             .replace(/</g, '&lt;')
             .replace(/>/g, '&gt;')
             .replace(/"/g, '&quot;');
}

function getExpertById(id) {
  return data.metadata.participants.find(p => p.id === id) || {};
}

function generateSpeakerCard(speaker, type, title, content) {
  const expert = getExpertById(speaker);
  const avatar = expert.avatar || '💬';
  const name = expert.name || speaker;
  const expertTitle = expert.title || '';
  const color = expert.color || 'var(--accent)';

  const typeLabel = type === 'opening' ? '立场陈述' : type === 'analysis' ? '深度分析' : type === 'synthesis' ? '整合共识' : '发言';

  const contentHtml = content
    .split('\n\n')
    .filter(p => p.trim())
    .map(p => `<p style="margin-bottom:1.5vh;line-height:1.95">${escapeHtml(p)}</p>`)
    .join('');

  return `<div class="sp" style="border-left-color:${color}">
    <div class="sh">
      <div class="speaker-avatar" style="background:${color}">${avatar}</div>
      <div>
        <div class="sn">${escapeHtml(name)}</div>
        <div class="sr">${escapeHtml(expertTitle)} · ${typeLabel}</div>
      </div>
    </div>
    ${title ? `<div style="font-size:.9rem;font-weight:600;color:var(--gold);margin-bottom:1.5vh;padding-bottom:1vh;border-bottom:1px solid rgba(var(--paper-rgb),.08)">▸ ${escapeHtml(title)}</div>` : ''}
    <div class="st">${contentHtml}</div>
  </div>`;
}

function generateCollision(collision) {
  if (!collision) return '';

  const contentHtml = collision.content
    .split('\n\n')
    .filter(p => p.trim())
    .map(p => `<p style="margin-bottom:1.5vh;line-height:1.9">${escapeHtml(p)}</p>`)
    .join('');

  return `<div style="background:rgba(var(--accent-rgb),.06);border:1px solid rgba(var(--accent-rgb),.15);border-radius:var(--radius);padding:3vh 2.5vw;margin-top:3vh">
    <div style="font-family:var(--mono);font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);margin-bottom:2vh;font-weight:700">⚡ 专家交锋</div>
    <div style="font-family:var(--serif-zh);font-size:1.05rem;font-weight:600;margin-bottom:2vh;line-height:1.6">${escapeHtml(collision.title)}</div>
    <div class="st">${contentHtml}</div>
  </div>`;
}

function generateInsightsPage() {
  let insightsHtml = '';
  data.keyInsights.forEach((insight, i) => {
    insightsHtml += `<div class="insight-c" data-anim>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:2vh">
        <span style="font-family:var(--mono);font-size:1.5rem;font-weight:900;color:var(--accent);opacity:.5">0${i+1}</span>
      </div>
      <div class="insight-q">${escapeHtml(insight.title)}</div>
      <div class="insight-a">${escapeHtml(insight.content)}</div>
      <div style="margin-top:2vh;padding-top:1.5vh;border-top:1px solid rgba(var(--paper-rgb),.08)">
        <div style="font-family:var(--mono);font-size:10px;color:rgba(var(--paper-rgb),.4);margin-bottom:1vh">💬 核心引言</div>
        <div style="font-family:var(--serif-zh);font-size:.95rem;font-style:italic;color:var(--gold);line-height:1.7">"${escapeHtml(insight.quote)}"</div>
      </div>
    </div>`;
  });
  return `<div class="grid-2">${insightsHtml}</div>`;
}

function generateExpertsOverview() {
  let expertsHtml = '';
  data.metadata.participants.forEach((p, i) => {
    expertsHtml += `<div class="card-rise" style="border-left-color:${p.color}" data-anim>
      <div class="speaker-header">
        <div class="speaker-avatar" style="background:${p.color}">${p.avatar}</div>
        <div>
          <div class="speaker-name">${escapeHtml(p.name)}</div>
          <div class="speaker-role">${escapeHtml(p.title)}</div>
        </div>
      </div>
    </div>`;
  });
  return expertsHtml;
}

function generateSourceMaterials() {
  let html = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:3vh">';
  data.metadata.sourceMaterials.forEach(m => {
    html += `<span class="tag tag-blue">${escapeHtml(m)}</span>`;
  });
  html += '</div>';
  return html;
}

let slidesHtml = '';

// Slide 0: Cover
slidesHtml += `<div class="slide hero title-slide" data-title="${escapeHtml(data.metadata.title)}">
  <div class="frame">
    <div class="slide-content" style="justify-content:center;align-items:center;text-align:center">
      <div class="cover-badge" data-anim>圆桌洞见</div>
      <div class="cover-title" data-anim>${escapeHtml(data.metadata.title)}</div>
      <div class="cover-sub" data-anim>${escapeHtml(data.metadata.subtitle)}</div>
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
          <div class="cover-stat-num">18</div>
          <div class="cover-stat-label">发言</div>
        </div>
        <div class="cover-stat">
          <div class="cover-stat-num">${data.keyInsights.length}</div>
          <div class="cover-stat-label">洞见</div>
        </div>
      </div>
      <div class="meta-row" data-anim>
        ${data.metadata.participants.map(p => `<span>${p.avatar} ${escapeHtml(p.name)}</span>`).join(' · ')}
      </div>
      <div style="margin-top:2vh;font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;opacity:.4" data-anim>
        ${escapeHtml(data.metadata.date)} · ${escapeHtml(data.metadata.duration)}
      </div>
    </div>
  </div>
</div>`;

// Slide 1: Key Insights Overview
slidesHtml += `<div class="slide" data-title="核心洞见">
  <div class="frame">
    <div class="kicker" data-anim>KEY INSIGHTS</div>
    <div class="h-xl" data-anim style="margin-bottom:4vh">核心洞见</div>
    ${generateInsightsPage()}
    <div class="deck-footer">${data.keyInsights.length}个颠覆认知的观点</div>
  </div>
</div>`;

// Slide 2: Experts Overview
slidesHtml += `<div class="slide" data-title="专家阵容">
  <div class="frame">
    <div class="kicker" data-anim>EXPERT PANEL</div>
    <div class="h-xl" data-anim style="margin-bottom:4vh">专家阵容</div>
    <div class="grid-2">${generateExpertsOverview()}</div>
    <div class="deck-footer">6位跨界专家，3轮深度交锋</div>
  </div>
</div>`;

// Slide 3: Source Materials
slidesHtml += `<div class="slide" data-title="参考资料">
  <div class="frame">
    <div class="kicker" data-anim>REFERENCE MATERIALS</div>
    <div class="h-xl" data-anim style="margin-bottom:4vh">参考资料</div>
    <div class="card" data-anim>
      <div class="card-title">核心素材</div>
      <div class="card-body">
        <p style="margin-bottom:2vh">本场圆桌洞见基于以下科幻作品与商业理论著作：</p>
        ${generateSourceMaterials()}
        <p style="font-size:.88rem;color:rgba(var(--paper-rgb),.6);margin-top:2vh">注：讨论内容为专家基于公开资料的观点延伸，不代表对原著的学术解读。</p>
      </div>
    </div>
    <div class="deck-footer">资料来源：WebSearch + 专家档案整合</div>
  </div>
</div>`;

// Discussion Rounds
data.rounds.forEach((round, roundIdx) => {
  const roundNum = roundIdx + 1;

  // Round Title Slide
  slidesHtml += `<div class="slide title-slide" data-title="第${roundNum}轮：${escapeHtml(round.title)}">
    <div class="frame">
      <div class="hero-dark">
        <div class="kicker" data-anim>ROUND ${roundNum}</div>
        <div class="h-hero" data-anim style="background:linear-gradient(135deg,var(--paper) 0%,var(--gold) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">${escapeHtml(round.title)}</div>
        <div class="quote-large" data-anim style="max-width:700px;margin-top:3vh;font-size:1.1rem">${escapeHtml(round.subtitle)}</div>
      </div>
    </div>
  </div>`;

  // Discussion Content - First Half
  let discussionsHtml1 = '';
  round.discussions.slice(0, 3).forEach(d => {
    discussionsHtml1 += generateSpeakerCard(d.speaker, d.type, d.title, d.content);
  });

  slidesHtml += `<div class="slide" data-title="第${roundNum}轮：上半场">
    <div class="frame">
      <div class="kicker" data-anim>ROUND ${roundNum} · 上半场</div>
      <div class="h-lg" data-anim style="margin-bottom:3vh">${escapeHtml(round.title)} · 立场与依据</div>
      ${discussionsHtml1}
      <div class="deck-footer">第 ${roundNum}/3 轮 · ${round.discussions.length} 位专家发言</div>
    </div>
  </div>`;

  // Discussion Content - Second Half
  let discussionsHtml2 = '';
  round.discussions.slice(3).forEach(d => {
    discussionsHtml2 += generateSpeakerCard(d.speaker, d.type, d.title, d.content);
  });

  slidesHtml += `<div class="slide" data-title="第${roundNum}轮：下半场">
    <div class="frame">
      <div class="kicker" data-anim>ROUND ${roundNum} · 下半场</div>
      <div class="h-lg" data-anim style="margin-bottom:3vh">${escapeHtml(round.title)} · 多元视角</div>
      ${discussionsHtml2}
      <div class="deck-footer">第 ${roundNum}/3 轮 · ${round.discussions.length} 位专家发言</div>
    </div>
  </div>`;

  // Collision Slide
  if (round.collision) {
    slidesHtml += `<div class="slide" data-title="第${roundNum}轮：交锋">
      <div class="frame">
        <div class="kicker" data-anim>ROUND ${roundNum} · 观点碰撞</div>
        <div class="h-lg" data-anim style="margin-bottom:3vh">${escapeHtml(round.title)} · 专家交锋</div>
        ${generateCollision(round.collision)}
        <div class="deck-footer">第 ${roundNum}/3 轮 · 直接反驳与回应</div>
      </div>
    </div>`;
  }
});

// Final Slide
slidesHtml += `<div class="slide hero title-slide" data-title="结语">
  <div class="frame">
    <div class="slide-content" style="justify-content:center;align-items:center;text-align:center">
      <div class="kicker" data-anim>CONCLUSION</div>
      <div class="h-hero" data-anim style="margin-bottom:4vh">叙事经济学的边界</div>
      <div class="quote-large" data-anim style="max-width:800px;margin-bottom:4vh">
        "${escapeHtml(data.finalQuote.text)}"
      </div>
      <div style="font-family:var(--mono);font-size:.9rem;color:rgba(var(--paper-rgb),.6);margin-bottom:4vh">—— ${escapeHtml(data.finalQuote.speaker)}</div>
      <div class="gold-line" data-anim></div>
      <div class="meta-row" data-anim>
        ${data.metadata.participants.map(p => `<span>${p.avatar} ${escapeHtml(p.name)}</span>`).join(' · ')}
      </div>
      <div style="margin-top:4vh;font-family:var(--mono);font-size:11px;letter-spacing:.15em;text-transform:uppercase;opacity:.4" data-anim>
        圆桌洞见 · ${escapeHtml(data.metadata.date)}
      </div>
    </div>
  </div>
</div>`;

// Read template and inject slides
const templatePath = path.join(__dirname, '..', 'assets', 'roundtable-template.html');
let template = fs.readFileSync(templatePath, 'utf-8');

template = template.replace('__BOOK_TITLE__', data.metadata.title);
template = template.replace('<!-- SLIDES_HERE -->', slidesHtml);

fs.writeFileSync(outputPath, template, 'utf-8');
console.log(`HTML generated: ${outputPath}`);

const fs = require('fs');
const path = require('path');

const jsonPath = path.join(__dirname, '..', 'content', '影视模因_散户狂潮_讨论.json');
const outputPath = path.join(__dirname, '..', 'output', '影视模因_散户狂潮_圆桌洞见.html');

const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;')
             .replace(/</g, '&lt;')
             .replace(/>/g, '&gt;')
             .replace(/"/g, '&quot;')
             .replace(/'/g, '&#039;');
}

function getExpertById(id) {
  return data.experts.find(e => e.id === id) || {};
}

function generateSpeakerCard(expertId, stance, content, quotes = [], citations = []) {
  const expert = getExpertById(expertId);
  const avatar = expert.avatar || '💬';
  const name = expert.name || expertId;
  const title = expert.title || '';
  const color = expert.color || 'var(--accent)';

  let quotesHtml = '';
  if (quotes && quotes.length > 0) {
    quotesHtml = `<div style="margin-top:1.5vh;display:flex;flex-direction:column;gap:.5vh">`;
    quotes.forEach(q => {
      quotesHtml += `<div style="font-family:var(--serif-zh);font-size:.88rem;font-style:italic;color:var(--gold);padding-left:1vw;border-left:2px solid rgba(var(--gold-rgb),.4);margin-bottom:.5vh">"${escapeHtml(q)}"</div>`;
    });
    quotesHtml += `</div>`;
  }

  let citationsHtml = '';
  if (citations && citations.length > 0) {
    citationsHtml = `<div style="margin-top:1.5vh;font-family:var(--mono);font-size:10px;color:rgba(var(--paper-rgb),.35);letter-spacing:.05em">📌 ${citations.map(c => escapeHtml(c)).join(' · ')}</div>`;
  }

  return `<div class="sp" style="border-left-color:${color}">
    <div class="sh">
      <div class="speaker-avatar" style="background:${color}">${avatar}</div>
      <div>
        <div class="sn">${escapeHtml(name)}</div>
        <div class="sr">${escapeHtml(title)}</div>
      </div>
    </div>
    ${stance ? `<div style="font-size:.9rem;font-weight:600;color:var(--gold);margin-bottom:1.5vh;padding-bottom:1vh;border-bottom:1px solid rgba(var(--paper-rgb),.08)">▸ ${escapeHtml(stance)}</div>` : ''}
    <div class="st">${content.split('\n').map(p => `<p style="margin-bottom:1.2vh;line-height:1.9">${escapeHtml(p)}</p>`).join('')}</div>
    ${quotesHtml}
    ${citationsHtml}
  </div>`;
}

function generateCollision(collision) {
  if (!collision) return '';

  const parts = collision.content.split('\n').filter(p => p.trim());

  return `<div style="background:rgba(var(--accent-rgb),.06);border:1px solid rgba(var(--accent-rgb),.15);border-radius:var(--radius);padding:3vh 2.5vw;margin-top:2vh">
    <div style="font-family:var(--mono);font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);margin-bottom:2vh;font-weight:700">⚡ 专家交锋</div>
    <div style="font-family:var(--serif-zh);font-size:1.05rem;font-weight:600;margin-bottom:2vh;line-height:1.6">${escapeHtml(collision.title)}</div>
    <div class="st">${parts.map(p => `<p style="margin-bottom:1.2vh;line-height:1.9">${escapeHtml(p)}</p>`).join('')}</div>
  </div>`;
}

function generateInsightsPage() {
  let insightsHtml = '<div class="grid-2">';
  data.key_insights.forEach((insight, i) => {
    insightsHtml += `<div class="insight-c" style="animation-delay:${i * 0.1}s">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:2vh">
        <span style="font-family:var(--mono);font-size:1.5rem;font-weight:900;color:var(--accent);opacity:.5">0${i+1}</span>
        <span style="font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--gold);padding:3px 8px;background:rgba(var(--gold-rgb),.1);border-radius:3px">${escapeHtml(insight.expert)}</span>
      </div>
      <div class="insight-q">${escapeHtml(insight.title)}</div>
      <div class="insight-a">${escapeHtml(insight.summary)}</div>
    </div>`;
  });
  insightsHtml += '</div>';
  return insightsHtml;
}

function generateDiscussionPage(round) {
  let html = '';

  round.discussions.forEach((d, i) => {
    html += generateSpeakerCard(d.expert_id, d.stance, d.content, d.quotes, d.citations);
  });

  html += generateCollision(round.collision);

  return html;
}

let slidesHtml = '';

// Slide 0: Cover
slidesHtml += `<div class="slide hero title-slide" data-title="${escapeHtml(data.title)}">
  <div class="frame">
    <div class="slide-content" style="justify-content:center;align-items:center;text-align:center">
      <div class="cover-badge" data-anim>圆桌洞见</div>
      <div class="cover-title" data-anim>${escapeHtml(data.title)}</div>
      <div class="cover-sub" data-anim>${escapeHtml(data.subtitle)}</div>
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
          <div class="cover-stat-num">5</div>
          <div class="cover-stat-label">洞见</div>
        </div>
      </div>
      <div class="meta-row" data-anim>
        ${data.experts.map(e => `<span>${e.avatar} ${escapeHtml(e.name)}</span>`).join(' · ')}
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
    <div class="deck-footer">5个颠覆认知的观点</div>
  </div>
</div>`;

// Slide 2: Experts Overview
let expertsHtml = '<div class="grid-2">';
data.experts.forEach((e, i) => {
  expertsHtml += `<div class="card-rise" style="border-left-color:${e.color}" data-anim>
    <div class="speaker-header">
      <div class="speaker-avatar" style="background:${e.color}">${e.avatar}</div>
      <div>
        <div class="speaker-name">${escapeHtml(e.name)}</div>
        <div class="speaker-role">${escapeHtml(e.title)}</div>
      </div>
    </div>
  </div>`;
});
expertsHtml += '</div>';

slidesHtml += `<div class="slide" data-title="专家阵容">
  <div class="frame">
    <div class="kicker" data-anim>EXPERT PANEL</div>
    <div class="h-xl" data-anim style="margin-bottom:4vh">专家阵容</div>
    ${expertsHtml}
    <div class="deck-footer">6位跨界专家，3轮深度交锋</div>
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
        <div class="quote-large" data-anim style="max-width:700px;margin-top:3vh">${escapeHtml(round.description)}</div>
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
});

// Final Slide
slidesHtml += `<div class="slide hero title-slide" data-title="结语">
  <div class="frame">
    <div class="slide-content" style="justify-content:center;align-items:center;text-align:center">
      <div class="kicker" data-anim>CONCLUSION</div>
      <div class="h-hero" data-anim style="margin-bottom:4vh">散户狂潮中的生存法则</div>
      <div class="quote-large" data-anim style="max-width:800px;margin-bottom:4vh">
        在极端斯坦，活得久比赚得快更重要。杠铃策略不是悲观主义，而是对不确定性的最高敬意。
      </div>
      <div class="gold-line" data-anim></div>
      <div class="meta-row" data-anim>
        ${data.experts.map(e => `<span>${e.avatar} ${escapeHtml(e.name)}</span>`).join(' · ')}
      </div>
      <div style="margin-top:4vh;font-family:var(--mono);font-size:11px;letter-spacing:.15em;text-transform:uppercase;opacity:.4" data-anim>
        圆桌洞见 · ${data.date}
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
console.log(`HTML generated: ${outputPath}`);

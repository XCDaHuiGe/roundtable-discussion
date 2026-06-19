const fs = require('fs');
const path = require('path');

const jsonPath = path.join(__dirname, '..', 'content', '虚构世界_资产化_讨论.json');
const outputPath = path.join(__dirname, '..', 'output', '虚构世界_资产化_圆桌洞见.html');

const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;')
             .replace(/</g, '&lt;')
             .replace(/>/g, '&gt;')
             .replace(/"/g, '&quot;')
             .replace(/'/g, '&#039;');
}

function getExpertInfo(name) {
  const expert = data.experts[name];
  if (!expert) return { avatar: '💬', title: '', color: 'var(--accent)' };
  return expert;
}

function generateSpeakerCard(name, content, colorClass = '') {
  const info = getExpertInfo(name);
  const color = info.color || 'var(--accent)';
  const title = info.title || '';
  
  const paragraphs = content.split('\n').filter(p => p.trim());
  let contentHtml = paragraphs.map(p => {
    let line = escapeHtml(p);
    line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    line = line.replace(/\*(.*?)\*/g, '<em>$1</em>');
    return `<p style="margin-bottom:1.2vh;line-height:1.9">${line}</p>`;
  }).join('');

  return `<div class="sp" style="border-left-color:${color}">
    <div class="sh">
      <div class="speaker-avatar" style="background:${color}">${info.avatar}</div>
      <div>
        <div class="sn">${escapeHtml(name)}</div>
        <div class="sr">${escapeHtml(title)}</div>
      </div>
    </div>
    <div class="st">${contentHtml}</div>
  </div>`;
}

function generateCollision(collision) {
  if (!collision) return '';

  const title = collision.title || '';
  const content = collision.content || '';
  const paragraphs = content.split('\n').filter(p => p.trim());
  let contentHtml = paragraphs.map(p => `<p style="margin-bottom:1.2vh;line-height:1.9">${escapeHtml(p)}</p>`).join('');

  return `<div class="cb" style="background:rgba(var(--accent-rgb),.06);border:1px solid rgba(var(--accent-rgb),.15);border-radius:var(--radius);padding:3vh 2.5vw;margin-top:2vh">
    <div class="cl" style="font-family:var(--mono);font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);margin-bottom:2vh;font-weight:700">⚡ 专家交锋</div>
    <div style="font-family:var(--serif-zh);font-size:1.05rem;font-weight:600;margin-bottom:2vh;line-height:1.6">${escapeHtml(title)}</div>
    <div class="st">${contentHtml}</div>
  </div>`;
}

function generateInsights() {
  if (!data.conclusion || !data.conclusion.key_insights) return '';
  
  let html = '<div class="grid-2">';
  data.conclusion.key_insights.forEach((insight, i) => {
    html += `<div class="insight-c" data-anim>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:2vh">
        <span style="font-family:var(--mono);font-size:1.5rem;font-weight:900;color:var(--accent);opacity:.5">0${i+1}</span>
      </div>
      <div class="insight-q">${escapeHtml(insight.title)}</div>
      <div class="insight-a">${escapeHtml(insight.content)}</div>
    </div>`;
  });
  html += '</div>';
  return html;
}

function generateExpertsOverview() {
  let html = '<div class="grid-2">';
  const names = data.metadata.experts;
  names.forEach(name => {
    const info = getExpertInfo(name);
    const color = info.color || 'var(--accent)';
    html += `<div class="card-rise" style="border-left-color:${color}" data-anim>
      <div class="speaker-header">
        <div class="speaker-avatar" style="background:${color}">${info.avatar}</div>
        <div>
          <div class="speaker-name">${escapeHtml(name)}</div>
          <div class="speaker-role">${escapeHtml(info.title)}</div>
        </div>
      </div>
      <div style="font-size:.85rem;line-height:1.7;color:rgba(var(--paper-rgb),.7)">${escapeHtml(info.identity || '')}</div>
      <div style="margin-top:1vh;font-family:var(--mono);font-size:10px;letter-spacing:.05em;color:var(--gold)">专长：${escapeHtml(info.expertise || '')}</div>
    </div>`;
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
          <div class="cover-stat-num">${data.metadata.experts.length}</div>
          <div class="cover-stat-label">专家</div>
        </div>
        <div class="cover-stat">
          <div class="cover-stat-num">${data.metadata.rounds}</div>
          <div class="cover-stat-label">轮讨论</div>
        </div>
        <div class="cover-stat">
          <div class="cover-stat-num">${data.metadata.experts.length * data.metadata.rounds}</div>
          <div class="cover-stat-label">发言</div>
        </div>
        <div class="cover-stat">
          <div class="cover-stat-num">${data.conclusion && data.conclusion.key_insights ? data.conclusion.key_insights.length : 5}</div>
          <div class="cover-stat-label">洞见</div>
        </div>
      </div>
      <div class="meta-row" data-anim>
        ${data.metadata.experts.map(e => {
          const info = getExpertInfo(e);
          return `<span>${info.avatar} ${escapeHtml(e)}</span>`;
        }).join(' · ')}
      </div>
    </div>
  </div>
</div>`;

// Slide 1: Core Question
slidesHtml += `<div class="slide" data-title="核心问题">
  <div class="frame">
    <div class="kicker" data-anim>CORE QUESTION</div>
    <div class="h-xl" data-anim style="margin-bottom:4vh">核心问题</div>
    <div class="insight-c" data-anim style="margin-bottom:4vh">
      <div class="insight-q" style="font-size:1.3rem">${escapeHtml(data.metadata.subtitle)}</div>
    </div>
    <div class="h-lg" data-anim style="margin-bottom:3vh">四大核心矛盾</div>
    <div class="grid-2">
      <div class="card" data-anim>
        <div class="card-num">01</div>
        <div class="card-title">IP证券化</div>
        <div class="card-body">文化价值的解放还是文化的金融化异化？</div>
      </div>
      <div class="card" data-anim>
        <div class="card-num">02</div>
        <div class="card-title">宇宙化命题</div>
        <div class="card-body">《流浪地球》宇宙观是文化IP还是金融工具？</div>
      </div>
      <div class="card" data-anim>
        <div class="card-num">03</div>
        <div class="card-title">监管博弈</div>
        <div class="card-body">"去金融化"是中国式审慎还是对创新的扼杀？</div>
      </div>
      <div class="card" data-anim>
        <div class="card-num">04</div>
        <div class="card-title">泡沫之争</div>
        <div class="card-body">虚构世界资产化：增强文化影响力还是制造新的泡沫？</div>
      </div>
    </div>
  </div>
</div>`;

// Slide 2: Experts Overview
slidesHtml += `<div class="slide" data-title="专家阵容">
  <div class="frame">
    <div class="kicker" data-anim>EXPERT PANEL</div>
    <div class="h-xl" data-anim style="margin-bottom:4vh">专家阵容</div>
    ${generateExpertsOverview()}
    <div class="deck-footer">6位跨界专家，3轮深度交锋</div>
  </div>
</div>`;

// Discussion Rounds
data.rounds.forEach((round, roundIdx) => {
  const roundNum = roundIdx + 1;
  const theme = round.theme || '';

  // Round Title Slide
  slidesHtml += `<div class="slide title-slide" data-title="第${roundNum}轮：${escapeHtml(round.title)}">
    <div class="frame">
      <div class="hero-dark">
        <div class="kicker" data-anim>ROUND ${roundNum}</div>
        <div class="h-hero" data-anim style="background:linear-gradient(135deg,var(--paper) 0%,var(--gold) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">${escapeHtml(round.title)}</div>
        <div class="quote-large" data-anim style="max-width:700px;margin-top:3vh">${theme ? escapeHtml(theme) : ''}</div>
      </div>
    </div>
  </div>`;

  // Discussion Content - each speaker on their own slide
  round.speeches.forEach((speech, speechIdx) => {
    slidesHtml += `<div class="slide" data-title="第${roundNum}轮：${escapeHtml(speech.expert)}">
      <div class="frame">
        <div class="kicker" data-anim>ROUND ${roundNum} · ${speech.expert}</div>
        <div class="h-lg" data-anim style="margin-bottom:3vh">${escapeHtml(round.title)}</div>
        ${generateSpeakerCard(speech.expert, speech.content)}
        <div class="deck-footer">第 ${roundNum}/3 轮 · ${speech.expert}</div>
      </div>
    </div>`;
  });

  // Collision slide
  if (round.collision) {
    slidesHtml += `<div class="slide" data-title="第${roundNum}轮：专家交锋">
      <div class="frame">
        <div class="kicker" data-anim>ROUND ${roundNum} · 专家交锋</div>
        <div class="h-lg" data-anim style="margin-bottom:3vh">${escapeHtml(round.collision_title || '专家交锋')}</div>
        ${generateCollision(round.collision)}
        <div class="deck-footer">第 ${roundNum}/3 轮 · 碰撞总结</div>
      </div>
    </div>`;
  }
});

// Key Insights
if (data.conclusion && data.conclusion.key_insights) {
  slidesHtml += `<div class="slide" data-title="核心洞见">
    <div class="frame">
      <div class="kicker" data-anim>KEY INSIGHTS</div>
      <div class="h-xl" data-anim style="margin-bottom:4vh">核心洞见</div>
      ${generateInsights()}
      <div class="deck-footer">${data.conclusion.key_insights.length}个颠覆认知的观点</div>
    </div>
  </div>`;
}

// Summary
if (data.conclusion && data.conclusion.summary) {
  slidesHtml += `<div class="slide" data-title="总结">
    <div class="frame">
      <div class="kicker" data-anim>SUMMARY</div>
      <div class="h-xl" data-anim style="margin-bottom:4vh">六维总结</div>
      <div class="st" data-anim style="font-size:1rem;line-height:2">${data.conclusion.summary.split('\n\n').map(p => `<p style="margin-bottom:2vh">${escapeHtml(p)}</p>`).join('')}</div>
      <div class="deck-footer">圆桌洞见 · 总结</div>
    </div>
  </div>`;
}

// Final Slide
slidesHtml += `<div class="slide hero title-slide" data-title="结语">
  <div class="frame">
    <div class="slide-content" style="justify-content:center;align-items:center;text-align:center">
      <div class="kicker" data-anim>CONCLUSION</div>
      <div class="h-hero" data-anim style="margin-bottom:4vh">虚构世界的金融化之路</div>
      <div class="quote-large" data-anim style="max-width:800px;margin-bottom:4vh">
        当哈利·波特的魔法世界可以在金融市场上交易，当流浪地球的宇宙观成为可投资的资产类别，我们正在见证文化与资本关系的根本性转变。\n\n这不是终点，而是开始。
      </div>
      <div class="gold-line" data-anim></div>
      <div class="meta-row" data-anim>
        ${data.metadata.experts.map(e => {
          const info = getExpertInfo(e);
          return `<span>${info.avatar} ${escapeHtml(e)}</span>`;
        }).join(' · ')}
      </div>
      <div style="margin-top:4vh;font-family:var(--mono);font-size:11px;letter-spacing:.15em;text-transform:uppercase;opacity:.4" data-anim>
        圆桌洞见 · ${data.metadata.date} · V${data.metadata.version}
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
console.log(`Total slides: ${slidesHtml.split('<div class="slide').length - 1}`);

const fs = require('fs');
const path = require('path');

const jsonPath = path.join(__dirname, '..', 'content', '经典文学_AI创作_讨论.json');
const outputPath = path.join(__dirname, '..', 'output', '经典文学_AI创作_圆桌洞见.html');

const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

function escapeHtml(str) {
  if (!str) return '';
  if (typeof str !== 'string') return str;
  return str.replace(/&/g, '&amp;')
             .replace(/</g, '&lt;')
             .replace(/>/g, '&gt;')
             .replace(/"/g, '&quot;');
}

function escapeAttr(str) {
  if (!str) return '';
  return str.replace(/"/g, '&quot;');
}

function renderSlide(slide, index, total) {
  const type = slide.type;
  const title = slide.title || '';

  switch (type) {
    case 'hero-dark':
      return `<div class="slide hero title-slide" data-title="${escapeAttr(title)}">
  <div class="frame">
    <div class="slide-content" style="justify-content:center;align-items:center;text-align:center">
      <div class="cover-badge anim-in" data-anim>圆桌洞见</div>
      <h1 class="title-main anim-in anim-delay-1" data-anim>${escapeHtml(title)}</h1>
      <div class="title-sub anim-in anim-delay-2" data-anim>${escapeHtml(slide.subtitle || '')}</div>
      <div class="gold-line anim-in anim-delay-3" data-anim></div>
      ${slide.badges ? `<div class="cover-stats anim-in anim-delay-4" data-anim>
        ${slide.badges.map(b => `<div class="cover-stat"><div class="cover-stat-num">${escapeHtml(b)}</div></div>`).join('')}
      </div>` : ''}
    </div>
  </div>
  <div class="slide-number">${String(index + 1).padStart(2, '0')} / ${total}</div>
</div>`;

    case 'content':
      return `<div class="slide" data-title="${escapeAttr(title)}">
  <div class="frame">
    ${slide.section ? `<div class="kicker anim-in" data-anim>${escapeHtml(slide.section)}</div>` : ''}
    ${title ? `<h2 class="h-xl anim-in anim-delay-1" data-anim>${escapeHtml(title)}</h2>` : ''}
    <div class="anim-in anim-delay-2" data-anim>${slide.content}</div>
  </div>
  <div class="slide-number">${String(index + 1).padStart(2, '0')} / ${total}</div>
</div>`;

    case 'section-header':
      return `<div class="slide title-slide" data-title="${escapeAttr(title)}">
  <div class="frame">
    <div class="hero-dark">
      <div class="kicker anim-in" data-anim>SECTION</div>
      <h2 class="h-hero anim-in anim-delay-1" data-anim style="background:linear-gradient(135deg,var(--paper) 0%,var(--gold) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">${escapeHtml(title)}</h2>
      <div class="quote-large anim-in anim-delay-2" data-anim>${escapeHtml(slide.subtitle || '')}</div>
    </div>
  </div>
  <div class="slide-number">${String(index + 1).padStart(2, '0')} / ${total}</div>
</div>`;

    case 'clash-header':
      return `<div class="slide title-slide" data-title="${escapeAttr(title)}">
  <div class="frame">
    <div class="hero-dark">
      <div class="kicker anim-in" data-anim>⚡ EXPERT CLASH</div>
      <h2 class="h-hero anim-in anim-delay-1" data-anim style="background:linear-gradient(135deg,var(--accent) 0%,var(--purple) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">${escapeHtml(title)}</h2>
      <div class="quote-large anim-in anim-delay-2" data-anim>${escapeHtml(slide.subtitle || '')}</div>
    </div>
  </div>
  <div class="slide-number">${String(index + 1).padStart(2, '0')} / ${total}</div>
</div>`;

    case 'quote-slide':
      return `<div class="slide" data-title="核心洞见">
  <div class="frame">
    <div class="hero-dark" style="flex:1">
      <div class="kicker anim-in" data-anim>KEY QUOTE</div>
      <div class="quote anim-in anim-delay-1" data-anim style="max-width:800px;font-size:clamp(1.1rem,2vw,1.5rem);margin:4vh auto">${escapeHtml(slide.quote || '')}</div>
      ${slide.attribution ? `<div class="meta-row anim-in anim-delay-2" data-anim>- ${escapeHtml(slide.attribution)}</div>` : ''}
    </div>
  </div>
  <div class="slide-number">${String(index + 1).padStart(2, '0')} / ${total}</div>
</div>`;

    case 'footer':
      return `<div class="slide hero title-slide" data-title="${escapeAttr(title)}">
  <div class="frame">
    <div class="slide-content" style="justify-content:center;align-items:center;text-align:center">
      <div class="kicker anim-in" data-anim>ROUNDTABLE INSIGHT</div>
      <h2 class="title-main anim-in anim-delay-1" data-anim>${escapeHtml(title)}</h2>
      <div class="title-sub anim-in anim-delay-2" data-anim>${escapeHtml(slide.subtitle || '')}</div>
      <div class="gold-line anim-in anim-delay-3" data-anim></div>
      ${slide.experts ? `<div class="meta-row anim-in anim-delay-4" data-anim>${slide.experts.join(' · ')}</div>` : ''}
    </div>
  </div>
  <div class="slide-number">${String(index + 1).padStart(2, '0')} / ${total}</div>
</div>`;

    default:
      return '';
  }
}

const total = data.slides.length;
let slidesHtml = data.slides.map((slide, i) => renderSlide(slide, i, total)).join('\n');

const templatePath = path.join(__dirname, '..', 'assets', 'roundtable-template.html');
let template = fs.readFileSync(templatePath, 'utf-8');

template = template.replace('__BOOK_TITLE__', data.meta.title);
template = template.replace('<!-- SLIDES_HERE -->', slidesHtml);

fs.writeFileSync(outputPath, template, 'utf-8');
console.log(`HTML generated: ${outputPath}`);
console.log(`Total slides: ${total}`);

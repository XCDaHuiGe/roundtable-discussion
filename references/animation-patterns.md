# 动画模式参考（Animation Patterns）

生成演示文稿时使用此参考。根据预期情感匹配动画效果。

---

## 情感-动画映射指南

| 情感 | 动画效果 | 视觉提示 |
|:---|:---|:---|
| **戏剧/电影感** | 慢速淡入 (1-1.5s)、大比例过渡 (0.9→1)、视差滚动 | 深色背景、聚光灯效果、全出血图片 |
| **科技/未来感** | 霓虹发光 (box-shadow)、故障/乱码文字、网格揭示 | 粒子系统 (canvas)、网格图案、等宽字体、青/品红/电蓝 |
| **活泼/友好** | 弹性缓动 (spring physics)、浮动/摇摆 | 圆角、柔和/明亮色彩、手绘元素 |
| **专业/企业** | 微妙快速动画 (200-300ms)、干净切换 | 海军蓝/石板灰/炭灰、精确间距、数据可视化聚焦 |
| **平静/极简** | 非常慢的微妙运动、温和淡入 | 高留白、柔和色调、衬线字体、充足内边距 |
| **编辑/杂志** | 交错文字揭示、图文互动 | 强类型层次、引用块、打破网格的布局 |

---

## 入场动画

### 淡入 + 上滑（最通用）

```css
.reveal {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.6s cubic-bezier(.25,.46,.45,.94),
              transform 0.6s cubic-bezier(.25,.46,.45,.94);
}
.visible .reveal {
  opacity: 1;
  transform: translateY(0);
}
```

### 缩放进入

```css
.reveal-scale {
  opacity: 0;
  transform: scale(0.9);
  transition: opacity 0.6s, transform 0.6s cubic-bezier(.25,.46,.45,.94);
}
.visible .reveal-scale {
  opacity: 1;
  transform: scale(1);
}
```

### 从左滑入

```css
.reveal-left {
  opacity: 0;
  transform: translateX(-50px);
  transition: opacity 0.6s, transform 0.6s cubic-bezier(.25,.46,.45,.94);
}
.visible .reveal-left {
  opacity: 1;
  transform: translateX(0);
}
```

### 模糊进入

```css
.reveal-blur {
  opacity: 0;
  filter: blur(10px);
  transition: opacity 0.8s, filter 0.8s cubic-bezier(.25,.46,.45,.94);
}
.visible .reveal-blur {
  opacity: 1;
  filter: blur(0);
}
```

### 交错列表

```css
.stagger-list > * {
  opacity: 0;
  transform: translateY(20px);
}
.stagger-list.visible > *:nth-child(1) { transition-delay: 0ms; }
.stagger-list.visible > *:nth-child(2) { transition-delay: 100ms; }
.stagger-list.visible > *:nth-child(3) { transition-delay: 200ms; }
.stagger-list.visible > *:nth-child(4) { transition-delay: 300ms; }
.stagger-list.visible > *:nth-child(5) { transition-delay: 400ms; }
```

---

## 背景效果

### 渐变网格

```css
.gradient-bg {
  background:
    radial-gradient(ellipse at 20% 80%, rgba(120, 0, 255, 0.3) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(0, 255, 200, 0.2) 0%, transparent 50%),
    var(--bg-primary);
}
```

### 网格图案

```css
.grid-bg {
  background-image:
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 50px 50px;
}
```

### 点阵图案

```css
.dots-bg {
  background-image: radial-gradient(rgba(255,255,255,0.1) 1px, transparent 1px);
  background-size: 20px 20px;
}
```

---

## 交互效果

### 3D 倾斜悬停

```javascript
class TiltEffect {
  constructor(element) {
    this.element = element;
    this.element.style.transformStyle = 'preserve-3d';
    this.element.style.perspective = '1000px';

    this.element.addEventListener('mousemove', (e) => {
      const rect = this.element.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      this.element.style.transform = 
        `rotateY(${x * 10}deg) rotateX(${-y * 10}deg)`;
    });

    this.element.addEventListener('mouseleave', () => {
      this.element.style.transform = 'rotateY(0) rotateX(0)';
    });
  }
}
```

### 粒子背景

```javascript
class ParticleBackground {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.particles = [];
    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.init();
    this.animate();
  }

  resize() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  init() {
    const count = Math.min(80, Math.floor(this.canvas.width * this.canvas.height / 15000));
    for (let i = 0; i < count; i++) {
      this.particles.push({
        x: Math.random() * this.canvas.width,
        y: Math.random() * this.canvas.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        radius: Math.random() * 2 + 1,
        alpha: Math.random() * 0.5 + 0.1
      });
    }
  }

  animate() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    this.particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > this.canvas.width) p.vx *= -1;
      if (p.y < 0 || p.y > this.canvas.height) p.vy *= -1;
      
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      this.ctx.fillStyle = `rgba(201, 162, 39, ${p.alpha})`;
      this.ctx.fill();
    });

    // 连线
    for (let i = 0; i < this.particles.length; i++) {
      for (let j = i + 1; j < this.particles.length; j++) {
        const dx = this.particles[i].x - this.particles[j].x;
        const dy = this.particles[i].y - this.particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          this.ctx.beginPath();
          this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
          this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
          this.ctx.strokeStyle = `rgba(201, 162, 39, ${0.08 * (1 - dist / 120)})`;
          this.ctx.stroke();
        }
      }
    }

    requestAnimationFrame(() => this.animate());
  }
}
```

---

## 过渡效果

### 幻灯片切换

```css
.slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transform: translateX(100%);
  transition: opacity 0.5s, transform 0.5s;
}
.slide.active {
  opacity: 1;
  transform: translateX(0);
}
.slide.prev {
  transform: translateX(-100%);
}
```

### 淡入淡出

```css
.slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.6s;
}
.slide.active {
  opacity: 1;
}
```

### 缩放过渡

```css
.slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transform: scale(0.9);
  transition: opacity 0.5s, transform 0.5s;
}
.slide.active {
  opacity: 1;
  transform: scale(1);
}
```

---

## 自动动画（reveal.js 风格）

```html
<!-- 自动动画：元素间过渡 -->
<section class="slide" data-auto-animate>
  <h1 style="font-size: 4rem;">标题</h1>
</section>

<section class="slide" data-auto-animate>
  <h1 style="font-size: 2rem; position: absolute; top: 10%;">标题</h1>
  <p>新内容</p>
</section>
```

```css
[data-auto-animate] * {
  transition: all 0.6s cubic-bezier(.25,.46,.45,.94);
}
```

---

## 故障排除

| 问题 | 解决方案 |
|:---|:---|
| 字体未加载 | 检查 Google Fonts URL；确保 CSS 中字体名称匹配 |
| 动画未触发 | 验证 Intersection Observer 正在运行；检查 `.visible` 类是否被添加 |
| 滚动吸附不工作 | 确保 html 上有 `scroll-snap-type: y mandatory`；每个 slide 需要 `scroll-snap-align: start` |
| 移动端问题 | 在 768px 断点禁用重型效果；测试触摸事件；减少粒子数量 |
| 性能问题 | 谨慎使用 `will-change`；优先使用 `transform`/`opacity` 动画；节流滚动处理程序 |

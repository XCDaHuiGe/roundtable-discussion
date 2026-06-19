# 圆桌 HTML-PPT 退化诊断与升级原则

> 日期：2026-06-19  
> 对照样本：`output/天道_圆桌洞见.html`（旧版基线） vs `output/遥远的救世主_圆桌洞见.html`（新版退化样本）

## 结论

最近一次退化不是“视觉风格不够高级”这么简单，而是生成链路把强内容压扁了：

- 旧版《天道》有 14 页，包含 7 轮交锋、Shock Event、假设演化、开放问题、张力图谱。
- 新版《遥远的救世主》只有 12 页，主要重复“回应关系 / 关键冲突 / 核心洞见”，并大量使用通用话术。
- 原始 `content/遥远的救世主_V8.json` 里其实有强字段：`theme`、`key_question`、`reality_cases`、`cost_discussion`、`human_nature`、`cognitive_upgrade`、`open_questions`。退化发生在 V8 适配器和页面规划器。

## 外部参考拆解

| 来源 | 可取精华 | 融合方式 |
|---|---|---|
| `visual-style-ppt-skill` | Style Lock、缩略图总览、先定整套节奏再逐页生成 | 为圆桌输出建立“风格锁”和“页面节奏表”，防止每页像同一张卡片 |
| `guizang-ppt-skill` | 电子杂志 / 瑞士网格两套强风格、页面节奏、class 预检、逐页视觉 QA | 引入页面类型与版式匹配，不把概念页、案例页、数据页都塞进同一布局 |
| `html-ppt-skill` | 主题 tokens、布局 catalog、runtime 分离 | 圆桌 OS 应拆成数据适配器、页面规划器、版式渲染器、质量门 |
| `ppt-anything` | 每页是一个叙事 beat，情绪与观点同页成立 | 圆桌每页必须有“核心问题 + 情绪/冲击 + 认知位移”之一 |
| `web-design-skill` | 先声明设计系统，再写页面；反 AI-slop；固定 16:9 视距审查 | 将“死板卡片堆叠”列为失败模式，使用杂志焦点页、案例档案页、问题墙 |
| 飞书链接 | 当前链接需要权限或登录 | 暂不纳入，需用户导出或授权后再分析 |

## 新的生成原则

1. 内容先于模板：页面类型由材料字段驱动，不用模板强行套材料。
2. 一页一个 beat：每页必须承担明确叙事功能，如提问、冲击、冲突、升级、收束。
3. 版式有节奏：同一布局不能长期连续出现，至少包含焦点页、光谱页、案例页、冲突页、阶梯页、问题墙、张力图。
4. 保留现实代价：`reality_cases` 和 `cost_discussion` 优先生成 Shock 页。
5. 保留认知位移：`cognitive_upgrade` 必须生成“旧思维 -> 新思维 -> 复杂性 -> 行动洞见”。
6. 结尾不是总结：必须有开放问题或张力图谱，给下一轮思考留下入口。
7. 验收以浏览器为准：代码通过不等于作品成立，必须检查翻页、溢出、页面类型和关键页可读性。

## 已落地的第一批修复

- `engine/cognitive_model/adapters.py`：V8 适配器保留 `theme/key_question/reality_cases/cost_discussion/human_nature/cognitive_upgrade`。
- `engine/html_ppt/cognitive_page_contracts.py`：新增 `round_opening`、`case_shock`、`cognitive_upgrade`、`open_questions`、`tension_map` 等页面类型。
- `engine/html_ppt/cognitive_page_planner.py`：恢复轮次叙事链路：开场、立场、Shock、冲突、认知升级。
- `engine/html_ppt_v13_renderer.py`：新增 `magazine_focus`、`case_file`、`evolution_ladder`、`tension_bars`、`question_wall` 等版式。
- `engine/validate_html_ppt_v13.py`：修复乱码检查，并把新增页面类型纳入低密度白名单。
- `output/遥远的救世主_圆桌洞见.html`：从 12 页升级为 27 页，恢复 Shock、开放问题、张力图谱等关键层。

## 验收证据

- 单元测试：相关测试 `21 passed`。
- 生成验证：`Roundtable OS validation passed`，生成 27 页。
- 浏览器验收：逐页键盘翻页无主容器溢出；任一时刻只有 1 页 visible；Shock、开放问题、张力图谱均可进入并处于视口内。

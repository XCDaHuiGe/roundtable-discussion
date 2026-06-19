# V11 Agent 联网采集协议

## 热点标准模式

1. 实时联网搜索中文互联网热点。
2. 初筛 30 个候选。
3. 按争议价值筛出 10 个高争议话题。
4. 深挖前 3 个话题。
5. 每个话题选择 6 位专家。
6. 每个话题跑 3 轮训练。
7. 输出 `engine/v11_cli.py` 可消费的 prepared JSON。

## 信息源分层

- 事实确认层：Bing、新闻、官方说明、原始报道。
- 争议立场层：知乎 MCP、微博、小红书、B站、公众号、评论区抽样。
- 深度解释层：长文、专栏、研究、历史案例。
- 噪声过滤层：剔除纯八卦、谣言、标题党、重复搬运。

## prepared JSON 格式

顶层结构：

```json
{
  "run_id": "2026-06-08-hot-topics",
  "topics": []
}
```

每个 topic 必须包含：

- `title`
- `definition`
- `controversy_map`
- `experts`
- `rounds`
- `final_insights`

每个 round 必须包含：

- `round_number`
- `purpose`
- `original`
- `score`
- `lowest_dimension`
- `rewrite_instruction`
- `rewritten`

`score` 必须包含：

- `factual_robustness`
- `insight_delta`
- `conflict_strength`
- `persona_consistency`
- `structure`
- `practical_usefulness`
- `empty_talk_rate`

具体可参考 `tests/test_v11_cli.py`。

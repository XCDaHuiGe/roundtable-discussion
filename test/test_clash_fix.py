import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from engine.llm_generate import call_llm_json, DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT, DEFAULT_MAX_RETRIES

TOPIC = "AI时代的亲密关系"

STANCES = [
    {"expert": "项飙", "stance": "现代人的亲密关系正在经历前所未有的'附近'消失。算法推荐让人与人之间的真实连接被数据匹配取代，但情感的本质是具身的、不可量化的。"},
    {"expert": "韩炳哲", "stance": "数字时代让我们陷入了一种'自我剥削'的困境——我们不断优化自己，却从未真正休息。"},
    {"expert": "丹尼尔·卡尼曼", "stance": "从认知科学的角度，我对AI情感代理持谨慎乐观。"},
    {"expert": "傅盛", "stance": "AI情感代理本质上是一个'超个性化'的内容推荐系统。"},
]

prompt = f"""《{TOPIC}》圆桌讨论 - Round 2 碰撞环节

请生成 4 个专家之间的直接碰撞（互相反驳）。

【关键要求】每个碰撞必须有完整的"攻击+反击"结构：
1. 攻击要具体、有理有据，引用对方原文
2. 攻击类型：逻辑漏洞、利益冲突、现实矛盾、人性弱点、失败案例
3. 反击必须：承认对方部分观点，然后指出核心错误，给出替代方案
4. 反击长度不少于攻击长度的60%，不能只是简单否认

返回 JSON 格式：
{{
  "clash_rounds": [
    {{
      "attacker": "攻击者名",
      "target": "目标名",
      "attack_type": "逻辑漏洞|利益冲突|现实矛盾|人性弱点|失败案例",
      "attack_content": "攻击内容（150-400字），必须引用对方原文并指出具体错误",
      "emotion": "serious|anger|sarcasm",
      "counter_attack": "反击内容（150-300字），承认部分观点后反驳，给出替代方案"
    }}
  ]
}}"""

print("Calling LLM...")
result = call_llm_json(
    prompt,
    "你是圆桌讨论的碰撞导演，每个碰撞必须有完整的攻击+反击结构。",
    connect_timeout=DEFAULT_CONNECT_TIMEOUT,
    read_timeout=DEFAULT_READ_TIMEOUT,
    max_retries=DEFAULT_MAX_RETRIES,
)

print(f"Success: {result['success']}")
print(f"Error: {result.get('error', 'none')}")
print(f"Data keys: {list(result.get('data', {}).keys()) if result.get('data') else 'none'}")

if result["success"] and result["data"]:
    clashes = result["data"].get("clash_rounds", [])
    print(f"\nGenerated {len(clashes)} clashes\n")

    for i, c in enumerate(clashes, 1):
        attack = c.get("attack_content", "")
        counter = c.get("counter_attack", "")
        ratio = len(counter) / len(attack) if attack else 0
        print(f"Clash {i}: {c.get('attacker')} -> {c.get('target')}")
        print(f"  Type: {c.get('attack_type')}")
        print(f"  Attack: {len(attack)} chars")
        print(f"  Counter: {len(counter)} chars ({ratio:.0%})")
        print(f"  Counter: {counter[:100]}...")
        print()
else:
    print(f"Failed. Raw response: {str(result)[:500]}")

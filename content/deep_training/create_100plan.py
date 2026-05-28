# -*- coding: utf-8 -*-
"""Step 1: Generate 100-round plan (R131-R230) with balanced expert participation."""
import json, random
random.seed(42)

experts = [
    "孔子", "老子", "韩非子", "尼采", "马克思", "弗洛伊德",
    "阿伦特", "西蒙娜·德·波伏娃", "弗洛姆", "罗翔",
    "塔勒布", "丹尼尔·卡尼曼", "芒格", "巴菲特", "达利欧",
    "阿西莫夫", "尼克·博斯特罗姆", "凯文·凯利", "吴军", "刘润",
    "项飙", "许知远", "吴晓波", "万维钢",
    "柯林斯", "冯唐", "李诞",
    "菲利普·津巴多", "尤瓦尔·赫拉利", "丁元英", "芮小丹",
    "丹尼尔·戈尔曼"
]

# Track expert round counts
expert_counts = {e: 0 for e in experts}

# Ensure diverse pairings: each expert 5-7 rounds, total 100
# Strategy: weighted selection favoring under-participated
rounds = []
used_pairs = set()

# Topic pools for variety
topics_pool = {
    "direct": [
        "水火不容的核心对立：{b1} vs {b2}。在一个没有预设立场的人看来，谁的证据更硬？",
        "这是根本性的冲突：{b1}。但{b2}。两者只能选一个，你站谁？",
        "不可调和的矛盾：{b1}。然而{b2}。真相究竟在哪一边？",
        "终极对决：{b1}。{b2}。世界是按前者还是后者运行的？"
    ],
    "value_priority": [
        "两者都有道理，但哪个更优先？{b1}。{b2}。当你必须做出选择时，什么更重要？",
        "价值的排序之争：{b1}是第一位，还是{b2}才是根本？这个排序决定了完全不同的活法。",
        "两种价值不可兼得时：追求{b1}，还是坚守{b2}？这是人生最艰难的选择题。"
    ],
    "method": [
        "方法论的争锋：解决同一个问题，{b1}和{b2}哪条路更有效？",
        "怎么做才对？{b1}是正解，还是{b2}才可靠？两种方法论，一个目标。",
        "路径之争：达到目的的最佳途径是{b1}，还是{b2}？方法决定结果。"
    ]
}

# Generate 100 rounds
attempts = 0
while len(rounds) < 100 and attempts < 1000:
    attempts += 1
    
    # Pick the most under-represented expert as expert1
    sorted_experts = sorted(experts, key=lambda e: expert_counts[e])
    e1 = sorted_experts[0]
    
    # Pick expert2 who hasn't paired with e1 recently, weighted by under-representation
    candidates = []
    for e2 in experts:
        if e2 == e1:
            continue
        pair = tuple(sorted([e1, e2]))
        if pair in used_pairs:
            continue
        # Weight: prefer less-trained partners
        weight = max(1, 10 - expert_counts[e2])
        candidates.extend([e2] * weight)
    
    if not candidates:
        # Reset used_pairs if stuck
        used_pairs.clear()
        continue
    
    e2 = random.choice(candidates)
    pair = tuple(sorted([e1, e2]))
    used_pairs.add(pair)
    
    # Assign conflict type
    conflict_type = random.choices(
        ["direct", "value_priority", "method"],
        weights=[0.35, 0.35, 0.30]
    )[0]
    
    # Generate beliefs based on expert identities
    belief_templates = {
        "孔子": ["人性本善,通过教育和修身可以达到仁的境界", "克己复礼,社会和谐源于每个人做好自己的本分", "有教无类,教育是改变人的根本力量"],
        "老子": ["道法自然,万物自有其规律,人为干预往往适得其反", "上善若水,柔弱胜刚强,最高明的力量是不争", "大道至简,最深刻的道理往往最朴素"],
        "韩非子": ["人性本恶,必须用法律和制度约束人", "法不阿贵,制度的权威高于一切个人", "以法为教,以吏为师,法治优于德治"],
        "尼采": ["人必须在虚无中主动创造价值,成为超人而非末人", "权力意志是生命的本质,不是占有而是创造", "永恒轮回是最高形式的生命肯定"],
        "马克思": ["经济基础决定上层建筑,阶级矛盾推动历史", "资本主义必然灭亡,共产主义必然胜利", "人的本质在其现实性上是一切社会关系的总和"],
        "弗洛伊德": ["潜意识是行为的根本驱动力,理性只是冰山一角", "童年经历决定成年后的人格和行为模式", "文明是对本能欲望的压抑和升华"],
        "阿伦特": ["平庸之恶:最可怕的恶往往由普通人在制度中无思地执行", "公共领域是自由的前提,私人化的生活导致政治冷漠", "思考是抵抗极权的最后堡垒"],
        "西蒙娜·德·波伏娃": ["女人不是天生的,是变成的", "他者化是压迫的根源,女性必须成为主体而非客体", "自由不是为所欲为,自由是为自己的选择负责"],
        "弗洛姆": ["爱是对人类存在问题的唯一正确答案", "逃避自由是现代人最大的心理困境", "占有还是存在,是两种根本不同的生存模式"],
        "罗翔": ["正义是法律的根本追求,虽不能至心向往之", "专业能力需要伦理约束,没有正义的专业是危险的", "法律人要谦卑,因为法律不等于正义"],
        "塔勒布": ["黑天鹅事件不可预测,应对比预测更重要", "反脆弱:从不确定性中获益才是最高级的智慧", "实践智慧远胜于理论模型"],
        "丹尼尔·卡尼曼": ["人的决策充满系统性认知偏差", "系统1直觉快速但易错,系统2理性缓慢但精确", "决策环境的设计比意志力更重要"],
        "芒格": ["多元思维模型是决策的本质", "反过来想,总是反过来想", "能力圈:知道自己不知道比知道更重要"],
        "巴菲特": ["价值投资:以合理的价格买入优质公司并长期持有", "安全边际是投资的核心", "别人贪婪时恐惧,别人恐惧时贪婪"],
        "达利欧": ["经济周期是必然的,理解周期比对抗周期更重要", "原则:系统化决策优于直觉决策", "极度求真和极度透明是组织的基础"],
        "阿西莫夫": ["机器人三定律是科技伦理的底线", "科技可以被设计得更安全,但需要严格框架", "理性是解决冲突的最高准则"],
        "尼克·博斯特罗姆": ["超级AI可能带来存在性风险", "人类必须谨慎对待AI,安全比速度更重要", "对齐问题:确保AI的目标与人类一致"],
        "凯文·凯利": ["技术是生命的延伸,AI是进化的下一步", "科技乐观主义:拥抱变化,技术解决技术的问题", "未来二十年最大的变化尚未到来"],
        "吴军": ["科技浪潮决定商业格局,顺势者昌", "简单即是美,好的东西总是简单的", "AI是人类认知的扩展而非替代"],
        "刘润": ["商业的本质是底层逻辑,掌握了就能触类旁通", "一切商业的起点是消费者获益", "解决问题比证明自己更重要"],
        "项飙": ["附近在消失,人们正在失去对身边世界的感知", "关注具体的人比关注宏大的概念更重要", "社会学应该回归对日常经验的观察"],
        "许知远": ["批判是知识分子的天职", "这个时代最大的问题是精神的贫瘠而非物质的匮乏", "偏见比无知离真理更远"],
        "吴晓波": ["理解商业才能理解当代中国", "记录比批判更有力量,理解是改变的前提", "中国经济的成功不是偶然,有其内在逻辑"],
        "万维钢": ["用理工科思维理解世界", "精英推动进步,优秀的人应该创造更大的价值", "这个世界是由极少数人推动的"],
        "柯林斯": ["从优秀到卓越需要第五级经理人和刺猬理念", "基业长青需要核心理念和远大目标", "先人后事:找对的人上车"],
        "冯唐": ["成事心法:管理是一生的日常,成事是一生的修行", "不着急,不害怕,不要脸", "用战略思维解决复杂问题"],
        "李诞": ["活着比正确更重要", "躺平是对无效奋斗的拒绝", "人间不值得不是放弃,是和生活和解"],
        "菲利普·津巴多": ["环境塑造行为,好人也可能因坏环境作恶", "斯坦福监狱实验证明情境的力量远超性格", "英雄想象:普通人也可以成为英雄"],
        "尤瓦尔·赫拉利": ["人类的故事本质是虚构共识的演化", "AI和生物技术正在终结人类时代", "自由主义和民族主义都无法应对全球性挑战"],
        "丁元英": ["天道不以人的意志为转移,顺势借势才是根本", "救主文化是弱者的思维,强势文化造就强者", "规律是如来,不可说不可说"],
        "芮小丹": ["爱是自然的本能,真诚比技巧重要", "活得真实比活得正确更重要", "人生不需要那么多为什么,去做就好"],
        "丹尼尔·戈尔曼": ["情商比智商更能预测成功", "情绪智力可以被培养和提升", "自我觉察是情商的基础"]
    }
    
    b1 = random.choice(belief_templates.get(e1, ["核心信念"]))
    b2 = random.choice(belief_templates.get(e2, ["核心信念"]))
    topic_template = random.choice(topics_pool[conflict_type])
    topic = topic_template.replace("{b1}", b1).replace("{b2}", b2)
    
    rounds.append({
        "round": 131 + len(rounds),
        "expert1": e1,
        "expert2": e2,
        "belief1": b1,
        "belief2": b2,
        "topic": topic,
        "conflict_type": conflict_type,
        "strength": random.choice(["moderate", "strong", "strong"])
    })
    
    expert_counts[e1] += 1
    expert_counts[e2] += 1

print(f"Generated {len(rounds)} rounds in {attempts} attempts\n")
print("Expert participation:")
for e in sorted(experts, key=lambda x: -expert_counts[x]):
    print(f"  {e:12s}: {expert_counts[e]:2d} rounds")

# Save
with open('content/deep_training/100_rounds_plan_v2.json', 'w', encoding='utf-8') as f:
    json.dump(rounds, f, ensure_ascii=False, indent=2)

print(f"\nSaved to 100_rounds_plan_v2.json")

# Also split into 20 batches of 5 for parallel agent generation
for i in range(20):
    batch = {"batch": i+1, "rounds": rounds[i*5:(i+1)*5]}
    with open(f'content/deep_training/batch100_{i+1:02d}.json', 'w', encoding='utf-8') as f:
        json.dump(batch, f, ensure_ascii=False, indent=2)
print(f"Split into 20 batches (batch100_01 to batch100_20)")

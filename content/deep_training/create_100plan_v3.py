# -*- coding: utf-8 -*-
"""Create 100-round plan (R231-R330) with unique pairings, balanced participation."""
import json, random
random.seed(202606)

experts = [
    "孔子","老子","韩非子","尼采","马克思","弗洛伊德",
    "阿伦特","西蒙娜·德·波伏娃","弗洛姆","罗翔",
    "塔勒布","丹尼尔·卡尼曼","芒格","巴菲特","达利欧",
    "阿西莫夫","尼克·博斯特罗姆","凯文·凯利","吴军","刘润",
    "项飙","许知远","吴晓波","万维钢",
    "柯林斯","冯唐","李诞",
    "菲利普·津巴多","尤瓦尔·赫拉利","丁元英","芮小丹",
    "丹尼尔·戈尔曼"
]

# Load existing rounds to avoid repeating pairings
existing_pairs = set()
import glob
for f in glob.glob('content/deep_training/round*.json'):
    try:
        d = json.loads(open(f, 'r', encoding='utf-8-sig').read())
        exps = tuple(sorted([e['name'] for e in d.get('experts', [])]))
        existing_pairs.add(exps)
    except:
        pass
print(f"Existing unique pairs: {len(existing_pairs)}")

beliefs_pool = {
    "孔子": ["仁者爱人,推己及人", "克己复礼为仁", "有教无类,因材施教", "不患寡而患不均", "己所不欲勿施于人"],
    "老子": ["道可道非常道", "无为而无不为", "知足者富,强行者有志", "大巧若拙,大辩若讷", "天下皆知美之为美斯恶矣"],
    "韩非子": ["法不阿贵,绳不挠曲", "道私者乱,道法者治", "以法为教,以吏为师", "治国无法则乱", "刑过不避大臣,赏善不遗匹夫"],
    "尼采": ["凡不能毁灭我的必使我强大", "人是一根绳索悬于深渊之上", "幸福就是有能力增加负担", "没有事实只有诠释", "在自己身上克服这个时代"],
    "马克思": ["哲学家只是解释世界问题在于改变世界", "人是一切社会关系的总和", "资本从来到世间每个毛孔都滴着血", "宗教是人民的鸦片", "自由不在于幻想中摆脱自然规律"],
    "弗洛伊德": ["梦是愿望的达成", "在潜意识中没有时间概念", "本我所在自我必至", "压抑不是消失而是在暗中发酵", "人的历史就是一部压抑史"],
    "阿伦特": ["恶是表面的深渊", "极权主义下人人都是齿轮", "思考是抵抗平庸之恶的唯一方式", "公共领域是自由的前提", "孤独使人丧失思考能力"],
    "西蒙娜·德·波伏娃": ["女人不是天生的而是变成的", "他者即地狱", "自由是选择的而非给予的", "处境无法定义你如何回应才定义你", "爱不是拯救而是共同成长"],
    "弗洛姆": ["现代人逃避自由", "爱是唯一理性的答案", "占有还是存在这是根本问题", "孤独感是人最深的恐惧", "消费主义是异化的最高形式"],
    "罗翔": ["法律是对人的最低要求", "正义如圆虽不能至心向往之", "法律的目的是维护秩序而不是彰显权力", "法治优于人治", "没有伦理约束的专业是危险的"],
    "塔勒布": ["你不知道的事比你知道的事更重要", "反脆弱是在不确定性中获益", "不要相信穿着西装的骗子", "经验优于理论", "少即是多"],
    "丹尼尔·卡尼曼": ["直觉快思考容易犯错", "思维懒惰是人类的天性", "确认偏误让你只看到想看的", "损失厌恶比获利渴望强两倍", "锚定效应无处不在"],
    "芒格": ["反过来想总是反过来想", "多元思维模型是决策利器", "能力圈比能力更重要", "激励机制是超级力量", "耐心是最大的美德"],
    "巴菲特": ["以合理价格买入优质企业", "安全边际是一切投资的核心", "别人恐惧时我贪婪", "复利是宇宙最强大的力量", "大潮退去才知道谁在裸泳"],
    "达利欧": ["痛苦加反思等于进步", "拥抱现实应对现实", "极度求真极度透明", "原则是系统化决策的基础", "从更高的层面俯视自己"],
    "阿西莫夫": ["机器人三定律是底线", "暴力是无能者的最后手段", "理性可以解决任何冲突", "知识本身即是危险", "科技需要伦理导航"],
    "尼克·博斯特罗姆": ["AI安全是文明优先事项", "超级智能可能一夜降临", "价值对齐是最硬的难题", "存在性风险不是科幻", "技术乐观主义需要审慎制衡"],
    "凯文·凯利": ["技术是生命的第七王国", "AI不是威胁而是进化", "去中心化是必然趋势", "未来二十年最大变化尚未到来", "拥抱科技就是拥抱人性"],
    "吴军": ["简单的东西才是最好的", "浪潮之巅顺势者昌", "AI是认知的延伸非替代", "信息密度决定认知深度", "科技史的规律是降维打击"],
    "刘润": ["一切商业的起点是消费者获益", "底层逻辑是万变不离其宗", "商业不是零和博弈", "抓住本质就抓住了一切", "解决问题比证明自己更重要"],
    "项飙": ["附近消失是人类学的危机", "关注具体的人而非抽象的概念", "全球化带来认同的焦虑", "内卷是资源争夺的囚徒困境", "做具体的事爱具体的人"],
    "许知远": ["偏见是通往真相的最大障碍", "娱乐至死是时代的精神危机", "批判是知识分子的天职", "这个时代最缺的是独立思考", "精英的堕落比大众的无知更可怕"],
    "吴晓波": ["改革开放是当代中国的底层逻辑", "商业的力量改变社会", "中国企业家的创造力被低估了", "理解经济才能理解中国", "制造业是中国经济的底盘"],
    "万维钢": ["用理工科思维破除迷思", "精英是推动进步的关键少数", "科学方法是最可靠的认知工具", "世界是复杂的不存在简单答案", "承认无知是智慧的开始"],
    "柯林斯": ["第五级经理人谦卑而坚定", "先人后事是基业长青的起点", "刺猬理念让你聚焦一件事", "飞轮效应持续积累终将爆发", "纪律文化优于个人英雄主义"],
    "冯唐": ["不着急不害怕不要脸", "成事心法是一生的修行", "管理是一生的日常", "战略的本质是取舍", "知行合一才是真本事"],
    "李诞": ["人间不值得但值得笑", "活着比正确更重要", "躺平是对无效奋斗的拒绝", "笑是最高形式的思考", "荒诞是生活的底色"],
    "菲利普·津巴多": ["情境的力量超越性格", "好人也会在坏环境中作恶", "斯坦福监狱实验是人性的镜子", "系统比个人更容易腐败", "英雄是敢于在情境中说的人"],
    "尤瓦尔·赫拉利": ["人类的故事是虚构共识", "AI和生物技术终结人类时代", "自由主义叙事已经破产", "自由意志是最大的幻觉", "数据主义正在取代人文主义"],
    "丁元英": ["规律不以人的意志为转移", "救主文化是弱势文化的根源", "强势文化造就强者", "见路不走即见因果", "天道即自然规律"],
    "芮小丹": ["活得真实比活得正确更重要", "爱是本能不需要理论", "去做比去想更重要", "人生不需要那么多为什么", "纯粹本身就是力量"],
    "丹尼尔·戈尔曼": ["情商比智商更能预测成功", "自我觉察是情商的基础", "情绪可以被管理不能被压抑", "同理心是领导力的核心", "认知控制在AI时代更重要"]
}

# Generate plan
rounds = []
expert_counts = {e: 0 for e in experts}
used_pairs = set(existing_pairs)

# Conflict type pool
types = ["direct", "value_priority", "method"]

round_num = 231
attempts = 0
total_desired = 100
while len(rounds) < total_desired and attempts < 2000:
    attempts += 1
    
    # Pick most under-trained expert
    sorted_experts = sorted(experts, key=lambda e: expert_counts[e])
    e1 = sorted_experts[0]
    
    # Find eligible partner
    candidates = []
    for e2 in experts:
        if e2 == e1: continue
        pair = tuple(sorted([e1, e2]))
        if pair in used_pairs: continue
        weight = max(1, 8 - expert_counts[e2])
        candidates.extend([e2] * weight)
    
    if not candidates:
        if len(used_pairs) > len(existing_pairs):
            used_pairs = set(existing_pairs)  # reset within this batch only
        continue
    
    e2 = random.choice(candidates)
    pair = tuple(sorted([e1, e2]))
    used_pairs.add(pair)
    
    conflict = random.choice(types)
    b1 = random.choice(beliefs_pool[e1])
    b2 = random.choice(beliefs_pool[e2])
    
    topic_templates = {
        "direct": [
            f"水火不容:{b1}。但{b2}。谁的证据更硬?",
            f"终极对立:{b1} vs {b2}。两者只能信一个,选哪个?",
            f"不可调和:{b1}。然而{b2}。真相在哪一边?"
        ],
        "value_priority": [
            f"价值排序之争:{b1}更重要,还是{b2}更重要?",
            f"不能兼得时:{b1}和{b2}你优先选哪个?",
            f"什么更重要?{b1}还是{b2}?"
        ],
        "method": [
            f"方法论之争:解决问题的最佳路径是{b1},还是{b2}?",
            f"哪种方法更有效?{b1}还是{b2}?",
            f"路径选择:{b1}还是{b2}才是正解?"
        ]
    }
    topic = random.choice(topic_templates[conflict])
    
    rounds.append({
        "round": round_num,
        "expert1": e1, "expert2": e2,
        "belief1": b1, "belief2": b2,
        "topic": topic,
        "conflict_type": conflict,
        "strength": random.choice(["strong","strong","moderate"])
    })
    expert_counts[e1] += 1
    expert_counts[e2] += 1
    round_num += 1

# Save plan
with open('content/deep_training/100_rounds_plan_v3.json', 'w', encoding='utf-8') as f:
    json.dump(rounds, f, ensure_ascii=False, indent=2)

print(f"Created {len(rounds)} rounds (R231-R{231+len(rounds)-1})")
print(f"Attempts needed: {attempts}\n")

print("Expert participation:")
for e in sorted(experts, key=lambda x: -expert_counts[x]):
    print(f"  {e:12s}: {expert_counts[e]:2d}")

# Split into 20 batches of 5
for i in range(20):
    batch = {"batch": i+1, "rounds": rounds[i*5:(i+1)*5]}
    with open(f'content/deep_training/batch_v3_{i+1:02d}.json', 'w', encoding='utf-8') as f:
        json.dump(batch, f, ensure_ascii=False, indent=2)
print(f"\nSplit into 20 batches (batch_v3_01 to batch_v3_20)")

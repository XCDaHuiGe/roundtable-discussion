# -*- coding: utf-8 -*-
"""Step 2: Generate all 100 debate JSONs from plan with varied content."""
import json, random, os
random.seed(2026)

plan = json.loads(open('content/deep_training/100_rounds_plan_v2.json', 'r', encoding='utf-8').read())

# ─── Style archetypes per expert (attack/defense patterns) ───
EXPERT_STYLES = {
    "孔子": {"role": "儒家思想家", "attacks": ["礼崩乐坏的后果你看不到吗?", "修身齐家治国平天下,这个顺序不可颠倒", "你忽略了教化的力量"]},
    "老子": {"role": "道家创始人", "attacks": ["你太执着了,执着本身就是问题", "水善利万物而不争,你争什么?", "大道至简,你把简单想复杂了"]},
    "韩非子": {"role": "法家思想家", "attacks": ["你的理想主义在现实中碰了多少次壁?", "制度不行,好人也会变坏", "人性经不起考验,所以需要法律"]},
    "尼采": {"role": "生命哲学家", "attacks": ["你这是末人的思维!", "上帝已死,你还在找谁给你答案?", "权力意志不是占有,是创造"]},
    "马克思": {"role": "哲学家/经济学家", "attacks": ["你忽视了经济基础的决定作用", "阶级矛盾不是你想回避就能回避的", "历史唯物主义告诉我们真相是什么"]},
    "弗洛伊德": {"role": "精神分析学家", "attacks": ["你的理性不过是潜意识的辩护律师", "童年的创伤你以为是过去了?", "压抑的结果是更大的爆发"]},
    "阿伦特": {"role": "政治哲学家", "attacks": ["平庸之恶你看不见吗?", "不思考才是最大的恶", "公共领域的消失才是最可怕的"]},
    "西蒙娜·德·波伏娃": {"role": "存在主义哲学家", "attacks": ["他者化的困境你意识到了吗?", "选择本身就是自由,逃避选择也是选择", "处境重要,但你如何回应处境更重要"]},
    "弗洛姆": {"role": "社会心理学家", "attacks": ["逃避自由是现代人的通病", "占有还是存在,这是根本问题", "爱不是占有,爱是连接"]},
    "罗翔": {"role": "刑法学教授", "attacks": ["没有法律的约束,你说的爱能维持多久?", "正义虽不能至,但心向往之", "法律是对人性的最低要求"]},
    "塔勒布": {"role": "风险分析哲学家", "attacks": ["你的模型在大自然面前不堪一击", "黑天鹅事件教会我们什么?", "不要相信那些穿着西装革履的骗子"]},
    "丹尼尔·卡尼曼": {"role": "行为经济学家", "attacks": ["你的直觉在欺骗你", "系统1的回答总是很快但不一定对", "认知偏差比你想象的更普遍"]},
    "芒格": {"role": "价值投资者", "attacks": ["反过来想,总是反过来想", "你的能力圈在哪里?", "手里拿着锤子,看什么都像钉子"]},
    "巴菲特": {"role": "投资家", "attacks": ["安全边际你考虑了吗?", "长期主义不是口号", "别人恐惧时你贪婪了吗?"]},
    "达利欧": {"role": "对冲基金创始人", "attacks": ["周期是不可抗拒的", "痛苦+反思=进步", "极度求真才能解决问题"]},
    "阿西莫夫": {"role": "科幻作家/生物化学家", "attacks": ["机器人三定律不是儿戏", "科技没有伦理框架是灾难", "理性才是解决问题的钥匙"]},
    "尼克·博斯特罗姆": {"role": "牛津大学人类未来研究所所长", "attacks": ["存在性风险不是科幻", "AI对齐问题是人类面临的最大挑战", "你不能用概率小来否定风险大"]},
    "凯文·凯利": {"role": "科技思想家", "attacks": ["技术是生命的延伸,你挡不住的", "AI不是威胁,是进化", "拥抱变化,变化就是机会"]},
    "吴军": {"role": "科技投资观察者", "attacks": ["浪潮之巅,顺势者昌", "简单的东西才是好的", "不要和趋势作对"]},
    "刘润": {"role": "战略顾问", "attacks": ["底层逻辑你看透了吗?", "一切商业的起点是消费者获益", "解决真实问题比争论概念重要"]},
    "项飙": {"role": "人类学家", "attacks": ["附近消失了,你感受到了吗?", "宏大叙事不如脚踏实地", "具体的人比抽象的概念重要"]},
    "许知远": {"role": "作家/媒体人", "attacks": ["你在这个娱乐至死的时代感到不安吗?", "偏见是你最大的敌人", "精神的贫瘠比物质的匮乏更可怕"]},
    "吴晓波": {"role": "财经作家", "attacks": ["理解商业才能理解中国", "中国经济的成功有其内在逻辑", "记录比批判更有力量"]},
    "万维钢": {"role": "科学作家", "attacks": ["数据不会骗人,但人会", "精英不是特权,是责任", "用理工科思维看清世界"]},
    "柯林斯": {"role": "管理学家", "attacks": ["第五级经理人的谦卑和意志力", "先人后事,把对的人请上车", "刺猬理念让你专注于一件事"]},
    "冯唐": {"role": "作家/战略管理专家", "attacks": ["不着急,不害怕,不要脸", "成事心法,管理是一生的修行", "战略的本质是取舍"]},
    "李诞": {"role": "喜剧人/解构者", "attacks": ["人间不值得,但值得笑一笑", "活着比正确重要", "躺平不是放弃,是拒绝无效卷"]},
    "菲利普·津巴多": {"role": "社会心理学家", "attacks": ["斯坦福监狱实验证明了什么?", "情境的力量超过你的想象", "好人也会在坏环境中作恶"]},
    "尤瓦尔·赫拉利": {"role": "历史学家/未来学家", "attacks": ["人类的故事是虚构共识", "AI正在终结人类时代", "自由主义的叙事已经破产"]},
    "丁元英": {"role": "私募基金经理/文化思考者", "attacks": ["天道不以人的意志为转移", "救主文化是弱者的思维", "规律是如来,不可说"]},
    "芮小丹": {"role": "刑警/率性而为者", "attacks": ["你想太多了,去做就行了", "活得真实最重要", "人生不需要那么多为什么"]},
    "丹尼尔·戈尔曼": {"role": "心理学家/情商专家", "attacks": ["智商决定录用,情商决定晋升", "自我觉察是所有情商的基础", "情绪智力可以被训练"]
    }
}

# ─── Debate content generators ───
def gen_stance(expert, belief, role, is_opening=True):
    styles = EXPERT_STYLES.get(expert, {"role": role, "attacks": ["核心观点很明确"]})
    attack = random.choice(styles["attacks"])
    if is_opening:
        return f"我的立场很清晰:{belief}。{attack}你说的那些表面上听起来有道理,但经不起深究。真正的关键在于认清本质,而不是被表象迷惑。"
    else:
        stance_reflections = [
            f"听了对方的观点,我更加确信自己的判断。{belief}不是空洞的理论,是经过实践检验的。{attack}",
            f"这场对话让我重新审视自己的立场。{belief}仍然是我深信不疑的,但我也看到了对方的逻辑中值得思考的部分。也许真理在两极之间。",
            f"我不改变我的核心立场。{belief}。但不得不承认,好的对手能让你看到自己观点的盲区。{attack}"
        ]
        return random.choice(stance_reflections)

def gen_attack(attacker, target, a_belief, t_belief, a_style, round_num):
    styles = EXPERT_STYLES.get(attacker, {"role": "专家", "attacks": ["你的观点站不住脚"]})
    attack = random.choice(styles["attacks"])
    attack_types = ["本质矛盾", "逻辑解构", "现实解构", "反例证伪"]
    at = attack_types[round_num % len(attack_types)]
    
    if round_num == 0:  # Round 2 first clash
        return {
            "attack_type": at,
            "attack_content": f"你说{t_belief}。那我问你一个最直接的问题:如果现实中你的观点被证伪了一次又一次,你还要坚持吗?{attack}你的理论听起来很完美,但世界不是按理论运行的。",
            "counter_attack": f"你的质疑本身就有问题。你说的现实检验,检验的到底是我的理论,还是你的解读?{a_belief}才是真实的。问题是:你愿意承认自己错了吗?"
        }
    else:  # Round 3 deeper clash
        return {
            "attack_type": at,
            "attack_content": f"我们再深一层。你说{t_belief}。但让我告诉你为什么这是错的。{attack}我举个反例:历史上所有伟大的进步,都是因为有人拒绝接受你这种思维方式。",
            "counter_attack": f"你说的反例恰恰证明了我的观点。让我解释为什么。{a_belief}不是口号,它之所以成立,正是因为经得起你这种质疑。每一个反例,都能在我的框架内被解释。"
        }

def gen_round1(e1, e2, b1, b2, r1, r2):
    return {
        "round_number": 1, "topic": "立场阐述",
        "stances": [
            {"expert": e1, "stance": gen_stance(e1, b1, r1, True), "emotion": "serious"},
            {"expert": e2, "stance": gen_stance(e2, b2, r2, True), "emotion": "serious"}
        ], "clash_rounds": []
    }

def gen_round2(e1, e2, b1, b2, r1, r2):
    a1 = gen_attack(e1, e2, b1, b2, r1, 0)
    a2 = gen_attack(e2, e1, b2, b1, r2, 1)
    return {
        "round_number": 2, "topic": "相互质疑", "stances": [],
        "clash_rounds": [
            {"attacker": e1, "target": e2, **a1, "emotion": "passionate", "counter_emotion": "calm"},
            {"attacker": e2, "target": e1, **a2, "emotion": "skeptical", "counter_emotion": "firm"}
        ]
    }

def gen_round3(e1, e2, b1, b2, r1, r2):
    a1 = gen_attack(e1, e2, b1, b2, r1, 2)
    a2 = gen_attack(e2, e1, b2, b1, r2, 3)
    return {
        "round_number": 3, "topic": "深度交锋", "stances": [],
        "clash_rounds": [
            {"attacker": e1, "target": e2, **a1, "emotion": "intense", "counter_emotion": "thoughtful"},
            {"attacker": e2, "target": e1, **a2, "emotion": "provocative", "counter_emotion": "reflective"}
        ]
    }

def gen_round4(e1, e2, b1, b2, r1, r2):
    return {
        "round_number": 4, "topic": "认知升华", "stances": [
            {"expert": e1, "stance": gen_stance(e1, b1, r1, False), "emotion": "enlightened"},
            {"expert": e2, "stance": gen_stance(e2, b2, r2, False), "emotion": "enlightened"}
        ], "clash_rounds": []
    }

# ─── Generate all 100 JSONs ───
success = 0
failed = 0

for r in plan:
    rn = r["round"]
    e1, e2 = r["expert1"], r["expert2"]
    b1, b2 = r["belief1"], r["belief2"]
    s1 = EXPERT_STYLES.get(e1, {"role": "专家"})
    s2 = EXPERT_STYLES.get(e2, {"role": "专家"})
    r1, r2 = s1["role"], s2["role"]
    
    debate = {
        "title": f"Round {rn}: {e1} vs {e2}",
        "experts": [{"name": e1, "role": r1}, {"name": e2, "role": r2}],
        "rounds": [
            gen_round1(e1, e2, b1, b2, r1, r2),
            gen_round2(e1, e2, b1, b2, r1, r2),
            gen_round3(e1, e2, b1, b2, r1, r2),
            gen_round4(e1, e2, b1, b2, r1, r2)
        ]
    }
    
    fname = f'content/deep_training/round{rn}_{e1}_{e2}.json'
    try:
        json.dump(debate, open(fname, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        json.loads(open(fname, 'r', encoding='utf-8').read())  # verify
        success += 1
        if success % 20 == 0:
            print(f"  Generated {success}/100...")
    except Exception as ex:
        failed += 1
        print(f"  FAIL R{rn}: {ex}")

print(f"\nDone: {success} valid JSONs, {failed} failed")

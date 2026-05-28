# -*- coding: utf-8 -*-
"""Regenerate batch1 with clean JSON - no problematic quotes."""
import json

plan_data = json.loads(open('content/deep_training/batch20_1.json', 'r', encoding='utf-8').read())
rounds = plan_data['rounds']

for r in rounds:
    rn = r['round']
    e1 = r['expert1']
    e2 = r['expert2']
    b1 = r['belief1']
    b2 = r['belief2']
    topic = r['topic']
    
    debate = {
        "title": f"Round {rn}: {e1} vs {e2}",
        "experts": [
            {"name": e1, "role": "专家学者"},
            {"name": e2, "role": "专家学者"}
        ],
        "rounds": [
            {
                "round_number": 1,
                "topic": "立场阐述",
                "stances": [
                    {"expert": e1, "stance": f"我的核心观点很明确:{b1}。这不是一个理论问题,这是一个实践问题。{e2}说得有道理,但忽略了最关键的一点:世界的运行不是靠理想推动的,是靠规律推动的。", "emotion": "serious"},
                    {"expert": e2, "stance": f"恰恰相反。{b2}。{e1}所说的规律确实存在,但那只是表面现象。真正的驱动力在于更深层的东西。如果你只看表面规律,就会错失本质。", "emotion": "serious"}
                ],
                "clash_rounds": []
            },
            {
                "round_number": 2,
                "topic": "相互质疑",
                "stances": [],
                "clash_rounds": [
                    {
                        "attacker": e1, "target": e2,
                        "attack_type": "本质矛盾",
                        "attack_content": f"你说{b2},那我问你:当现实和你的理念冲突的时候,你选择遵从现实还是遵从理念?历史上多少惨剧,都是因为有人太相信自己的想法是对的,忽略了现实的规律。你的逻辑看起来很美,但经不起实践的检验。",
                        "counter_attack": f"你说的实践检验,本身就是一种预设了立场的实践。同样的数据,不同的人能得出不同的结论。问题不在于数据本身,而在于你用什么框架去解读。你所谓的规律,只是你愿意看到的那一部分。",
                        "emotion": "passionate",
                        "counter_emotion": "calm"
                    },
                    {
                        "attacker": e2, "target": e1,
                        "attack_type": "现实解构",
                        "attack_content": f"你刚才说{b1},那我问你一个简单的问题:你能举出一个完全脱离了你个人价值判断的客观规律吗?你所谓的规律,其实是你相信的一套叙事。真正的问题不是规律对不对,而是你为什么选择相信这个规律而不是那个。",
                        "counter_attack": f"好问题。但我不是在选择相信什么,我是在观察世界如何实际运转。你说我选择了一套叙事,那你呢?你拒绝相信规律本身,不就是你的叙事吗?每个人都有一套叙事,关键在于谁的叙事更接近真实世界的运行方式。",
                        "emotion": "skeptical",
                        "counter_emotion": "firm"
                    }
                ]
            },
            {
                "round_number": 3,
                "topic": "深度交锋",
                "stances": [],
                "clash_rounds": [
                    {
                        "attacker": e1, "target": e2,
                        "attack_type": "逻辑解构",
                        "attack_content": f"我们争了半天,其实核心分歧只有一点:你认为理念优先,我认为规律优先。但让我追问一句:如果你的理念和现实出现了不可调和的矛盾,你会改变你的理念吗?如果你不会,那么你的理念就不是追求真理的工具,而是逃避现实的借口。",
                        "counter_attack": f"我不会为了迎合现实而放弃理念。但我也不会无视现实。真正的智慧是在理念和现实之间找到平衡。你说规律优先,但历史上每一次真正的进步,都是有人拒绝接受现实规律的结果。奴隶制曾经是经济规律,废除它的时候,人们也說你不现实。",
                        "emotion": "intense",
                        "counter_emotion": "thoughtful"
                    },
                    {
                        "attacker": e2, "target": e1,
                        "attack_type": "反例证伪",
                        "attack_content": f"你说规律驱动世界,那爱呢?正义呢?牺牲呢?这些也是规律能解释的吗?一个母亲为孩子牺牲,一个士兵为战友挡子弹,这是哪条规律驱动的?世界不是只有你看到的那一种力量在起作用。",
                        "counter_attack": f"爱和牺牲不是反规律的,它们是进化规律的一部分。母亲对孩子的爱是基因为了延续自身而编程的。士兵的牺牲是群体选择的结果。你说这是超越规律,我说这是规律的高级表现形式。",
                        "emotion": "provocative",
                        "counter_emotion": "reflective"
                    }
                ]
            },
            {
                "round_number": 4,
                "topic": "认知升华",
                "stances": [
                    {"expert": e1, "stance": f"这场对话让我意识到:我过去可能太强调规律的决定性作用,忽略了人的主观能动性和价值选择的重要性。规律是骨架,但价值和理念是血肉。没有骨架不行,但只有骨架也不是一个完整的人。", "emotion": "enlightened"},
                    {"expert": e2, "stance": f"我也反思了自己的立场。理念确实重要,但不能脱离现实只谈理念。像{e1}说的,不考虑规律的理想主义容易变成空中楼阁。真正的智慧,大概是在坚持理念的同时,也尊重现实规律。", "emotion": "enlightened"}
                ],
                "clash_rounds": []
            }
        ]
    }
    
    fname = f'content/deep_training/round{rn}_{e1}_{e2}.json'
    json.dump(debate, open(fname, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    
    try:
        json.loads(open(fname, 'r', encoding='utf-8').read())
        print(f"  R{rn} {e1} vs {e2} OK")
    except json.JSONDecodeError as e:
        print(f"  R{rn} FAIL: {e}")

print("Done.")

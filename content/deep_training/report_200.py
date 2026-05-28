# -*- coding: utf-8 -*-
"""Consolidated report: 200 rounds total performance."""
import sys, os, json, glob, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Read all expert profiles for final versions
experts_dir = 'expert-library/experts'
final_versions = {}
for category in os.listdir(experts_dir):
    cat_path = os.path.join(experts_dir, category)
    if not os.path.isdir(cat_path): continue
    for f in os.listdir(cat_path):
        if not f.endswith('.md'): continue
        name = f.replace('.md','')
        content = open(os.path.join(cat_path, f), 'r', encoding='utf-8').read()
        import re
        vm = re.search(r'\*\*版本\*\*:\s*V(\d+)', content)
        tm = re.search(r'\*\*训练次数\*\*:\s*(\d+)', content)
        sm = re.search(r'\*\*当前评分\*\*:\s*([\d.]+)', content)
        final_versions[name] = {
            'v': int(vm.group(1)) if vm else 0,
            'trainings': int(tm.group(1)) if tm else 0,
            'score': float(sm.group(1)) if sm else 0
        }

# Historical baseline (before any of today's training)
baseline_v = {
    "孔子":19,"老子":27,"韩非子":19,"尼采":24,"马克思":9,"弗洛伊德":8,
    "阿伦特":16,"西蒙娜·德·波伏娃":15,"弗洛姆":29,"罗翔":16,
    "塔勒布":16,"丹尼尔·卡尼曼":28,"芒格":10,"巴菲特":21,"达利欧":13,
    "阿西莫夫":34,"尼克·博斯特罗姆":22,"凯文·凯利":36,"吴军":51,"刘润":43,
    "项飙":69,"许知远":10,"吴晓波":16,"万维钢":11,
    "柯林斯":16,"冯唐":57,"李诞":54,
    "菲利普·津巴多":4,"尤瓦尔·赫拉利":20,"丁元英":11,"芮小丹":6,
    "丹尼尔·戈尔曼":7
}

print(f"{'='*75}")
print(f"  200 轮深度训练全景报告")
print(f"{'='*75}")
print(f"\n{'─'*75}")
print(f"  {'专家':<14} {'起点':<6} {'终点':<6} {'+跳':<6} {'训练':<6} {'融合':<6} {'替换':<6} {'密度':<8}")
print(f"{'─'*75}")

# Training stats from this session
session_stats = {
    "孔子":(14+7,"孔子"),"老子":(20+6,"老子"),"韩非子":(24+6,"韩非子"),
    "尼采":(18+6,"尼采"),"马克思":(10+6,"马克思"),"弗洛伊德":(5+6,"弗洛伊德"),
    "阿伦特":(12+7,"阿伦特"),"西蒙娜·德·波伏娃":(10+6,"波伏娃"),"弗洛姆":(0+3,"弗洛姆"),
    "罗翔":(10+6,"罗翔"),"塔勒布":(8+6,"塔勒布"),"丹尼尔·卡尼曼":(2+6,"卡尼曼"),
    "芒格":(11+6,"芒格"),"巴菲特":(9+6,"巴菲特"),"达利欧":(12+6,"达利欧"),
    "阿西莫夫":(7+7,"阿西莫夫"),"尼克·博斯特罗姆":(6+6,"博斯特罗姆"),"凯文·凯利":(16+7,"凯文·凯利"),
    "吴军":(12+5,"吴军"),"刘润":(11+6,"刘润"),"项飙":(1+6,"项飙"),
    "许知远":(10+6,"许知远"),"吴晓波":(12+6,"吴晓波"),"万维钢":(12+7,"万维钢"),
    "柯林斯":(4+7,"柯林斯"),"冯唐":(12+7,"冯唐"),"李诞":(16+6,"李诞"),
    "菲利普·津巴多":(12+6,"津巴多"),"尤瓦尔·赫拉利":(11+6,"赫拉利"),
    "丁元英":(12+6,"丁元英"),"芮小丹":(12+7,"芮小丹"),"丹尼尔·戈尔曼":(10+5,"戈尔曼")
}

# Session replacements
session_repl = {
    "孔子":6+2,"老子":3+3,"韩非子":3+3,"尼采":4+2,"马克思":4+1,"弗洛伊德":5+1,
    "阿伦特":4+0,"西蒙娜·德·波伏娃":4+0,"弗洛姆":1+1,"罗翔":2+2,
    "塔勒布":6+0,"丹尼尔·卡尼曼":1+4,"芒格":5+0,"巴菲特":5+1,"达利欧":6+2,
    "阿西莫夫":3+3,"尼克·博斯特罗姆":5+3,"凯文·凯利":4+1,"吴军":5+0,"刘润":6+2,
    "项飙":0+1,"许知远":6+1,"吴晓波":5+0,"万维钢":6+7,
    "柯林斯":4+0,"冯唐":3+3,"李诞":2+0,
    "菲利普·津巴多":5+0,"尤瓦尔·赫拉利":6+3,"丁元英":4+1,"芮小丹":3+0,"丹尼尔·戈尔曼":6+5
}

for name in sorted(final_versions.keys(), key=lambda n: -(final_versions[n]['v'] - baseline_v.get(n,0))):
    fv = final_versions.get(name, {})
    cur_v = fv.get('v', 0)
    base = baseline_v.get(name, 0)
    jump = cur_v - base
    trainings = fv.get('trainings', 0)
    m = session_stats.get(name, (0,))[0]
    r = session_repl.get(name, 0)
    
    if jump <= 0: continue
    bar = '█' * min(jump, 30)
    print(f"  {name:<12} V{base:<3} V{cur_v:<3} +{jump:<3} {trainings:<4} {m:<5} {r:<5} {bar}")

print(f"\n{'='*75}")
top5 = sorted(final_versions.keys(), key=lambda n: -(final_versions[n]['v'] - baseline_v.get(n,0)))[:5]
print(f"  最大跨幅 Top 5:")
for n in top5:
    fv = final_versions[n]
    base = baseline_v.get(n, 0)
    print(f"    {n:12s}: V{base} → V{fv['v']} (+{fv['v']-base})")

print(f"\n  版本新高度:")
for n in sorted(final_versions.keys(), key=lambda n: -final_versions[n]['v'])[:10]:
    fv = final_versions[n]
    print(f"    {n:12s}: V{fv['v']} ({fv.get('score','?')}分, {fv.get('trainings','?')}次训练)")

print(f"\n{'='*75}")
print(f"  本批 100轮 详细反馈 (R231-R330)")
print(f"{'='*75}")
print("""
  99/100 处理成功, 1个JSON损坏(round264)
  
  融合分布:
    319 策略融合 (3.2/轮)
    52  素材替换  (0.5/轮)
    32/32 专家全部升级

  融合率排行:
    孔子 2.0/轮 · 芮小丹 2.0/轮 · 老子 2.0/轮 
    韩非子 2.0/轮 · 尼采 2.0/轮 · 马克思 2.0/轮
    吴晓波 2.0/轮 · 丁元英 2.0/轮 · 戈尔曼 2.0/轮

  饱和预警:
    卡尼曼 0.3/轮 → 极限，建议停止
    弗洛姆 0.5/轮 → 接近饱和
    项飙 0.7/轮 → 高位饱和

  本批最大赢家:
    芮小丹 V18→V25 (+7) - 小说角色达到专业级
    孔子 V41→V48 (+7) - 儒家思想持续完善
    万维钢 V27→V34 (+7) - 理工科思维武装完成
""")

# Find top jump experts
print(f"{'─'*75}")
print(f"  全局最终排名 (版本):")
print(f"{'─'*75}")
for name in sorted(final_versions.keys(), key=lambda n: -final_versions[n]['v']):
    fv = final_versions[name]
    base = baseline_v.get(name, 0)
    jump = fv['v'] - base
    print(f"  {name:<12} V{fv['v']:<3}  (+{jump:<2})  {fv.get('trainings',0):>3}次训练")

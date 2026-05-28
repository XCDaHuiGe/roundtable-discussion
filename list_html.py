# -*- coding: utf-8 -*-
import os
outputs = os.listdir('output')
htmls = [f for f in outputs if f.endswith('.html') and not f.startswith('test') and not f.startswith('example')]
htmls.sort(key=lambda x: os.path.getsize(os.path.join('output', x)))
for f in htmls:
    sz = os.path.getsize(os.path.join('output', f))
    print(f"{sz//1024:4d}KB  {f}")

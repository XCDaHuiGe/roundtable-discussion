import glob, json

LQ = chr(0x201c)
RQ = chr(0x201d)

for fname in [
    'content/deep_training/round266_项飙_弗洛伊德.json',
    'content/deep_training/round267_吴晓波_尼克_博斯特罗姆.json',
]:
    with open(fname, 'r', encoding='utf-8') as f:
        text = f.read()

    import re
    
    # CJK char followed by " followed by CJK char -> CJK LQ CJK
    text = re.sub(
        r'([\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])"([\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])',
        r'\1' + LQ + r'\2',
        text
    )
    
    # CJK char followed by " followed by punctuation/space -> CJK RQ punct
    text = re.sub(
        r'([\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])"([\s.,;:\u2014\u2013])',
        r'\1' + RQ + r'\2',
        text
    )
    
    # punctuation/space followed by " followed by CJK char -> punct LQ CJK
    text = re.sub(
        r'([\s.,;:\u2014\u2013])"([\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])',
        r'\1' + LQ + r'\2',
        text
    )

    # Verify JSON validity
    try:
        json.loads(text)
        print('VALID:', fname)
    except json.JSONDecodeError as e:
        print('INVALID:', fname, e)
        print('  Context:', repr(text[max(0,e.pos-30):e.pos+30]))
    
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(text)
        print('  Saved:', fname)

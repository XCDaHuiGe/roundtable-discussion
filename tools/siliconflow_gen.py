import requests, base64, sys, os

def _load():
    d = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    k = os.path.join(d, ".sf_key")
    with open(k) as f:
        return f.read().strip()

_key = _load()
_url = "https://api.siliconflow.cn/v1/images/generations"

def gen(prompt, size="1024x1024", output="output/test.png"):
    h = {"Authorization": "Bearer " + _key, "Content-Type": "application/json"}
    d = {"model": "Kwai-Kolors/Kolors", "prompt": prompt, "image_size": size}
    r = requests.post(_url, headers=h, json=d, timeout=120)
    if r.status_code == 200:
        imgs = r.json().get("images", [])
        if imgs:
            img = requests.get(imgs[0]["url"], timeout=60)
            if img.status_code == 200:
                os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
                with open(output, "wb") as f:
                    f.write(img.content)
                print("OK:", output, len(img.content), "bytes")
                return base64.b64encode(img.content).decode()
    else:
        print("ERR:", r.text[:200])
    return None

if __name__ == "__main__":
    gen(sys.argv[1], sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else gen(sys.argv[1])

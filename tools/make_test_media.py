#!/usr/bin/env python3
"""Create the still images used for melt test renders and README previews."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = os.path.join(os.path.dirname(__file__), "testmedia")
W, H = 1920, 1080
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def grad(c1, c2, w=W, h=H, diag=True):
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        for x in range(0, w):
            t = ((x / w) + (y / h)) / 2 if diag else y / h
            px[x, y] = tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
    return im


def clip_a():
    im = grad((255, 94, 58), (122, 40, 203)).resize((W, H))
    d = ImageDraw.Draw(im)
    for x in range(0, W, 120):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255), width=2)
    for y in range(0, H, 120):
        d.line([(0, y), (W, y)], fill=(255, 255, 255), width=2)
    f = ImageFont.truetype(BOLD, 220)
    d.text((W / 2, H / 2 - 40), "OUZ LABS", font=f, anchor="mm", fill="white", stroke_width=8, stroke_fill="black")
    d.text((W / 2, H / 2 + 150), "clip A", font=ImageFont.truetype(BOLD, 80), anchor="mm", fill="white")
    return im


def clip_b():
    im = grad((20, 200, 170), (10, 60, 120))
    d = ImageDraw.Draw(im)
    for i in range(12):
        d.ellipse([i * 170 - 60, 700 - (i % 3) * 120, i * 170 + 140, 900 - (i % 3) * 120], fill=(255, 255, 255, 60), outline="white", width=4)
    d.text((W / 2, H / 2 - 80), "clip B", font=ImageFont.truetype(BOLD, 200), anchor="mm", fill="white", stroke_width=6, stroke_fill="black")
    return im


def screen():
    im = Image.new("RGB", (W, H), (30, 30, 36))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 60], fill=(48, 48, 56))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([24 + i * 40, 18, 48 + i * 40, 42], fill=c)
    d.rectangle([0, 60, 360, H], fill=(37, 37, 44))
    mono = ImageFont.truetype(MONO, 34)
    for i, n in enumerate(["agent.py", "ghost.py", "tinder.py", "README.md", "evals/"]):
        d.text((30, 100 + i * 56), n, font=mono, fill=(200, 200, 210))
    code = ["from ollama import chat", "", "def ghost_reply(msg):", "    # toxic alpha mode", "    resp = chat(model='llama3',",
            "        messages=[{'role': 'user',", "                   'content': msg}])", "    return resp.message.content", "",
            "for girl in ['Roxy', 'Gemma', 'Clara']:", "    print(ghost_reply(f'hi {girl}'))"]
    cols = [(198, 120, 221), (230, 230, 230), (97, 175, 239), (127, 132, 142), (229, 192, 123)]
    for i, line in enumerate(code):
        d.text((420, 110 + i * 58), f"{i + 1:>2}  " + line, font=mono, fill=cols[i % len(cols)])
    d.rectangle([1200, 760, 1880, 1040], fill=(20, 20, 24), outline=(80, 80, 90), width=2)
    d.text((1220, 780), "$ python agent.py\nGhost: hey Clara ;)", font=mono, fill=(39, 201, 63))
    return im


def background():
    im = grad((14, 18, 40), (60, 20, 80))
    return im.filter(ImageFilter.GaussianBlur(4))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for n, fn in [("a", clip_a), ("b", clip_b), ("screen", screen), ("bg", background)]:
        fn().save(os.path.join(OUT, n + ".png"))
    print("ok")

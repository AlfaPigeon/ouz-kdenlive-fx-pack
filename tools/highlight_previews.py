#!/usr/bin/env python3
"""README previews for the Highlights pack: one animated GIF per group (In -> Loop -> Out over a
test still) + a static sheet of the label title templates. Output: docs/previews/highlights_*.gif|jpg"""
import os, subprocess, sys, tempfile
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_highlights as MH

ROOT = MH.ROOT
OUT = os.path.join(ROOT, "docs", "previews")
T = 240   # tile size
BG = Image.open(os.path.join(ROOT, "tools", "testmedia", "screen.png")).convert("RGB").resize((1920, 1080))
BGT = BG.crop((420, 0, 1500, 1080)).resize((T, T), Image.LANCZOS)

def frames(path):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", path, "-vf", f"scale={T}:{T}:flags=area",
                                   "-f", "rawvideo", "-pix_fmt", "rgba", "-"])
    return list(np.frombuffer(raw, np.uint8).reshape(-1, T, T, 4))

def sequence(A, color):
    d = os.path.join(MH.OUT, "1080", A.group)
    if A.single:
        f = frames(os.path.join(d, f"ouzfx_hl_{A.name}_{color}.webm"))
        return f + f + [np.zeros_like(f[0])] * 10
    fin = frames(os.path.join(d, f"ouzfx_hl_{A.name}_in_{color}.webm"))
    fout = frames(os.path.join(d, f"ouzfx_hl_{A.name}_out_{color}.webm"))
    return fin[:A.intro + 36] + fout + [np.zeros_like(fin[0])] * 10

def comp(fr):
    im = Image.fromarray(fr, "RGBA")
    out = BGT.copy(); out.paste(im, (0, 0), im)
    return out

def gif(name, items, cols=3):
    seqs = [sequence(A, c) for A, c in items]
    n = max(len(s) for s in seqs)
    rows = (len(seqs) + cols - 1) // cols
    tmp = tempfile.mkdtemp()
    for i in range(0, n, 2):     # 15 fps preview
        W = Image.new("RGB", (cols * T + (cols - 1) * 4, rows * T + (rows - 1) * 4), (20, 22, 25))
        for j, s in enumerate(seqs):
            fr = s[min(i, len(s) - 1)]
            W.paste(comp(fr), ((j % cols) * (T + 4), (j // cols) * (T + 4)))
        W.save(os.path.join(tmp, f"{i // 2:04d}.png"))
    out = os.path.join(OUT, f"highlights_{name}.gif")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "15", "-i", os.path.join(tmp, "%04d.png"), "-vf",
                    "split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                    out], check=True)
    print(out, os.path.getsize(out) // 1024, "KB")

def main():
    os.makedirs(OUT, exist_ok=True)
    by = {A.name: A for A in MH.ASSETS}
    g = lambda *names, color=None: [(by[n], color or by[n].colors[0]) for n in names]
    gif("arrows", g("arrow_right", "arrow_left", "arrow_curved_down_right", "arrow_down", "arrow_up", "arrow_curved_down_left"))
    gif("boxes", g("box_draw_16x9", "box_pop_16x9", "focus_brackets", "box_draw_1x1", "box_draw_wide") + [(by["box_draw_16x9"], "volt")])
    gif("circles", g("circle_draw", "circle_pop", "ellipse_draw", "pulse_ring", "scribble_circle") + [(by["circle_draw"], "chalk")])
    gif("marks", g("underline_swipe", "check_draw", "cross_draw", "ping_dot", "click_ripple") + [(by["check_draw"], "volt")])
    gif("badges", g("step_badge_01", "step_badge_02", "step_badge_03", "new_sticker"), cols=4)

if __name__ == "__main__":
    main()

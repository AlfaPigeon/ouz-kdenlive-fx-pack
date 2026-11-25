#!/usr/bin/env python3
"""Generate the editable OuzFX Highlights title templates (.kdenlivetitle).

One set per profile (1080p, 4k, vertical) because Kdenlive titles are authored at
project resolution. Text items are positioned from the *rendered* ink box, measured
with melt (kdenlivetitle producer), so labels sit optically centred in their tags.
Requires melt + the brand fonts installed (fonts/ or ./install.sh --fonts).

    python3 tools/make_titles.py
"""
import json, os, subprocess, sys, tempfile, math
from xml.sax.saxutils import escape
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brand

ROOT = brand.ROOT
OUT = os.path.join(ROOT, "titles")
CACHE = os.path.join(ROOT, "tools", "title_metrics.json")
PROFILES = {"1080p": (1920, 1080, "atsc_1080p_30"), "4k": (3840, 2160, "uhd_2160p_30"), "vertical": (1080, 1920, None)}
# MLT's kdenlivetitle producer reads font-weight on the legacy Qt5 scale (50 = normal)
QT5_WEIGHT = {500: 57, 600: 63, 700: 75, 800: 81}
DUR = 150   # 5 s @ 30 fps

def col(name, a=255):
    return "%d,%d,%d,%d" % (brand.rgb(name) + (a,))

NONE = "0,0,0,0"

# ------------------------------------------------------------------ measuring
_metrics = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

def text_xml(x, y, text, role, px, color, spacing=0, z=10, rot=0.0, box_w=None, align=1):
    """align: 1 = left, 4 = centre (Qt::AlignHCenter) inside box_w"""
    fam, _, _, css = brand.FONTS[role]
    m = matrix(rot)
    box = f'box-width="{box_w:.2f}" box-height="{px * 1.35:.2f}" ' if box_w else ""
    return (f' <item z-index="{z}" type="QGraphicsTextItem">\n'
            f'  <position x="{x:.2f}" y="{y:.2f}">\n   <transform rotation="{rot:g}" zoom="100">{m}</transform>\n  </position>\n'
            f'  <content font-color="{col(color)}" font-outline-color="{NONE}" font-pixel-size="{int(px)}" '
            f'font-italic="0" font-underline="0" font-weight="{QT5_WEIGHT[css]}" font="{fam}" font-outline="0" '
            f'font-spacing="{int(spacing)}" letter-spacing="{int(spacing)}" alignment="{align}" {box}line-spacing="0" tab-width="80" '
            f'typewriter="0;2;1;0;0">{escape(text)}</content>\n </item>\n')

def matrix(rot):
    a = math.radians(rot); c, s = math.cos(a), math.sin(a)
    return f"{c:.6f},{s:.6f},0,{-s:.6f},{c:.6f},0,0,0,1"

def rect_xml(x, y, w, h, pen=NONE, penw=0, brush=NONE, radius=0, z=1, rot=0.0, ellipse=False):
    t = "QGraphicsEllipseItem" if ellipse else "QGraphicsRectItem"
    rr = "" if ellipse else f' cornerRadius="{radius:g}"'
    return (f' <item z-index="{z}" type="{t}">\n'
            f'  <position x="{x:.2f}" y="{y:.2f}">\n   <transform rotation="{rot:g}" zoom="100">{matrix(rot)}</transform>\n  </position>\n'
            f'  <content pencolor="{pen}" rect="0,0,{w:.2f},{h:.2f}" penwidth="{penw:g}" brushcolor="{brush}"{rr}/>\n </item>\n')

def doc(W, H, items):
    return (f'<kdenlivetitle width="{W}" height="{H}" out="{DUR - 1}">\n' + "".join(items) +
            f' <startviewport rect="0,0,{W},{H}"/>\n <endviewport rect="0,0,{W},{H}"/>\n <background color="0,0,0,0"/>\n</kdenlivetitle>\n')

def render(xml, W, H):
    with tempfile.TemporaryDirectory() as d:
        t = os.path.join(d, "t.kdenlivetitle"); open(t, "w").write(xml)
        png = os.path.join(d, "t.png")
        prof = {(1920, 1080): "atsc_1080p_30", (3840, 2160): "uhd_2160p_30", (1080, 1920): "vertical_hd_30"}[(W, H)]
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        subprocess.run(["melt", "-profile", prof, t, "in=0", "out=0", "-consumer", f"avformat:{png}",
                        "vcodec=png", "pix_fmt=rgba", "frames=1", "update=1"], env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return np.array(Image.open(png).convert("RGBA"))

def ink(text, role, px, spacing):
    """ink box (dx, dy, w, h) of a text item relative to its position"""
    key = f"{text}|{role}|{px}|{spacing}"
    if key not in _metrics:
        x0, y0 = 100, 100
        a = render(doc(1920, 1080, [text_xml(x0, y0, text, role, px, "slate", spacing)]), 1920, 1080)
        ys, xs = np.where(a[..., 3] > 40)
        _metrics[key] = [int(xs.min() - x0), int(ys.min() - y0), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)]
        json.dump(_metrics, open(CACHE, "w"), indent=0, sort_keys=True)
    return _metrics[key]

def text_centered(cx, cy, text, role, px, color, spacing=0, z=10, rot=0.0, box_w=None, sample=None):
    """Centre text on (cx, cy). With box_w the item is a centred box (alignment=4), so any
    replacement text (template %s) stays centred; vertical centre comes from the sample's ink."""
    dx, dy, w, h = ink(sample or text, role, px, spacing)
    if box_w:
        lx, ly = box_w / 2, dy + h / 2
        a = math.radians(rot); c, s = math.cos(a), math.sin(a)
        rx, ry = lx * c - ly * s, lx * s + ly * c
        return text_xml(cx - rx, cy - ry, text, role, px, color, spacing, z, rot, box_w, 4), w, h
    lx, ly = dx + w / 2, dy + h / 2          # local ink centre
    a = math.radians(rot); c, s = math.cos(a), math.sin(a)
    rx, ry = lx * c - ly * s, lx * s + ly * c
    return text_xml(cx - rx, cy - ry, text, role, px, color, spacing, z, rot), w, h

def rrect_centered(cx, cy, w, h, rot=0.0, **kw):
    a = math.radians(rot); c, s = math.cos(a), math.sin(a)
    lx, ly = w / 2, h / 2
    return rect_xml(cx - (lx * c - ly * s), cy - (lx * s + ly * c), w, h, rot=rot, **kw)

# ------------------------------------------------------------------ templates
TAG_STYLES = {   # bg, text
    "tangerine": ("tangerine", "slate"),
    "volt": ("volt", "slate"),
    "cobalt": ("cobalt", "chalk"),
    "slate": ("slate", "chalk"),
    "chalk": ("chalk", "slate"),
}

TAG_CHARS = 10   # tag pill fits this many JetBrains Mono characters

def tag(cx, cy, k, style, text="%s", anchor="center"):
    """JetBrains Mono 'lab tag': filled 16px-radius pill, label text = template text (%s)."""
    bg, fg = TAG_STYLES[style]
    px, sp = int(40 * k), int(2 * k)
    cap = ink("LABEL", "mono", px, sp)[3]
    w = ink("W" * TAG_CHARS, "mono", px, sp)[2]
    tw, th = w + 64 * k, cap + 40 * k
    if anchor == "bottomleft":
        cx, cy = cx + tw / 2, cy - th / 2
    items = [rrect_centered(cx, cy, tw, th, brush=col(bg), radius=brand.CORNER_RADIUS * k, z=5)]
    t, _, _ = text_centered(cx, cy, text, "mono", px, fg, sp, z=10, box_w=tw, sample="LABEL")
    items.append(t)
    return items, tw, th

BOX_W, BOX_H = 880, 495     # matches highlights box_draw_16x9 at 1:1 in 1080p/vertical

def templates(W, H):
    k = min(W, H) / 1080
    cx, cy = W / 2, H / 2
    T = {}
    for st in ("tangerine", "volt", "cobalt", "slate"):
        items, _, _ = tag(cx, cy, k, st)
        T[f"ouzfx_tag_{st}"] = (f"OuzFX Tag {st.title()}", items)
    S = brand.STROKE * k
    for st in ("tangerine", "volt", "chalk"):
        bx, by = cx - BOX_W * k / 2, cy - BOX_H * k / 2
        items, _, _ = tag(bx - S / 2, by - S / 2 - 12 * k, k, st, anchor="bottomleft")
        T[f"ouzfx_box_tag_{st}"] = (f"OuzFX Box Tag {st.title()} (pairs with box_draw_16x9)", items)
        box = rect_xml(bx, by, BOX_W * k, BOX_H * k, pen=col(st), penw=S, radius=brand.CORNER_RADIUS * k, z=1)
        T[f"ouzfx_box_label_{st}"] = (f"OuzFX Box + Label {st.title()}", [box] + items)
    R = 300 * k
    it, _, th = tag(cx, cy + R + S / 2 + 24 * k + (40 * k + ink("LABEL", "mono", int(40 * k), int(2 * k))[3]) / 2, k, "tangerine")
    T["ouzfx_circle_label_tangerine"] = ("OuzFX Circle + Label Tangerine",
                                         [rect_xml(cx - R, cy - R, 2 * R, 2 * R, pen=col("tangerine"), penw=S, ellipse=True, z=1)] + it)
    # step badge
    r = 66 * k; o = brand.STICKER_OUTLINE * k
    t, _, _ = text_centered(cx, cy, "%s", "mono", int(64 * k), "slate", int(-1 * k), box_w=2 * r, sample="01")
    T["ouzfx_step_badge"] = ("OuzFX Step Badge (edit number)",
                             [rect_xml(cx - r - o / 2, cy - r - o / 2, 2 * r + o, 2 * r + o, pen=col("chalk"), penw=o, brush=col("tangerine"), ellipse=True, z=1), t])
    # NEW sticker (rotated -8 deg like the brand's sticker cutouts)
    rot = -8
    sw, sh = 330 * k, 150 * k
    t, _, _ = text_centered(cx, cy, "%s", "display", int(110 * k), "slate", int(110 * k * brand.TRACKING), rot=rot,
                            box_w=sw, sample="NEW")
    T["ouzfx_sticker_new"] = ("OuzFX Sticker NEW (edit word)",
                              [rrect_centered(cx, cy, sw, sh, rot=rot, pen=col("chalk"), penw=2 * o, brush=col("volt"), radius=24 * k, z=1), t])
    # corner lab tag (top-left): slate pill, volt LED, mono label
    m = 64 * k
    txt = "EXP 01 // HIGHLIGHTS"     # sample; pill fits ~22 characters
    px = int(30 * k)
    dx, dy, w, h = ink("W" * 22, "mono", px, int(1 * k))
    capH = ink("EXP", "mono", px, int(1 * k))[3]
    ph = capH + 34 * k; led = 14 * k
    pw = w + 3 * 22 * k + led
    x0, y0 = m, m
    tx0 = x0 + 22 * k + led + 18 * k
    sdx, sdy, sw_, sh_ = ink(txt, "mono", px, int(1 * k))
    t = text_xml(tx0, y0 + ph / 2 - (sdy + sh_ / 2), "%s", "mono", px, "chalk", int(1 * k), box_w=w + 8 * k, align=1)
    T["ouzfx_lab_tag_corner"] = ("OuzFX Lab Tag Corner (series label)",
                                 [rect_xml(x0, y0, pw, ph, brush=col("slate"), radius=brand.CORNER_RADIUS * k, z=1),
                                  rect_xml(x0 + 22 * k, y0 + ph / 2 - led / 2, led, led, brush=col("volt"), ellipse=True, z=2), t])
    # callout note panel
    pw, ph = 820 * k, 190 * k
    px0, py0 = cx - pw / 2, cy - ph / 2
    kick = ink("NOTE", "mono", int(26 * k), int(2 * k))
    body = ink("Callout text goes here", "body", int(46 * k), 0)
    items = [rect_xml(px0, py0, pw, ph, brush=col("slate"), radius=brand.CORNER_RADIUS * k, z=1),
             rect_xml(px0 + 26 * k, py0 + 30 * k, 10 * k, ph - 60 * k, brush=col("tangerine"), radius=5 * k, z=2)]
    tx = px0 + 66 * k
    t1, _, _ = text_centered(tx + kick[2] / 2, py0 + 48 * k + kick[3] / 2, "NOTE", "mono", int(26 * k), "tangerine", int(2 * k))
    # body = template text, left aligned in the panel
    t2 = text_xml(tx, py0 + 104 * k - body[1], "%s", "body", int(46 * k), "chalk", 0, box_w=pw - 66 * k - 34 * k, align=1)
    T["ouzfx_callout_note"] = ("OuzFX Callout Note", items + [t1, t2])
    return T

def main():
    index = {}
    for prof, (W, H, _) in PROFILES.items():
        d = os.path.join(OUT, prof); os.makedirs(d, exist_ok=True)
        for fn, (label, items) in templates(W, H).items():
            open(os.path.join(d, fn + ".kdenlivetitle"), "w").write(doc(W, H, items))
            index[fn] = label
        print(prof, len(templates(W, H)), "titles")
    json.dump(index, open(os.path.join(OUT, "index.json"), "w"), indent=1)

if __name__ == "__main__":
    main()

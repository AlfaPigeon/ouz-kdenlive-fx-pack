#!/usr/bin/env python3
"""Generate the OuzFX Highlights overlay clips (alpha WebM VP9, 30 fps, square).

Every asset is rendered procedurally with cairocffi (+ PIL for brand text) so the
pack is fully reproducible:

    python3 tools/make_highlights.py                 # 1080 + 2160, all assets
    python3 tools/make_highlights.py --size 1080     # one size
    python3 tools/make_highlights.py --only arrow    # assets whose name contains 'arrow'
    python3 tools/make_highlights.py --prores        # also write ProRes 4444 .mov fallbacks

Canvas is square (1080x1080 or 2160x2160) so the same clip works in landscape and
vertical projects. The point of interest (arrow tip / shape centre) is always the
canvas centre.

Clip phases (all seamless with each other):
  _in    intro animation + one 2 s idle cycle (ends in the rest pose)
  _loop  2 s seamless idle loop (repeat to extend)
  _out   exit animation starting from the rest pose
"""
import argparse, math, os, subprocess, sys
from multiprocessing import Pool

import numpy as np
import cairocffi as cairo
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brand

ROOT = brand.ROOT
OUT = os.path.join(ROOT, "highlights")
FPS = 30
LOOP = 60            # idle period (frames)
TAU = 2 * math.pi

CORE = ["tangerine", "volt", "chalk"]
TANGERINE = ["tangerine"]

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ease_out(t):  return 1 - (1 - clamp(t)) ** 3
def ease_in(t):   return clamp(t) ** 3
def ease_io(t):
    t = clamp(t); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def smooth(t):
    t = clamp(t); return t * t * (3 - 2 * t)

def keys(t, kf):
    """piecewise smoothstep through [(t, v), ...]"""
    if t <= kf[0][0]: return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * smooth((t - t0) / (t1 - t0))
    return kf[-1][1]

POP_IN = [(0, .55), (.55, 1.08), (.8, .985), (1, 1.0)]       # elastic pop
POP_OUT = [(0, 1.0), (.3, 1.06), (1, .55)]                  # anticipate + shrink

# ---------------------------------------------------------------- geometry
class Poly:
    def __init__(self, pts):
        self.p = np.asarray(pts, float)
        d = np.r_[0, np.cumsum(np.hypot(*np.diff(self.p, axis=0).T))]
        self.cum = d
        self.L = d[-1]

    def at(self, s):
        s = clamp(s, 0, self.L)
        i = int(np.searchsorted(self.cum, s))
        if i <= 0: return self.p[0]
        t = (s - self.cum[i - 1]) / max(1e-9, self.cum[i] - self.cum[i - 1])
        return self.p[i - 1] + (self.p[i] - self.p[i - 1]) * t

    def sub(self, a, b):
        """points between fractions a..b"""
        sa, sb = clamp(a) * self.L, clamp(b) * self.L
        if sb - sa < 1e-6: return None
        inner = self.p[(self.cum > sa) & (self.cum < sb)]
        return np.vstack([self.at(sa), inner, self.at(sb)])

    def tangent(self, frac):
        s = clamp(frac) * self.L
        a, b = self.at(max(0, s - 2)), self.at(min(self.L, s + 2))
        v = b - a
        n = np.hypot(*v)
        return v / n if n else np.array([1.0, 0])

def stroke_pts(ctx, pts, close=False):
    if pts is None or len(pts) < 2: return
    ctx.move_to(*pts[0])
    for q in pts[1:]: ctx.line_to(*q)
    if close: ctx.close_path()
    ctx.stroke()

def bezier(p0, p1, p2, p3, n=200):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = map(np.asarray, (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3

def rrect_pts(cx, cy, w, h, r, n=10):
    """rounded-rect perimeter, clockwise, starting top-left (just after corner)."""
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    pts = []
    corners = [((x1 - r, y0 + r), -90), ((x1 - r, y1 - r), 0), ((x0 + r, y1 - r), 90), ((x0 + r, y0 + r), 180)]
    pts.append((x0 + r, y0))
    for (ccx, ccy), a0 in corners:
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    pts.append((x0 + r, y0))
    return pts

def ellipse_pts(cx, cy, rx, ry, start=-100, turns=1.0, n=360, wobble=None):
    pts = []
    m = int(n * turns)
    for i in range(m + 1):
        a = math.radians(start) + TAU * turns * i / m
        k = 1 + (wobble(i / m) if wobble else 0)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return pts

def noise_fn(seed, amp, freqs=(2, 3, 5)):
    rng = np.random.RandomState(seed)
    ph = rng.uniform(0, TAU, len(freqs))
    am = rng.uniform(.4, 1, len(freqs))
    def f(t):
        return amp * sum(a * math.sin(TAU * fr * t + p) for a, fr, p in zip(am, freqs, ph)) / len(freqs)
    return f

def jitter(pts, seed, amp):
    """perpendicular smooth wobble for a hand-drawn look"""
    P = np.asarray(pts, float)
    if amp <= 0: return P
    n = noise_fn(seed, amp)
    d = np.gradient(P, axis=0)
    nn = np.hypot(d[:, 0], d[:, 1])[:, None]
    nn[nn == 0] = 1
    perp = np.c_[-d[:, 1], d[:, 0]] / nn
    t = np.linspace(0, 1, len(P))
    return P + perp * np.array([n(x) for x in t])[:, None]

def rot(v, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([v[0] * c - v[1] * s, v[0] * s + v[1] * c])

# ---------------------------------------------------------------- text sprites
_TEXT_CACHE = {}
def text_sprite(text, role, px, color, tracking=0.0):
    """PIL-rendered text -> premultiplied cairo surface (cached)."""
    key = (text, role, px, color, tracking)
    if key in _TEXT_CACHE: return _TEXT_CACHE[key]
    f = ImageFont.truetype(brand.font_path(role), px)
    f.set_variation_by_name(brand.FONTS[role][2])
    # manual tracking
    widths = [f.getlength(ch) for ch in text]
    total = sum(widths) + tracking * px * (len(text) - 1)
    asc, desc = f.getmetrics()
    W, H = int(total + px), int(asc + desc + px * .5)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = px / 2
    for ch, w in zip(text, widths):
        d.text((x, px * .25), ch, font=f, fill=brand.rgb(color) + (255,))
        x += w + tracking * px
    bb = im.getbbox()
    im = im.crop(bb)
    a = np.asarray(im, np.float32) / 255.0
    pm = a[..., :3] * a[..., 3:4]
    bgra = np.dstack([pm[..., 2], pm[..., 1], pm[..., 0], a[..., 3]])
    buf = np.ascontiguousarray((bgra * 255 + .5).astype(np.uint8))
    s = cairo.ImageSurface.create_for_data(bytearray(buf.tobytes()), cairo.FORMAT_ARGB32, im.width, im.height, im.width * 4)
    _TEXT_CACHE[key] = s
    return s

def paint_sprite(ctx, s, cx, cy, alpha=1.0):
    ctx.save()
    ctx.set_source_surface(s, cx - s.get_width() / 2, cy - s.get_height() / 2)
    ctx.paint_with_alpha(alpha)
    ctx.restore()

# ---------------------------------------------------------------- assets
# Each asset: draw(ctx, S, k, phase, f, color) where phase in {"intro","idle","out"}.
# intro frames = A.intro, idle cycle = LOOP, out frames = A.out.

class Asset:
    def __init__(self, name, group, colors, intro, out, draw, single=False, desc=""):
        self.name, self.group, self.colors = name, group, colors
        self.intro, self.out, self.draw, self.single, self.desc = intro, out, draw, single, desc

ASSETS = []
def asset(name, group, colors, intro=14, out=9, single=False, desc=""):
    def deco(fn):
        ASSETS.append(Asset(name, group, colors, intro, out, fn, single, desc)); return fn
    return deco

def setup(ctx, color, w, alpha=1.0):
    r, g, b = brand.rgbf(color)
    ctx.set_source_rgba(r, g, b, alpha)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

def breathe(f, amt=.015):
    return 1 + amt * math.sin(TAU * f / LOOP) if f is not None else 1

def boil_seed(f):
    """hand-drawn 'boil': 3 drawings cycling every 4 frames (seamless over 60f)"""
    return (f // 4) % 3

# -- straight arrows ---------------------------------------------------------
DIRS = {"right": (1, 0), "left": (-1, 0), "down": (0, 1), "up": (0, -1)}

def make_straight(dname, d):
    d = np.array(d, float)
    @asset(f"arrow_{dname}", "arrows", CORE, intro=13, out=9,
           desc=f"straight arrow pointing {dname} (tip = clip centre), draw-on + nudge")
    def draw(ctx, S, k, phase, f, color):
        c = np.array([S / 2, S / 2])
        L, hl = 300 * k, 64 * k
        tip_rest = c - d * 6 * k
        off, p, alpha = 0.0, 1.0, 1.0
        if phase == "intro":
            t = f / (13 - 1)
            p = ease_out(t)
            off = -110 * k * (1 - ease_out(t))
        elif phase == "idle":
            off = 18 * k * max(0.0, math.sin(TAU * 2 * f / LOOP)) ** 2
        else:
            t = f / (9 - 1)
            off = -170 * k * ease_in(t)
            alpha = 1 - ease_in(t)
        tip = tip_rest + d * off
        tail = tip - d * L
        end = tail + d * L * p
        setup(ctx, color, brand.STROKE * k * 1.1, alpha)
        stroke_pts(ctx, [tail, end])
        hs = clamp((p - .45) / .55)
        if hs > 0:
            h = hl * keys(hs, [(0, 0), (.7, 1.12), (1, 1)])
            stroke_pts(ctx, [end + rot(-d, 38) * h, end, end + rot(-d, -38) * h])
    return draw

for _n, _d in DIRS.items():
    make_straight(_n, _d)

# -- curved hand-drawn arrows -------------------------------------------------
def make_curved(dname, mirror):
    @asset(f"arrow_curved_{dname}", "arrows", CORE, intro=16, out=10,
           desc=f"hand-drawn curved arrow pointing {dname.replace('_', '-')} (tip = clip centre)")
    def draw(ctx, S, k, phase, f, color):
        cx = cy = S / 2
        sx = -1 if mirror else 1
        seed = boil_seed(f) if phase == "idle" else 0
        P = lambda x, y: (cx + sx * x * k, cy + y * k)
        pts = bezier(P(-360, -260), P(-150, -360), P(20, -190), P(-8, -14), 220)
        pts = jitter(pts, 11 + seed, 4.5 * k)
        poly = Poly(pts)
        a, b, alpha, off = 0.0, 1.0, 1.0, np.zeros(2)
        if phase == "intro":
            b = ease_out(f / 11)
        elif phase == "idle":
            pass
        else:
            t = f / 9
            a = ease_in(t)
        tan = poly.tangent(.995)
        if phase == "idle":
            off = tan * 10 * k * math.sin(TAU * f / LOOP)
        ctx.save(); ctx.translate(*off)
        setup(ctx, color, brand.STROKE * k, alpha)
        stroke_pts(ctx, poly.sub(a, b))
        # head draws after shaft (frames 11-15 of intro)
        hp = 1.0
        if phase == "intro": hp = ease_out((f - 10) / 5)
        if phase == "out": hp = 1 - ease_in((f - 4) / 5)
        if hp > 0:
            tip = poly.p[-1]
            hl = 62 * k
            l1 = Poly(jitter([tip + rot(-tan, 36 + 3 * seed) * hl, tip], 5 + seed, 2 * k))
            l2 = Poly(jitter([tip, tip + rot(-tan, -40) * hl * .95], 7 + seed, 2 * k))
            stroke_pts(ctx, l1.sub(1 - hp, 1))
            stroke_pts(ctx, l2.sub(0, hp))
        ctx.restore()
    return draw

make_curved("down_right", False)
make_curved("down_left", True)

# -- outline boxes ------------------------------------------------------------
def make_box_draw(name, w, h, colors):
    @asset(name, "boxes", colors, intro=15, out=10,
           desc=f"rounded outline box {w}x{h} (1080 ref), stroke draw-on")
    def draw(ctx, S, k, phase, f, color):
        s = breathe(f) if phase == "idle" else 1.0
        poly = Poly(rrect_pts(S / 2, S / 2, w * k * s, h * k * s, brand.CORNER_RADIUS * k))
        a, b = 0.0, 1.0
        if phase == "intro": b = ease_out(f / 14)
        if phase == "out": a = ease_in(f / 9)
        setup(ctx, color, brand.STROKE * k)
        stroke_pts(ctx, poly.sub(a, b), close=(a == 0 and b >= 1))
    return draw

make_box_draw("box_draw_16x9", 880, 495, CORE)
make_box_draw("box_draw_1x1", 560, 560, TANGERINE)
make_box_draw("box_draw_wide", 900, 260, TANGERINE)

def pop_state(phase, f, n_in, n_out):
    if phase == "intro":
        t = f / (n_in - 1); return keys(t, POP_IN), clamp(t * 3)
    if phase == "out":
        t = f / (n_out - 1); return keys(t, POP_OUT), 1 - ease_in(clamp((t - .2) / .8))
    return breathe(f), 1.0

@asset("box_pop_16x9", "boxes", TANGERINE, intro=11, out=8, desc="rounded outline box 16:9, elastic scale-pop")
def box_pop(ctx, S, k, phase, f, color):
    s, al = pop_state(phase, f, 11, 8)
    poly = Poly(rrect_pts(S / 2, S / 2, 880 * k * s, 495 * k * s, brand.CORNER_RADIUS * k))
    setup(ctx, color, brand.STROKE * k, al)
    stroke_pts(ctx, poly.p, close=True)

@asset("focus_brackets", "boxes", CORE, intro=11, out=8, desc="4 corner brackets snap in around a 16:9 area")
def brackets(ctx, S, k, phase, f, color):
    al = 1.0
    if phase == "intro":
        t = f / 10; s = keys(t, [(0, 1.45), (.6, .96), (.85, 1.01), (1, 1)]); al = clamp(t * 3)
    elif phase == "out":
        t = f / 7; s = 1 + .35 * ease_in(t); al = 1 - ease_in(t)
    else:
        s = 1 + .02 * math.sin(TAU * f / LOOP)
    cx = cy = S / 2
    hw, hh, arm, r = 440 * k * s, 248 * k * s, 92 * k, brand.CORNER_RADIUS * k
    setup(ctx, color, brand.STROKE * k, al)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = cx + sx * hw, cy + sy * hh
            ctx.move_to(x, y - sy * arm)
            ctx.line_to(x, y - sy * r)
            ctx.curve_to(x, y, x, y, x - sx * r, y)
            ctx.line_to(x - sx * arm, y)
            ctx.stroke()

# -- circles ------------------------------------------------------------------
def make_ellipse_draw(name, rx, ry, colors, desc):
    @asset(name, "circles", colors, intro=15, out=10, desc=desc)
    def draw(ctx, S, k, phase, f, color):
        s = breathe(f) if phase == "idle" else 1.0
        poly = Poly(ellipse_pts(S / 2, S / 2, rx * k * s, ry * k * s))
        a, b = 0.0, 1.0
        if phase == "intro": b = ease_out(f / 14)
        if phase == "out": a = ease_in(f / 9)
        setup(ctx, color, brand.STROKE * k)
        stroke_pts(ctx, poly.sub(a, b))
    return draw

make_ellipse_draw("circle_draw", 300, 300, CORE, "circle outline, stroke draw-on")
make_ellipse_draw("ellipse_draw", 430, 230, TANGERINE, "wide ellipse outline, stroke draw-on")

@asset("circle_pop", "circles", TANGERINE, intro=11, out=8, desc="circle outline, elastic scale-pop")
def circle_pop(ctx, S, k, phase, f, color):
    s, al = pop_state(phase, f, 11, 8)
    setup(ctx, color, brand.STROKE * k, al)
    ctx.arc(S / 2, S / 2, 300 * k * s, 0, TAU); ctx.stroke()

@asset("pulse_ring", "circles", TANGERINE, intro=11, out=8, desc="circle with sonar pulse rings (loop)")
def pulse_ring(ctx, S, k, phase, f, color):
    s, al = pop_state("idle" if phase == "idle_in" else phase, f, 11, 8)
    if phase in ("idle", "idle_in"): s = 1.0
    R = 170 * k
    setup(ctx, color, brand.STROKE * k, al)
    ctx.arc(S / 2, S / 2, R * s, 0, TAU); ctx.stroke()
    if phase != "intro":
        for ph in (0, LOOP // 2):
            age = (f - ph) % LOOP
            if phase == "idle_in" and f - age < 0:
                continue            # ring would have been emitted before the clip started
            t = age / LOOP
            r = R * (1 + 1.1 * ease_out(t))
            setup(ctx, color, brand.STROKE * k * (1 - .6 * t), (1 - t) ** 1.5 * .9 * min(1, t * 10) * al)
            ctx.arc(S / 2, S / 2, r, 0, TAU); ctx.stroke()

# -- hand-drawn marks ---------------------------------------------------------
@asset("scribble_circle", "marks", CORE, intro=18, out=10, desc="hand-drawn scribble loop around an object")
def scribble(ctx, S, k, phase, f, color):
    seed = boil_seed(f) if phase == "idle" else 0
    wob = noise_fn(30 + seed, .045, (1, 2, 3))
    pts = ellipse_pts(S / 2, S / 2, 330 * k, 250 * k, start=-150, turns=1.22, n=300, wobble=wob)
    pts = jitter(pts, 40 + seed, 3 * k)
    poly = Poly(pts)
    a, b = 0.0, 1.0
    if phase == "intro": b = ease_io(f / 17)
    if phase == "out": a = ease_in(f / 9)
    setup(ctx, color, brand.STROKE * k * .95)
    stroke_pts(ctx, poly.sub(a, b))

@asset("underline_swipe", "marks", CORE, intro=9, out=8, desc="marker underline swipe (sits just below centre)")
def underline(ctx, S, k, phase, f, color):
    seed = boil_seed(f) if phase == "idle" else 0
    cx, cy = S / 2, S / 2 + 40 * k
    pts = bezier((cx - 400 * k, cy + 12 * k), (cx - 130 * k, cy - 6 * k), (cx + 150 * k, cy + 4 * k), (cx + 400 * k, cy - 14 * k), 160)
    poly = Poly(jitter(pts, 50 + seed, 2.5 * k))
    a, b = 0.0, 1.0
    if phase == "intro": b = ease_out(f / 8)
    if phase == "out": a = ease_in(f / 7)
    setup(ctx, color, 24 * k)
    stroke_pts(ctx, poly.sub(a, b))

def mark_draw(ctx, S, k, phase, f, color, strokes, nin, nout):
    al, s = 1.0, 1.0
    if phase == "out":
        t = f / (nout - 1); s = keys(t, POP_OUT); al = 1 - ease_in(clamp((t - .2) / .8))
    elif phase == "idle":
        s = breathe(f, .02)
    ctx.save(); ctx.translate(S / 2, S / 2); ctx.scale(s, s); ctx.translate(-S / 2, -S / 2)
    setup(ctx, color, 30 * k, al)
    n = len(strokes)
    for i, pts in enumerate(strokes):
        poly = Poly(pts)
        b = 1.0
        if phase == "intro":
            span = (nin - 1) / n
            b = ease_out((f - i * span) / span)
        stroke_pts(ctx, poly.sub(0, b))
    ctx.restore()

@asset("check_draw", "marks", CORE, intro=12, out=8, desc="check mark draw-on")
def check(ctx, S, k, phase, f, color):
    c = S / 2
    pts = np.r_[np.linspace((c - 180 * k, c + 10 * k), (c - 55 * k, c + 135 * k), 40),
                np.linspace((c - 55 * k, c + 135 * k), (c + 200 * k, c - 160 * k), 80)[1:]]
    mark_draw(ctx, S, k, phase, f, color, [pts], 12, 8)

@asset("cross_draw", "marks", CORE, intro=12, out=8, desc="cross (X) mark draw-on")
def cross(ctx, S, k, phase, f, color):
    c, r = S / 2, 150 * k
    mark_draw(ctx, S, k, phase, f, color,
              [np.linspace((c - r, c - r), (c + r, c + r), 60), np.linspace((c + r, c - r), (c - r, c + r), 60)], 12, 8)

# -- pointers -----------------------------------------------------------------
@asset("ping_dot", "pointers", TANGERINE, intro=8, out=7, desc="solid dot with ping ring (loop)")
def ping(ctx, S, k, phase, f, color):
    s, al = pop_state("idle" if phase == "idle_in" else phase, f, 8, 7)
    if phase in ("idle", "idle_in"): s = 1.0
    r = 24 * k
    setup(ctx, color, 1, al)
    ctx.arc(S / 2, S / 2, r * s, 0, TAU); ctx.fill()
    if phase != "intro":
        t = (f % (LOOP // 2)) / (LOOP // 2)
        setup(ctx, color, 7 * k * (1 - .5 * t), (1 - t) ** 1.4 * min(1, t * 8) * al)
        ctx.arc(S / 2, S / 2, r + 90 * k * ease_out(t), 0, TAU); ctx.stroke()

@asset("click_ripple", "pointers", CORE, intro=20, out=0, single=True, desc="one-shot cursor click ripple (20 f)")
def click(ctx, S, k, phase, f, color):
    c = S / 2
    t = f / 19
    # press dot
    d = keys(t, [(0, 0), (.12, 1.15), (.3, 1), (1, 0)])
    if d > 0:
        setup(ctx, color, 1, min(1, d))
        ctx.arc(c, c, 16 * k * d, 0, TAU); ctx.fill()
    for delay, rmax in ((0, 95), (.18, 135)):
        tt = clamp((t - delay) / (1 - delay))
        if 0 < tt < 1:
            setup(ctx, color, 8 * k * (1 - .6 * tt), (1 - tt) ** 1.3)
            ctx.arc(c, c, 18 * k + rmax * k * ease_out(tt), 0, TAU); ctx.stroke()

# -- badges -------------------------------------------------------------------
def make_badge(n):
    @asset(f"step_badge_{n:02d}", "badges", TANGERINE, intro=11, out=8,
           desc=f"numbered step badge {n:02d} (JetBrains Mono)")
    def draw(ctx, S, k, phase, f, color):
        s, al = pop_state(phase, f, 11, 8)
        dy = 0.0
        if phase == "idle": s, dy = 1.0, -5 * k * math.sin(TAU * f / LOOP)
        c = S / 2
        ctx.save(); ctx.translate(c, c + dy); ctx.scale(s, s)
        R = 66 * k
        setup(ctx, "chalk", 1, al); ctx.arc(0, 0, R + brand.STICKER_OUTLINE * k, 0, TAU); ctx.fill()
        setup(ctx, color, 1, al); ctx.arc(0, 0, R, 0, TAU); ctx.fill()
        sp = text_sprite(f"{n:02d}", "mono", int(64 * k), "slate", -0.02)
        paint_sprite(ctx, sp, 0, 0, al)
        ctx.restore()
    return draw

for _i in range(1, 6):
    make_badge(_i)

@asset("new_sticker", "badges", ["volt"], intro=13, out=8, desc="'NEW' sticker cutout (Acid Volt, 5px Lab Chalk outline)")
def new_sticker(ctx, S, k, phase, f, color):
    s, al = pop_state(phase, f, 13, 8)
    ang = -8.0
    if phase == "intro": ang = keys(f / 12, [(0, -26), (.55, -4), (.8, -9), (1, -8)])
    if phase == "idle": s, ang = 1.0, -8 + 3 * math.sin(TAU * f / LOOP)
    c = S / 2
    ctx.save(); ctx.translate(c, c); ctx.rotate(math.radians(ang)); ctx.scale(s, s)
    w, h, r, o = 330 * k, 150 * k, brand.CORNER_RADIUS * k * 1.5, brand.STICKER_OUTLINE * k
    def rr(w, h, r):
        p = rrect_pts(0, 0, w, h, r)
        ctx.move_to(*p[0]); [ctx.line_to(*q) for q in p[1:]]; ctx.close_path()
    setup(ctx, "chalk", 1, al); rr(w + 2 * o, h + 2 * o, r + o); ctx.fill()
    setup(ctx, color, 1, al); rr(w, h, r); ctx.fill()
    sp = text_sprite("NEW", "display", int(110 * k), "slate", brand.TRACKING)
    paint_sprite(ctx, sp, 0, 0, al)
    ctx.restore()

# ---------------------------------------------------------------- rendering
SLATE = np.array(brand.rgbf("slate"), np.float32)

def render_frame(A, S, phase, f, color):
    k = S / 1080
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    if phase == "idle_in" and A.name not in ("pulse_ring", "ping_dot"):
        phase = "idle"
    A.draw(ctx, S, k, phase, f, color)
    surf.flush()
    buf = np.frombuffer(surf.get_data(), np.uint8).reshape(S, surf.get_stride() // 4, 4)[:, :S]
    pm = buf[..., [2, 1, 0, 3]].astype(np.float32) / 255.0      # premultiplied RGBA
    a = pm[..., 3]
    # soft Carbon Slate drop shadow keeps light colours readable on bright footage
    if a.max() > 0:
        half = Image.fromarray((a * 255).astype(np.uint8)).resize((S // 2, S // 2), Image.BILINEAR)
        half = half.filter(ImageFilter.GaussianBlur(5 * k))
        sh = np.asarray(half.resize((S, S), Image.BILINEAR), np.float32) / 255.0 * .38
        dy = int(5 * k)
        sh = np.roll(sh, dy, axis=0); sh[:dy] = 0
        out_a = a + sh * (1 - a)
        rgb = pm[..., :3] + SLATE * (sh * (1 - a))[..., None]
    else:
        out_a, rgb = a, pm[..., :3]
    with np.errstate(invalid="ignore", divide="ignore"):
        straight = np.where(out_a[..., None] > 0, rgb / out_a[..., None], 0)
    out = np.dstack([straight, out_a])
    return (np.clip(out, 0, 1) * 255 + .5).astype(np.uint8)

def frames_for(A, clip):
    if A.single:
        return [("intro", f) for f in range(A.intro)]
    if clip == "in":
        return [("intro", f) for f in range(A.intro)] + [("idle_in", f) for f in range(LOOP)]
    if clip == "loop":
        return [("idle", f) for f in range(LOOP)]
    return [("out", f) for f in range(A.out)] + [("out", A.out - 1)] * 0

def out_path(A, clip, color, S, ext="webm"):
    sub = "1080" if S == 1080 else "2160"
    nm = f"ouzfx_hl_{A.name}_{color}.{ext}" if A.single else f"ouzfx_hl_{A.name}_{clip}_{color}.{ext}"
    return os.path.join(OUT, sub, A.group, nm)

BY_NAME = {}
def encode(job):
    name, clip, color, S, prores = job
    A = BY_NAME.get(name) or {x.name: x for x in ASSETS}[name]
    path = out_path(A, clip, color, S)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fr = frames_for(A, clip)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{S}x{S}",
           "-r", str(FPS), "-i", "-", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0",
           "-crf", "26" if S == 1080 else "30", "-auto-alt-ref", "0", "-row-mt", "1", "-deadline", "good",
           "-cpu-used", "2", "-threads", "2", "-metadata", f"title=OuzFX Highlights {A.name} {clip} {color}", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    mov = None
    if prores:
        mpath = out_path(A, clip, color, S, "mov").replace(os.sep + "highlights" + os.sep, os.sep + "highlights-prores" + os.sep)
        os.makedirs(os.path.dirname(mpath), exist_ok=True)
        mov = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{S}x{S}",
                                "-r", str(FPS), "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444",
                                "-pix_fmt", "yuva444p10le", mpath], stdin=subprocess.PIPE)
    for ph, f in fr:
        data = render_frame(A, S, ph, f, color).tobytes()
        p.stdin.write(data)
        if mov: mov.stdin.write(data)
    p.stdin.close(); p.wait()
    if mov: mov.stdin.close(); mov.wait()
    return path, len(fr), os.path.getsize(path)

def jobs(sizes, only, prores):
    for S in sizes:
        for A in ASSETS:
            if only and not any(o in A.name for o in only): continue
            for color in A.colors:
                for clip in (["one"] if A.single else ["in", "loop", "out"]):
                    yield (A.name, clip, color, S, prores)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, action="append", choices=[1080, 2160])
    ap.add_argument("--only", action="append")
    ap.add_argument("--prores", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for A in ASSETS: print(f"{A.group:9} {A.name:24} {','.join(A.colors):24} {A.desc}")
        return
    J = list(jobs(a.size or [1080, 2160], a.only, a.prores))
    print(f"{len(J)} clips")
    with Pool(a.workers) as pool:
        for path, n, size in pool.imap_unordered(encode, J):
            print(f"{os.path.relpath(path, ROOT)}  {n}f  {size // 1024} KB", flush=True)

if __name__ == "__main__":
    main()

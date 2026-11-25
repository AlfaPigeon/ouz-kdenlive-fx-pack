"""OuzFX preset definitions.

Every preset is described once here and turned into Kdenlive files by
tools/build.py. Effect presets are Kdenlive *effect templates* (<effectgroup>
XML, the format Kdenlive itself writes with "Save effect group" and the format
the KDE Store "Kdenlive Effect Templates" category distributes). Composition
presets are custom composition XML (same schema as Kdenlive's
data/transitions/*.xml). Luma wipes are 16-bit greyscale PNG gradients.

Keyframe syntax is plain MLT animation syntax: "frame[type]=value;...".
Type letters (MLT >= 7.22, Kdenlive >= 24.08 shows them in the UI):
  (none) linear   | discrete   ~ smooth
  a/b/c sine in/out/in-out     d/e/f quad    g/h/i cubic   j/k/l quart
  m/n/o quint   p/q/r expo     s/t/u circ    v/w/x back    y/z/A elastic
  B/C/D bounce
The letter goes on the keyframe that STARTS the segment.
"""
import math
import random

# --------------------------------------------------------------------------
# helpers – effect templates use pixel rectangles (Kdenlive's keyframe offset
# code is only lossless for pixel values), so they are generated per profile.
# --------------------------------------------------------------------------


class P:
    """Profile-aware helpers."""

    def __init__(self, w, h):
        self.W, self.H = w, h

    def rect(self, s=1.0, dx=0.0, dy=0.0, o=1.0, ax=0.5, ay=0.5, sy=None):
        """Scale `s` around anchor (ax, ay) (fractions of the frame), then move
        by dx/dy (fractions of width/height). Returns 'x y w h o' in pixels."""
        sy = s if sy is None else sy
        w, h = self.W * s, self.H * sy
        x = ax * self.W - ax * w + dx * self.W
        y = ay * self.H - ay * h + dy * self.H
        return f"{x:.0f} {y:.0f} {w:.0f} {h:.0f} {o:g}"

    def bars(self, ratio):
        """Crop rect that leaves a `ratio` (e.g. 2.39) picture area, centred."""
        h = min(self.H, self.W / ratio)
        y = (self.H - h) / 2
        return f"0 {y:.0f} {self.W} {h:.0f}"

    def bars_kf(self, ratio, frames):
        return kf((0, "h", self.full()), (frames, self.bars(ratio)))

    def full(self):
        return f"0 0 {self.W} {self.H}"


def kf(*keys):
    """kf((0,'v'), (10,'c','v2')...) -> '0=v;10c=v2' ; middle item = type."""
    out = []
    for k in keys:
        if len(k) == 2:
            f, v = k
            t = ""
        else:
            f, t, v = k
        out.append(f"{f}{t}={v}")
    return ";".join(out)


def noise(seed, n, step, amp, octaves=((1.0, 1.0), (2.3, 0.45), (5.1, 0.2))):
    """Smooth deterministic pseudo-random curve sampled every `step` frames."""
    rnd = random.Random(seed)
    phases = [rnd.uniform(0, 2 * math.pi) for _ in octaves]
    vals = []
    for f in range(0, n + 1, step):
        v = 0.0
        for (freq, a), ph in zip(octaves, phases):
            v += a * math.sin(f / 25.0 * freq * 2 * math.pi * 0.35 + ph)
        vals.append((f, amp * v / 1.65))
    return vals


def decay_shake(seed, frames, amp, step=2):
    """Alternating, exponentially decaying offsets (impact shake)."""
    rnd = random.Random(seed)
    keys = []
    sign = 1
    for f in range(0, frames + 1, step):
        k = math.exp(-3.2 * f / frames)
        keys.append((f, sign * amp * k * rnd.uniform(0.6, 1.0),
                     -sign * amp * k * rnd.uniform(0.3, 0.9)))
        sign = -sign
    keys[0] = (0, 0.0, 0.0)
    keys[-1] = (keys[-1][0], 0.0, 0.0)
    return keys


# --------------------------------------------------------------------------
# effect template builders (return list of (effect_id, {prop: value}))
# --------------------------------------------------------------------------

def blur_kf(*keys):
    return ("boxblur", {"blur": kf(*keys), "hori": "1", "vert": "1"})


def dblur_kf(angle, *keys):
    return ("avfilter.dblur", {"av.angle": str(angle), "av.radius": kf(*keys), "av.planes": "7"})


def transform(rect, rotation="0", compositing="0"):
    return ("qtblend", {"rect": rect, "rotation": rotation, "compositing": compositing,
                        "distort": "0"})


def effect_templates(p: P):
    T = []  # (slug, name, category, description, frames, effects, fast_paced?)

    def add(slug, cat, name, desc, frames, effects, tags=()):
        T.append(dict(slug=slug, category=cat, name=name, desc=desc,
                      frames=frames, effects=effects, tags=list(tags)))

    S = 1.06  # overscan used by shakes so edges never show

    # ---------------- Camera shake ----------------
    xs = noise(11, 250, 3, 0.006)
    ys = noise(23, 250, 3, 0.007)
    rs = noise(37, 250, 3, 0.35)
    add("shake_handheld_light", "Camera Shake", "Handheld · Light",
        "Subtle, smooth handheld drift for 10 s (loopable feel). Great on static "
        "talking-head or screen footage. Trim/extend: keyframes stop at clip end.", 250,
        [transform(kf(*[(f, "~", p.rect(S, xs[i][1], ys[i][1])) for i, (f, _) in enumerate(xs)]),
                   kf(*[(f, "~", f"{rs[i][1]:.3f}") for i, (f, _) in enumerate(rs)])),
         blur_kf((0, 0))], tags=["loop"])

    xs = noise(5, 250, 2, 0.002, ((3.0, 1.0), (7.0, 0.5)))
    ys = noise(6, 250, 2, 0.002, ((3.3, 1.0), (6.1, 0.5)))
    add("shake_micro_jitter", "Camera Shake", "Micro Jitter",
        "Barely-there high-frequency jitter (10 s) that makes locked-off shots feel alive.", 250,
        [transform(kf(*[(f, "~", p.rect(1.02, xs[i][1], ys[i][1])) for i, (f, _) in enumerate(xs)])),
         blur_kf((0, 0))])

    ks = decay_shake(101, 20, 0.035)
    add("shake_heavy_impact", "Camera Shake", "Heavy Impact",
        "20-frame violent hit that decays to rest, with motion blur on the first frames. "
        "Put the clip start on the impact / beat drop.", 20,
        [transform(kf(*[(f, "", p.rect(1.10, x, y)) for f, x, y in ks]),
                   kf(*[(f, "", f"{(x * 90):.2f}") for f, x, y in ks])),
         blur_kf((0, 6), (6, 2), (12, 0))], tags=["fast"])

    ks = decay_shake(202, 75, 0.022, step=2)
    xs2 = [(f, x * (0.6 + 0.4 * math.sin(f))) for f, x, y in ks]
    add("shake_earthquake", "Camera Shake", "Earthquake",
        "3 s of strong rumbling shake that slowly calms down, with light blur.", 75,
        [transform(kf(*[(f, "", p.rect(1.12, xs2[i][1], y)) for i, (f, x, y) in enumerate(ks)]),
                   kf(*[(f, "", f"{(y * 60):.2f}") for f, x, y in ks])),
         blur_kf((0, 3), (40, 1), (75, 0))])

    rot = [(f, 4.5 * math.exp(-3 * f / 30) * (1 if (f // 3) % 2 == 0 else -1)) for f in range(0, 31, 3)]
    rot[-1] = (30, 0)
    add("shake_rotational", "Camera Shake", "Rotational",
        "Rocking rotational shake (30 frames, decaying) – feels like a punch to the camera.", 30,
        [transform(p.rect(1.12), kf(*[(f, "c", f"{r:.2f}") for f, r in rot])),
         blur_kf((0, 2), (12, 0))])

    bob = [(f, (0.012 if (f // 6) % 2 == 0 else -0.004)) for f in range(0, 241, 6)]
    add("shake_walk_bounce", "Camera Shake", "Walking Bounce",
        "Vertical bob of a walking camera operator (10 s loop).", 240,
        [transform(kf(*[(f, "c", p.rect(1.05, 0, dy)) for f, dy in bob])), blur_kf((0, 0))])

    # ---------------- Dynamic zoom ----------------
    add("zoom_punch_in", "Dynamic Zoom", "Punch-In 115%",
        "Snaps to 115% in 3 frames and holds – the classic jump-cut cover.", 3,
        [transform(kf((0, "q", p.rect(1.0)), (3, p.rect(1.15)))), blur_kf((0, 3), (3, 0))], tags=["fast"])
    add("zoom_punch_in_out", "Dynamic Zoom", "Punch In-Out (Beat)",
        "Zooms to 120% on frame 2 and settles back by frame 10. Drop one on every beat.", 10,
        [transform(kf((0, "q", p.rect(1.0)), (2, "h", p.rect(1.2)), (10, p.rect(1.0)))),
         blur_kf((0, 4), (3, 1), (8, 0))], tags=["fast"])
    add("zoom_boom", "Dynamic Zoom", "Boom Zoom",
        "Explosive 135% zoom with elastic settle at 112% (18 frames) – 'boom' moments.", 18,
        [transform(kf((0, "q", p.rect(1.0)), (3, "z", p.rect(1.35)), (18, p.rect(1.12)))),
         blur_kf((0, 8), (4, 2), (10, 0))], tags=["fast"])
    add("zoom_bounce", "Dynamic Zoom", "Zoom Bounce",
        "Zooms from 100% to 125% with a bouncy landing (20 frames).", 20,
        [transform(kf((0, "C", p.rect(1.0)), (20, p.rect(1.25)))), blur_kf((0, 0))])
    add("zoom_ken_burns_in", "Dynamic Zoom", "Slow Push-In (5 s)",
        "Ken Burns style 100→112% push over 5 s (use the composition version to fit any length).", 125,
        [transform(kf((0, "c", p.rect(1.0)), (125, p.rect(1.12)))), blur_kf((0, 0))])
    add("zoom_ken_burns_out", "Dynamic Zoom", "Slow Pull-Out (5 s)",
        "Ken Burns style 112→100% pull-back over 5 s.", 125,
        [transform(kf((0, "c", p.rect(1.12)), (125, p.rect(1.0)))), blur_kf((0, 0))])
    for slug, nm, ax, ay in [("tl", "Top-Left", 0.0, 0.0), ("tr", "Top-Right", 1.0, 0.0),
                             ("bl", "Bottom-Left", 0.0, 1.0), ("br", "Bottom-Right", 1.0, 1.0),
                             ("c", "Center", 0.5, 0.5)]:
        add(f"zoom_screen_{slug}", "Screen Zoom", f"Zoom to {nm} (Screen Rec)",
            f"Smooth 15-frame zoom to 180% on the {nm.lower()} of a screen recording, then holds. "
            "Razor the clip where you want to zoom; move the rectangle in the monitor to aim at the cursor.", 15,
            [transform(kf((0, "i", p.rect(1.0, ax=ax, ay=ay)), (15, p.rect(1.8, ax=ax, ay=ay)))),
             blur_kf((0, 0), (5, 2), (12, 0))], tags=["fast"])
    add("zoom_screen_out", "Screen Zoom", "Zoom Back Out (Screen Rec)",
        "Companion to the screen zooms: from 180% (center) back to full frame in 15 frames.", 15,
        [transform(kf((0, "i", p.rect(1.8)), (15, p.rect(1.0)))), blur_kf((0, 0), (5, 2), (12, 0))])

    # ---------------- Animations (intro, start-anchored) ----------------
    add("anim_pop_in", "Animations", "Pop-In",
        "Scales from 0 to 100% with a back-overshoot in 12 frames.", 12,
        [transform(kf((0, "w", p.rect(0.0, o=0)), (12, p.rect(1.0)))), blur_kf((0, 2), (8, 0))])
    for slug, nm, dx, dy, ang in [("left", "Left", -1.1, 0, 0), ("right", "Right", 1.1, 0, 0),
                                  ("top", "Top", 0, -1.1, 90), ("bottom", "Bottom", 0, 1.1, 90)]:
        add(f"anim_slide_in_{slug}", "Animations", f"Slide In from {nm}",
            f"Slides in from the {nm.lower()} edge in 12 frames (expo ease-out) with directional motion blur.", 12,
            [transform(kf((0, "q", p.rect(1.0, dx, dy)), (12, p.rect(1.0)))),
             dblur_kf(ang, (0, 60), (6, 10), (12, 0))])
    add("anim_bounce_in", "Animations", "Bounce In (Drop)",
        "Drops from above and bounces on the floor (20 frames).", 20,
        [transform(kf((0, "C", p.rect(1.0, 0, -1.05)), (20, p.rect(1.0)))), blur_kf((0, 0))])
    add("anim_spin_in", "Animations", "Spin-In",
        "Spins 360° while scaling from 0 to 100% (15 frames, cubic ease-out).", 15,
        [transform(kf((0, "h", p.rect(0.0, o=0)), (15, p.rect(1.0))), kf((0, "h", "-360"), (15, "0"))),
         blur_kf((0, 4), (10, 0))])
    add("anim_fade_scale_in", "Animations", "Fade + Scale In",
        "Gentle 92→100% scale with fade-in over 15 frames – clean Apple-style reveal.", 15,
        [transform(kf((0, "h", p.rect(0.92, o=0)), (15, p.rect(1.0)))), blur_kf((0, 3), (12, 0))])
    add("anim_whip_in", "Animations", "Whip-In",
        "Very fast slide from the right with heavy motion blur (6 frames).", 6,
        [transform(kf((0, "q", p.rect(1.0, 1.0)), (6, p.rect(1.0)))), dblur_kf(0, (0, 150), (4, 30), (6, 0))],
        tags=["fast"])
    add("anim_elastic_in", "Animations", "Elastic Zoom-In",
        "Springs in from 40% to 100% with an elastic wobble (20 frames).", 20,
        [transform(kf((0, "z", p.rect(0.4, o=0)), (20, p.rect(1.0)))), blur_kf((0, 0))])
    add("anim_blur_in", "Animations", "Blur-In",
        "Starts heavily blurred and transparent, resolves to sharp in 15 frames.", 15,
        [("avfilter.gblur", {"av.sigma": kf((0, "h", 40), (15, 0)), "av.sigmaV": kf((0, "h", 40), (15, 0)),
                             "av.steps": "1", "av.planes": "15"}),
         transform(kf((0, "h", p.rect(1.04, o=0)), (15, p.rect(1.0))))])

    # ---------------- Perspective screen share ----------------
    def c0(tl, tr, br, bl):
        m = lambda v: f"{(v + 1) / 3:.4f}"
        d = {"0": m(tl[0]), "1": m(tl[1]), "2": m(tr[0]), "3": m(tr[1]),
             "4": m(br[0]), "5": m(br[1]), "6": m(bl[0]), "7": m(bl[1]),
             "8": "0", "9": "0.5", "10": "0.5", "11": "0.166", "12": "1", "13": "0.01", "14": "0"}
        return d

    def rounded(r=0.035):
        return ("qtcrop", {"rect": p.full(), "radius": str(r), "circle": "0", "color": "0x00000000"})

    shadow = ("dropshadow", {"radius": "25", "x": "14", "y": "22", "color": "#a0000000"})
    add("screen_tilt_left", "Perspective Screen", "Tilt Left",
        "Screen recording turned into a 3D panel facing left: rounded corners, perspective and a soft "
        "drop shadow. Put a background on the track below.", 0,
        [rounded(), ("frei0r.c0rners", c0((0.06, 0.16), (0.90, 0.06), (0.90, 0.94), (0.06, 0.84))), shadow])
    add("screen_tilt_right", "Perspective Screen", "Tilt Right",
        "Mirror of Tilt Left – panel facing right.", 0,
        [rounded(), ("frei0r.c0rners", c0((0.10, 0.06), (0.94, 0.16), (0.94, 0.84), (0.10, 0.94))), shadow])
    add("screen_tilt_back", "Perspective Screen", "Laptop Lean",
        "Panel leaning back like a laptop screen seen from the desk.", 0,
        [rounded(), ("frei0r.c0rners", c0((0.16, 0.10), (0.84, 0.10), (0.94, 0.90), (0.06, 0.90))), shadow])
    add("screen_floating", "Perspective Screen", "Floating Screen (Flat)",
        "Flat floating window: rounded corners, 82% scale, big soft shadow.", 0,
        [rounded(0.03), transform(p.rect(0.82)), shadow])
    a = c0((0.06, 0.16), (0.90, 0.06), (0.90, 0.94), (0.06, 0.84))
    b = c0((0.09, 0.09), (0.91, 0.09), (0.91, 0.91), (0.09, 0.91))
    anim = {k: (kf((0, "i", a[k]), (25, b[k])) if k in "01234567" and len(k) == 1 else v) for k, v in a.items()}
    add("screen_tilt_to_flat", "Perspective Screen", "Swing to Front",
        "Starts tilted left and swings to a flat, centred panel in 25 frames – nice opener for a demo.", 25,
        [rounded(), ("frei0r.c0rners", anim), shadow])
    a2 = c0((0.30, 0.30), (0.70, 0.30), (0.70, 0.70), (0.30, 0.70))
    anim2 = {k: (kf((0, "w", a2[k]), (18, b[k])) if k in "01234567" and len(k) == 1 else v) for k, v in a2.items()}
    add("screen_pop_in", "Perspective Screen", "Floating Screen · Pop In",
        "Floating window pops in from 40% with overshoot (18 frames), rounded + shadow.", 18,
        [rounded(), ("frei0r.c0rners", anim2), shadow])

    # ---------------- Glitch / Stylize ----------------
    add("glitch_rgb_split_hit", "Glitch & Stylize", "RGB Split Hit",
        "8-frame chromatic split that kicks hard and snaps back – sync to a beat or a cut.", 8,
        [("avfilter.rgbashift", {"av.rh": kf((0, "|", 0), (1, "e", 28), (8, 0)), "av.bh": kf((0, "|", 0), (1, "e", -28), (8, 0)),
                                 "av.gv": kf((0, "|", 0), (1, "e", 6), (8, 0)), "av.edge": "smear"}),
         transform(kf((0, "|", p.rect(1.0)), (1, "e", p.rect(1.06)), (8, p.rect(1.0))))], tags=["fast"])
    add("glitch_digital_burst", "Glitch & Stylize", "Digital Glitch Burst",
        "12 frames of block glitching + RGB tearing that fades out.", 12,
        [("frei0r.glitch0r", {"0": kf((0, 1.0), (8, 0.6), (12, 0.0)), "1": "0.15", "2": kf((0, 0.6), (8, 0.4), (12, 0.0)), "3": kf((0, 0.6), (8, 0.4), (12, 0))}),
         ("avfilter.rgbashift", {"av.rh": kf((0, "|", 20), (3, "|", -14), (6, "|", 10), (9, "|", -4), (12, 0)),
                                 "av.bh": kf((0, "|", -20), (3, "|", 12), (6, "|", -8), (9, "|", 4), (12, 0)), "av.edge": "wrap"})],
        tags=["fast"])
    add("style_vhs", "Glitch & Stylize", "VHS Tape",
        "Scanlines, chroma bleed, soft blur, noise and slightly washed colour – instant 90s tape.", 0,
        [("avfilter.chromashift", {"av.cbh": "6", "av.crh": "-6", "av.cbv": "0", "av.crv": "0", "av.edge": "0"}),
         ("avfilter.gblur", {"av.sigma": "1.2", "av.sigmaV": "0.4", "av.steps": "1", "av.planes": "15"}),
         ("grain", {"noise": "18", "contrast": "100", "brightness": "100"}),
         ("frei0r.scanline0r", {})])
    add("flash_white", "Glitch & Stylize", "Flash Frame (White)",
        "2-frame white flash that fades by frame 6 – hides a cut and adds punch.", 6,
        [("brightness", {"level": kf((0, 4.0), (2, "e", 3.0), (6, 1.0))}),
         blur_kf((0, 4), (3, 0))], tags=["fast"])
    add("flash_black", "Glitch & Stylize", "Dip Flash (Black)",
        "Quick dip to black and back in 6 frames.", 6,
        [("brightness", {"level": kf((0, 0.0), (2, "e", 0.0), (6, 1.0))}),
         blur_kf((0, 3), (4, 0))], tags=["fast"])
    add("style_film_burn", "Glitch & Stylize", "Film Burn Flash",
        "Warm orange over-exposure with glow that peaks at frame 6 and clears by 16.", 16,
        [("frei0r.colorize", {"hue": "0.07", "saturation": kf((0, 0.0), (6, "f", 0.85), (16, 0.0)), "lightness": kf((0, 0.5), (6, "f", 0.68), (16, 0.5))}),
         ("frei0r.glow", {"Blur": kf((0, 0.0), (6, "f", 0.35), (16, 0.0))}),
         ("brightness", {"level": kf((0, 1.0), (6, "f", 1.9), (16, 1.0))})], tags=["fast"])
    add("style_light_leak", "Glitch & Stylize", "Warm Light Leak Look",
        "Soft warm glow and lifted highlights (static look). For moving leaks, also drop "
        "overlays/ouzfx_light_leak.mp4 on a track above with Screen blend.", 0,
        [("frei0r.glow", {"Blur": "0.12"}),
         ("frei0r.colorize", {"hue": "0.08", "saturation": "0.35", "lightness": "0.56"})])
    add("style_red_alert", "Glitch & Stylize", "Red Moment",
        "MrBeast-style 'stress' tint: flash to deep red with a small punch (hold 1–2 s).", 4,
        [("frei0r.colorize", {"hue": "0.0", "saturation": kf((0, "e", 0.0), (4, 0.9)), "lightness": "0.45"}),
         transform(kf((0, "e", p.rect(1.0)), (4, p.rect(1.08))))], tags=["fast"])
    add("style_flashback", "Glitch & Stylize", "B&W Flashback",
        "Black & white, grain, vignette and old-film flicker for flashbacks / archive footage.", 0,
        [("greyscale", {}), ("grain", {"noise": "30", "contrast": "130", "brightness": "90"}),
         ("vignette", {"radius": "0.75", "smooth": "0.6", "opacity": "0.6", "mode": "0"})])

    # ---------------- Overlays / looks ----------------
    add("look_cinematic_239", "Overlays", "Cinematic 2.39:1 Bars + Vignette",
        "Letterbox bars for a 2.39:1 look plus a soft vignette.", 0,
        [("qtcrop", {"rect": p.bars(2.39), "radius": "0", "circle": "0", "color": "0x000000ff"}),
         ("vignette", {"radius": "0.8", "smooth": "0.7", "opacity": "0.45", "mode": "0"})])
    add("look_bars_slide_in", "Overlays", "Cinematic Bars Slide-In",
        "2.39:1 letterbox bars glide in over 15 frames – 'movie moment' / dramatic beat.", 15,
        [("qtcrop", {"rect": p.bars_kf(2.39, 15), "radius": "0", "circle": "0", "color": "0x000000ff"}),
         ("vignette", {"radius": "0.8", "smooth": "0.7", "opacity": "0.45", "mode": "0"})])
    add("look_film_grain", "Overlays", "Film Grain + Dust",
        "Organic grain with a few dust specks – makes digital footage feel shot on film.", 0,
        [("grain", {"noise": "22", "contrast": "110", "brightness": "100"}),
         ("dust", {"maxdiameter": "2", "maxcount": "4"})])
    add("look_soft_vignette", "Overlays", "Soft Vignette",
        "Gentle edge darkening that pulls the eye to the centre.", 0,
        [("vignette", {"radius": "0.7", "smooth": "0.8", "opacity": "0.35", "mode": "0"}),
         ("brightness", {"level": "1.02"})])

    # ---------------- Fast-paced kit ----------------
    add("fast_impact_hit", "Fast-Paced", "Impact Hit (Shake + Flash + Zoom)",
        "All-in-one hit: 2-frame flash, 125% punch and a decaying shake (12 frames). Use on beat drops.", 12,
        [("brightness", {"level": kf((0, 3.0), (2, "e", 1.6), (5, 1.0))}),
         transform(kf(*[(f, "", p.rect(1.25 - 0.13 * f / 12, x, y)) for f, x, y in decay_shake(7, 12, 0.03)])),
         blur_kf((0, 7), (4, 1), (8, 0))], tags=["fast"])
    add("fast_smash_cut", "Fast-Paced", "Smash Cut In",
        "Starts at 140% with blur and slams to 100% in 4 frames – energetic hard cut entry.", 4,
        [transform(kf((0, "e", p.rect(1.4)), (4, p.rect(1.0)))), blur_kf((0, 10), (4, 0))], tags=["fast"])
    add("fast_zoom_cut_hold", "Fast-Paced", "Zoom Cut (Hard 130%)",
        "Instant 130% reframe, no animation – the MrBeast wide→close 'zoom cut'.", 0,
        [transform(p.rect(1.3)), blur_kf((0, 0))], tags=["fast"])
    add("fast_beat_pulse", "Fast-Paced", "Beat Pulse ×4",
        "Four quick 108% pulses, one every 12 frames (≈120 BPM at 24 fps). Stretch keyframes to your tempo.", 48,
        [transform(kf(*sum([[(i * 12, "q", p.rect(1.08)), (i * 12 + 8, p.rect(1.0))] for i in range(4)], []))),
         blur_kf(*sum([[(i * 12, 3), (i * 12 + 4, 0)] for i in range(4)], []))], tags=["fast"])
    add("fast_stutter_strobe", "Fast-Paced", "Stutter Strobe",
        "6-frame on/off brightness strobe – for glitchy, aggressive moments.", 6,
        [("brightness", {"level": kf((0, "|", 2.2), (1, "|", 1.0), (2, "|", 2.2), (3, "|", 1.0), (4, "|", 1.8), (5, "|", 1.0), (6, 1.0))}),
         transform(kf((0, "|", p.rect(1.05)), (1, "|", p.rect(1.0)), (2, "|", p.rect(1.05)), (3, "|", p.rect(1.0)), (6, p.rect(1.0))))],
        tags=["fast"])
    add("fast_freeze_pop", "Fast-Paced", "Freeze-Frame Pop",
        "Pair with Kdenlive's freeze (Timeline ▸ Insert Freeze Frame / Freeze effect): saturation boost, "
        "slight zoom and white flash so the still frame 'pops'.", 6,
        [("frei0r.saturat0r", {"Saturation": "0.25"}),
         ("brightness", {"level": kf((0, 2.4), (6, "e", 1.05))}),
         transform(kf((0, "w", p.rect(1.0)), (6, p.rect(1.07))))], tags=["fast"])
    add("fast_motion_slide_l", "Fast-Paced", "Motion-Blur Push Left",
        "Last 6 frames of a clip: whips the picture out to the left with heavy blur. "
        "Pair with 'Whip-In' on the next clip.", 6,
        [transform(kf((0, "p", p.rect(1.0)), (6, p.rect(1.0, -1.0)))), dblur_kf(0, (0, 0), (2, 60), (6, 150))], tags=["fast"])
    add("fast_speed_lines_zoom", "Fast-Paced", "Rush Zoom",
        "Accelerating zoom (100→160%) with growing blur over 8 frames – cut on the last frame.", 8,
        [transform(kf((0, "p", p.rect(1.0)), (8, p.rect(1.6)))), blur_kf((0, 0), (8, 14))], tags=["fast"])

    # ---------------- Text / titles ----------------
    add("text_pop", "Text & Titles", "Text Pop",
        "For title clips: pops in with a back overshoot in 8 frames (kinetic typography staple).", 8,
        [transform(kf((0, "w", p.rect(0.3, o=0)), (8, p.rect(1.0)))), blur_kf((0, 0))], tags=["fast"])
    add("text_slam", "Text & Titles", "Text Slam",
        "Title slams down from 300% and the frame shakes on landing (14 frames).", 14,
        [transform(kf((0, "g", p.rect(3.0, o=0)), (5, p.rect(1.0)),
                      *[(5 + f, "", p.rect(1.0, x * 0.6, y * 0.6)) for f, x, y in decay_shake(9, 9, 0.02, 1)][1:])),
         blur_kf((0, 6), (5, 0))], tags=["fast"])
    add("text_rise", "Text & Titles", "Text Rise",
        "Rises 6% and fades in over 12 frames – clean lower-third / callout entry.", 12,
        [transform(kf((0, "h", p.rect(1.0, 0, 0.06, o=0)), (12, p.rect(1.0)))), blur_kf((0, 2), (8, 0))])
    add("text_wiggle", "Text & Titles", "Text Wiggle (Loop)",
        "Playful ±3° wiggle and 2% breathe for 4 s – for stickers, arrows, emojis.", 100,
        [transform(kf(*[(f, "c", p.rect(1.0 + (0.02 if (f // 10) % 2 else 0))) for f in range(0, 101, 10)]),
                   kf(*[(f, "c", "3" if (f // 10) % 2 else "-3") for f in range(0, 101, 10)])), blur_kf((0, 0))])
    add("text_typewriter_flash", "Text & Titles", "Highlight Flash",
        "Draws attention to a callout: brightness flash + 110% pulse (10 frames).", 10,
        [("brightness", {"level": kf((0, 1.0), (2, "e", 1.8), (10, 1.0))}),
         transform(kf((0, p.rect(1.0)), (2, "h", p.rect(1.1)), (10, p.rect(1.0))))])
    return T


# --------------------------------------------------------------------------
# compositions – percentage + negative keyframes so they stretch to whatever
# length the composition has on the timeline.
# --------------------------------------------------------------------------

def R(x, y, w, h, o=100):
    return f"{x:g}% {y:g}% {w:g}% {h:g}% {o:g}%"


FULL = R(0, 0, 100, 100)


def compositions():
    C = []

    def add(slug, cat, name, desc, tag, values, tags=()):
        C.append(dict(slug=slug, category=cat, name=name, desc=desc, tag=tag, values=values, tags=list(tags)))

    def scaled(s, o=100, dx=0, dy=0):
        return R(50 - s / 2 + dx, 50 - s / 2 + dy, s, s, o)

    add("comp_zoom_through_in", "Transitions", "Zoom-Through In",
        "Top clip flies in from 300% (transparent) to full frame – put it over the end of the lower clip.",
        "affine", {"rect": f"0q={scaled(300, 0)};-1={FULL}"}, ["fast"])
    add("comp_zoom_through_out", "Transitions", "Zoom-Through Out",
        "Top clip rushes towards the camera (100→300%) and fades, revealing the clip below.",
        "affine", {"rect": f"0p={FULL};-1={scaled(300, 0)}"}, ["fast"])
    add("comp_zoom_out_reveal", "Transitions", "Shrink Away",
        "Top clip shrinks to nothing in the centre, revealing the lower track.",
        "qtblend", {"rect": f"0g={FULL};-1={scaled(0, 0)}"})
    for slug, nm, sx, sy in [("left", "Left", -100, 0), ("right", "Right", 100, 0), ("up", "Up", 0, -100), ("down", "Down", 0, 100)]:
        add(f"comp_whip_{slug}", "Transitions", f"Whip Pan {nm}",
            f"Top clip enters from the opposite side and whips {nm.lower()} into place with strong ease-out "
            "(add a dblur/boxblur for extra smear). Keep it 6–10 frames.",
            "qtblend", {"rect": f"0q={R(-sx, -sy, 100, 100)};-1={FULL}"}, ["fast"])
    add("comp_spin_in", "Transitions", "Spin In",
        "Top clip spins in 360° from 0% – fun, high-energy reveal.",
        "qtblend", {"rect": f"0h={scaled(0, 0)};-1={FULL}", "rotation": "0=-360;-1=0"}, ["fast"])
    add("comp_spin_out", "Transitions", "Spin Out",
        "Top clip spins away 360° shrinking to 0%.",
        "qtblend", {"rect": f"0g={FULL};-1={scaled(0, 0)}", "rotation": "0=0;-1=360"})
    for slug, nm, ex, ey in [("left", "Left", -100, 0), ("right", "Right", 100, 0), ("up", "Up", 0, -100), ("down", "Down", 0, 100)]:
        add(f"comp_slide_out_{slug}", "Animations", f"Slide Out {nm}",
            f"Top clip exits to the {nm.lower()} (expo ease-in). Place it over the END of the clip.",
            "qtblend", {"rect": f"0p={FULL};-1={R(ex, ey, 100, 100)}"})
    add("comp_pop_out", "Animations", "Pop Out",
        "Anticipates (grows to 106%) then collapses to 0% – place over the end of a clip/title.",
        "qtblend", {"rect": f"0v={FULL};-1={scaled(0, 0)}"})
    add("comp_fade_scale_out", "Animations", "Fade + Scale Out",
        "Soft 100→92% shrink with fade-out.",
        "qtblend", {"rect": f"0g={FULL};-1={scaled(92, 0)}"})
    add("comp_pop_in", "Animations", "Pop In (Any Length)",
        "Back-overshoot pop-in that stretches to the composition length.",
        "qtblend", {"rect": f"0w={scaled(0, 0)};-1={FULL}"})
    add("comp_ken_burns_in", "Dynamic Zoom", "Ken Burns Push-In (Any Length)",
        "100→115% slow push that always spans the whole composition – stretch it over a photo/clip.",
        "affine", {"rect": f"0c={FULL};-1={scaled(115)}"})
    add("comp_ken_burns_out", "Dynamic Zoom", "Ken Burns Pull-Out (Any Length)",
        "115→100% slow pull-back spanning the composition.",
        "affine", {"rect": f"0c={scaled(115)};-1={FULL}"})
    add("comp_ken_burns_pan", "Dynamic Zoom", "Ken Burns Pan L→R (Any Length)",
        "Pans across a 120% image from left to right over the composition length.",
        "affine", {"rect": f"0c={R(0, -10, 120, 120)};-1={R(-20, -10, 120, 120)}"})
    add("comp_picture_in_picture", "Perspective Screen", "Picture-in-Picture Corner (Pop)",
        "Webcam/facecam bubble: pops into the bottom-right corner at 30% size.",
        "qtblend", {"rect": f"0w={R(84, 84, 0, 0, 0)};12={R(67, 66, 30, 30)};-1={R(67, 66, 30, 30)}"})
    # luma based wipes (resource filled in by install.sh)
    for slug, nm, luma, soft in [("burn", "Film Burn Wipe", "ouzfx_burn.png", 0.25),
                                 ("glitch", "Glitch Blocks Wipe", "ouzfx_glitch_blocks.png", 0.0),
                                 ("diamond", "Diamond Wipe", "ouzfx_diamond.png", 0.08),
                                 ("clock", "Clock Wipe", "ouzfx_clock.png", 0.04),
                                 ("iris", "Iris Wipe", "ouzfx_radial.png", 0.1)]:
        add(f"comp_wipe_{slug}", "Luma Wipes", nm,
            f"Wipe composition using the bundled {luma} luma (softness {soft}). The same luma is also "
            "selectable in every Wipe/Luma transition and same-track mix.",
            "luma", {"resource": f"@LUMADIR@/HD/ouzfx/{luma}", "softness": str(soft)}, ["fast"] if slug == "glitch" else [])
    return C


LUMAS = [
    ("ouzfx_radial", "Iris / radial from centre"),
    ("ouzfx_radial_soft", "Soft round spotlight"),
    ("ouzfx_diagonal_tl", "Diagonal from top-left"),
    ("ouzfx_diagonal_tr", "Diagonal from top-right"),
    ("ouzfx_clock", "Clock sweep from 12 o'clock"),
    ("ouzfx_blinds_h", "Horizontal blinds (8 slats)"),
    ("ouzfx_blinds_v", "Vertical blinds (12 slats)"),
    ("ouzfx_diamond", "Diamond from centre"),
    ("ouzfx_burn", "Organic film-burn noise"),
    ("ouzfx_glitch_blocks", "Random glitch blocks"),
    ("ouzfx_zigzag", "Zig-zag teeth from left"),
    ("ouzfx_barn_doors", "Barn doors opening from centre"),
    ("ouzfx_spiral", "Spiral from centre"),
    ("ouzfx_heart", "Heart iris (for fun edits)"),
    ("ouzfx_pixel_dissolve", "Pixel dissolve (32px cells)"),
    ("ouzfx_swipe_up_soft", "Soft swipe upwards"),
]

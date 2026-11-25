"""OuzFX v1.1 "AFX" expansion – only the blueprint items that v1.0 did not cover.

Naming follows the blueprint: OuzFX AFX_Move_*, AFX_Cam_*, AFX_Style_*, AFX_Util_*,
AFX_Audio_*. Every item lists the blueprint entry it fills in `bp` (used to generate
docs/BLUEPRINT_COVERAGE.md). Geometry uses presets.P, so 1080p / 4K / vertical
variants are generated from the same normalized (fraction-of-frame) numbers.
"""
import math

from presets import P, kf, decay_shake, blur_kf, dblur_kf, transform, R, FULL

# qtblend rotates around the rect centre in Kdenlive (rotate_center=1 / rotate_anchor 0.5 0.5)


def _rot(vx, vy, deg):
    a = math.radians(deg)  # positive = clockwise on screen (y down)
    return vx * math.cos(a) - vy * math.sin(a), vx * math.sin(a) + vy * math.cos(a)


def pivot_rect(p: P, deg, px, py, s=1.0, o=1.0):
    """Rect (pixels) that makes a centre-rotated full-frame layer of scale s look as if it
    pivots around (px, py) – fractions of the frame (0,0 = top-left corner)."""
    w, h = p.W * s, p.H * s
    x0, y0 = (p.W - w) / 2, (p.H - h) / 2              # unrotated rect (centred)
    pivx, pivy = x0 + px * w, y0 + py * h               # pivot on the layer
    vx, vy = pivx - (x0 + w / 2), pivy - (y0 + h / 2)   # centre -> pivot
    rx, ry = _rot(vx, vy, deg)
    cx, cy = pivx - rx, pivy - ry                       # new centre keeps pivot fixed
    return f"{cx - w / 2:.0f} {cy - h / 2:.0f} {w:.0f} {h:.0f} {o:g}"


def cover_scale(p: P, deg):
    """Scale needed so a layer rotated by `deg` still covers the whole frame."""
    a = math.radians(abs(deg))
    return max(math.cos(a) + (p.H / p.W) * math.sin(a), math.cos(a) + (p.W / p.H) * math.sin(a)) * 1.005


def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def crop(rect, radius="0", color="0x00000000"):
    return ("qtcrop", {"rect": rect, "radius": radius, "circle": "0", "color": color})


def spot(shape, px, py, sx, sy, tw, mn, mx, op="0"):
    """Kdenlive 'Alpha shapes (Mask)' – region for the following effects (until Mask Apply).
    shape: 0 rectangle, 0.38 ellipse. min/max = shape value outside / inside.
    op "0" writes the shape as the mask (effects inside); op "1" subtracts it from the opaque
    frame, i.e. an inverted mask (effects OUTSIDE the shape) without frei0r's ring artefact."""
    return ("mask_start-frei0r.alphaspot", {
        "filter.Shape": str(shape), "filter.Position X": f"{px:g}", "filter.Position Y": f"{py:g}",
        "filter.Size X": f"{sx:g}", "filter.Size Y": f"{sy:g}", "filter.Tilt": "0.5",
        "filter.Transition width": f"{tw:g}", "filter.Min": f"{mn:g}", "filter.Max": f"{mx:g}",
        "filter.Operation": op})


MASK_APPLY = ("mask_apply", {})


def afx_templates(p: P):
    T = []

    def add(cat, name, bp, desc, frames, effects, tags=(), audio=False):
        slug = f"afx_{cat.split('_')[1].lower()}_{name.lower()}"
        T.append(dict(slug=slug, category=cat, name=name, desc=desc, frames=frames, effects=effects,
                      tags=list(tags), bp=bp, audio=audio))

    DIRS = [("Left", -1, 0), ("Right", 1, 0), ("Top", 0, -1), ("Bottom", 0, 1)]

    # ================================================================ AFX_Move
    for nm, sx, sy in DIRS:
        ang = 0 if sy == 0 else 90
        add("AFX_Move", f"Overshoot_Slide_In_{nm}", "1.2 Overshoot / Bounce Slide",
            f"Slides in from the {nm.lower()} edge, swings past its resting spot and settles back "
            "(14 frames, Kdenlive/MLT back ease-out – the overshoot peaks at ≈ 37% of the travel) with a short motion-blur peak.", 14,
            [transform(kf((0, "w", p.rect(1.0, 1.05 * sx, 1.05 * sy)), (14, p.rect(1.0)))),
             dblur_kf(ang, (0, 40), (5, 6), (14, 0))], tags=["fast"])

    reveals = [("Up", 0, 0.5, p.full_part(0, 0, 1, 0.5)), ("Down", 0, -0.5, p.full_part(0, 0.5, 1, 0.5)),
               ("Left", 0.5, 0, p.full_part(0, 0, 0.5, 1)), ("Right", -0.5, 0, p.full_part(0.5, 0, 0.5, 1))]
    for nm, dx, dy, mask in reveals:
        side = {"Up": "upper half", "Down": "lower half", "Left": "left half", "Right": "right half"}[nm]
        add("AFX_Move", f"Masked_Edge_Reveal_{nm}", "1.4 Masked Edge Reveal",
            f"Emerges {nm.lower()} out of an invisible line through the middle of the frame: the layer slides "
            f"while a static crop keeps only the {side} visible (15 frames, expo ease-out). Made for split "
            "graphics / callout cards – move the Crop rectangle to put the line anywhere.", 15,
            [transform(kf((0, "q", p.rect(1.0, dx, dy)), (15, p.rect(1.0)))), crop(mask)])

    for tier, amp, rot, period in [("Gentle", 0.010, 1.2, 100), ("Strong", 0.020, 2.0, 80)]:
        keys = list(range(0, 2 * period + 1, period // 4))
        add("AFX_Move", f"Idle_Float_{tier}", "1.7 Idle Float / Gentle Hover",
            f"Continuous hover for static PNGs/screenshots: ±{amp * 100:g}% vertical bob with ±{rot:g}° sway "
            f"(sine, {2 * period} frames ≈ {2 * period / 25:g} s, loops seamlessly – extend by copying keyframes).",
            2 * period,
            [transform(kf(*[(f, "~", p.rect(1.0, 0, -amp * math.sin(2 * math.pi * f / period))) for f in keys]),
                       kf(*[(f, "~", f"{rot * math.cos(2 * math.pi * f / period):.2f}")
                            for f in keys])),
             blur_kf((0, 0))], tags=["loop"])

    def c0(tl, tr, br, bl):
        m = lambda v: f"{(v + 1) / 3:.4f}"
        return {"0": m(tl[0]), "1": m(tl[1]), "2": m(tr[0]), "3": m(tr[1]), "4": m(br[0]), "5": m(br[1]),
                "6": m(bl[0]), "7": m(bl[1]), "8": "0", "9": "0.5", "10": "0.5", "11": "0.166", "12": "1",
                "13": "0.01", "14": "0.5"}  # alpha op Minimum: keep the source transparency
    flat = c0((0, 0), (1, 0), (1, 1), (0, 1))
    for nm, start in [("Left", c0((-0.95, 0.18), (-0.15, 0.02), (-0.15, 0.98), (-0.95, 0.82))),
                      ("Right", c0((1.15, 0.02), (1.95, 0.18), (1.95, 0.82), (1.15, 0.98)))]:
        anim = {k: (kf((0, "h", start[k]), (18, flat[k])) if k in "01234567" and len(k) == 1 else v) for k, v in start.items()}
        add("AFX_Move", f"Card_3D_Swing_In_{nm}", "1.8 Perspective Card Tilt / 3D Swing-In",
            f"Tweet / document / card swings in from the {nm.lower()} in 3D perspective and flattens to face the "
            "viewer (18 frames, cubic ease-out). Uses the Corners effect; works without Drop Shadow (any 24.08+).", 18,
            [("frei0r.c0rners", anim), blur_kf((0, 3), (12, 0))])

    def hinge(px, py, theta, frames=24, step=1):
        keys = [(f, theta(f / frames)) for f in range(0, frames + 1, step)]
        return [transform(kf(*[(f, "", pivot_rect(p, a, px, py)) for f, a in keys]),
                          kf(*[(f, "", f"{a:.2f}") for f, a in keys])), blur_kf((0, 2), (8, 0))]
    damped = lambda t, a0: a0 * math.exp(-4.0 * t) * math.cos(1.5 * math.pi * t) if t < 1 else 0.0
    add("AFX_Move", "Hinge_Swing_In_Top_Left", "1.9 Hinge / Pendulum Swing-In",
        "Swings down into frame around its top-left corner like a sign on a hinge, then settles with a "
        "small decaying swing (24 frames).", 24, hinge(0, 0, lambda t: damped(t, -95)))
    add("AFX_Move", "Hinge_Swing_In_Top_Right", "1.9 Hinge / Pendulum Swing-In",
        "Mirror of Hinge Swing-In Top-Left – pivots around the top-right corner.", 24,
        hinge(1, 0, lambda t: damped(t, 95)))
    add("AFX_Move", "Pendulum_Swing_Settle", "1.9 Hinge / Pendulum Swing-In",
        "Hangs from the top-centre and swings like a pendulum (±25°, decaying over 36 frames) – hanging "
        "signs, price tags, name cards.", 36,
        [*hinge(0.5, 0, lambda t: 25 * math.exp(-2.2 * t) * math.cos(2 * math.pi * 1.25 * t) if t < 1 else 0.0, 36)])

    margin = 0.03
    for nm, ax, ay in [("Top_Left", 0, 0), ("Top_Right", 1, 0), ("Bottom_Left", 0, 1), ("Bottom_Right", 1, 1)]:
        dx = margin if ax == 0 else -margin
        dy = margin * p.W / p.H if ay == 0 else -margin * p.W / p.H
        if p.H > p.W:
            dx, dy = (margin * p.H / p.W if ax == 0 else -margin * p.H / p.W), (margin if ay == 0 else -margin)
        add("AFX_Move", f"PiP_Snap_{nm}", "1.10 Corner PiP Snap",
            f"Shrinks a full-screen clip to a 32% picture-in-picture and snaps it into the {nm.replace('_', '-').lower()} "
            "corner with rounded edges (12 frames, cubic ease-out). For a border/shadow add "
            "'OuzFX AFX_Util_Drop_Shadow_Polish' after it.", 12,
            [crop(p.full(), kf((0, "h", "0"), (12, "0.08"))),
             transform(kf((0, "h", p.rect(1.0)), (12, p.rect(0.32, dx, dy, ax=ax, ay=ay))))])

    # text / title movement
    add("AFX_Move", "Text_Word_Pop_Shorts", "5.1 Short-Form Word Pop",
        "TikTok/Reels/Shorts caption pop: 85% → 105% → 100% in 4 frames. Faster and subtler than "
        "'Text · Text Pop' – drop it on every caption clip.", 4,
        [transform(kf((0, "e", p.rect(0.85, o=0.4)), (2, "f", p.rect(1.05)), (4, p.rect(1.0)))), blur_kf((0, 0))],
        tags=["fast"])
    for tier, fr in [("Fast", 25), ("Slow", 50)]:
        add("AFX_Move", f"Text_Typewriter_Wipe_{tier}", "5.3 Typewriter Line Wipe",
            f"Linear left-to-right crop reveal that uncovers a line of text over {fr} frames "
            f"({fr / 25:g} s @25 fps). Put it on a title clip; drag the last keyframe to change the speed.", fr,
            [crop(kf((0, f"0 0 1 {p.H}"), (fr, p.full()))), blur_kf((0, 0))])
    jit = [(0, 0.0, 0.0), (1, 0.012, 1.0), (2, -0.008, 0.15), (3, 0.006, 1.0), (4, -0.004, 0.55), (5, 0.0, 1.0), (6, 0.0, 1.0)]
    add("AFX_Move", "Text_Glitch_In", "5.4 Glitch-In Title",
        "Title flickers on: erratic opacity drops, tiny horizontal jitter and RGB tearing over the first "
        "6 frames, then locks steady.", 6,
        [transform(kf(*[(f, "|", p.rect(1.0, dx, 0, o=o)) for f, dx, o in jit])),
         ("avfilter.rgbashift", {"av.rh": kf((0, "|", 0), (1, "|", 14), (2, "|", -10), (3, "|", 8), (4, "|", -4), (5, "|", 0), (6, 0)),
                                 "av.bh": kf((0, "|", 0), (1, "|", -14), (2, "|", 10), (3, "|", -8), (4, "|", 4), (5, "|", 0), (6, 0)),
                                 "av.edge": "smear"})], tags=["fast"])

    # ================================================================ AFX_Cam
    for tier, fr, amp, s, rotk, b in [("Light", 10, 0.008, 1.04, 50, 1), ("Medium", 15, 0.018, 1.07, 70, 3)]:
        ks = decay_shake(300 + fr, fr, amp, 1 if fr <= 10 else 2)
        add("AFX_Cam", f"Impact_Shake_{tier}", "2.4 Impact Shake (Light / Medium / Heavy)",
            f"{tier} decaying X/Y + rotational jitter ({fr} frames) for bass hits, desk slams and small impacts. "
            "Heavy tier = 'Shake · Heavy Impact'.", fr,
            [transform(kf(*[(f, "", p.rect(s, x, y)) for f, x, y in ks]), kf(*[(f, "", f"{x * rotk:.2f}") for f, x, y in ks])),
             blur_kf((0, b), (fr // 2, 0))], tags=["fast"])

    for nm, dx, dy, ang in [("Right", 1.0, 0, 0), ("Up", 0, -1.0, 90), ("Down", 0, 1.0, 90)]:
        add("AFX_Cam", f"Whip_Pan_Push_{nm}", "2.5 Whip Pan Push (4 Directions)",
            f"Last 8 frames of a clip: whips the picture out {nm.lower()} with heavy directional blur. Razor 8 frames "
            "before the cut and drop it on the right-hand piece (left version = 'Fast · Motion-Blur Push Left').", 8,
            [transform(kf((0, "p", p.rect(1.0)), (8, p.rect(1.0, dx, dy)))), dblur_kf(ang, (0, 0), (3, 70), (8, 160))],
            tags=["fast"])

    beat = []
    for b0 in (0, 36):
        beat += [(b0, "f", 1.0, 1.0), (b0 + 3, "e", 1.035, 0.94), (b0 + 7, "f", 1.0, 1.0), (b0 + 10, "e", 1.05, 0.9), (b0 + 16, "", 1.0, 1.0)]
    beat.append((72, "", 1.0, 1.0))
    add("AFX_Cam", "Heartbeat_Pulse", "2.6 Heartbeat Pulse",
        "Two 'lub-dub' heartbeats (≈ 70 BPM, 72 frames): a small 103.5% swell, a bigger 105% one, with a matching "
        "darkening throb. Builds tension; copy keyframes to extend.", 72,
        [transform(kf(*[(f, t, p.rect(s)) for f, t, s, _ in beat])),
         ("brightness", {"level": kf(*[(f, t, f"{l:g}") for f, t, _, l in beat])})])

    for tier, deg in [("Subtle_8deg", 8), ("Strong_15deg", 15)]:
        keys = []
        for f in range(0, 21, 2):
            a = deg * ease_in_out(f / 20)
            keys.append((f, a, cover_scale(p, a)))
        add("AFX_Cam", f"Dutch_Angle_{tier}", "2.7 Dutch Angle Tilt",
            f"Eases the horizon to a {deg}° Dutch angle over 20 frames and holds, auto-zooming just enough "
            f"({cover_scale(p, deg) * 100:.0f}%) that no black corners show. Suspense / confusion / surreal beats.", 20,
            [transform(kf(*[(f, "", p.rect(s)) for f, a, s in keys]), kf(*[(f, "", f"{a:.2f}") for f, a, s in keys])),
             blur_kf((0, 0))])

    for nm, ax, ay in [("Top_Left", 0, 0), ("Top_Right", 1, 0), ("Bottom_Left", 0, 1), ("Bottom_Right", 1, 1)]:
        add("AFX_Cam", f"Zoom_Callout_Return_{nm}", "3.6 Magnifying Zoom Callout",
            f"Return half of the callout: from the 180% {nm.replace('_', '-').lower()} zoom (Screen Zoom · Zoom to "
            f"{nm.replace('_', '-')}) smoothly back to 100% in 15 frames. Razor where the callout ends.", 15,
            [transform(kf((0, "i", p.rect(1.8, ax=ax, ay=ay)), (15, p.rect(1.0, ax=ax, ay=ay)))),
             blur_kf((0, 0), (5, 2), (12, 0))])

    add("AFX_Cam", "Cinematic_Bars_Slide_Out", "2.8 Cinematic Letterbox Reveal",
        "Out half of the letterbox: 2.39:1 bars retract over 15 frames, leaving 'movie mode'. Pair with "
        "'Look · Cinematic Bars Slide-In'.", 15,
        [crop(kf((0, "h", p.bars(2.39)), (15, p.full())), color="0x000000ff"), blur_kf((0, 0))])

    # ================================================================ AFX_Util
    for nm, a, b, ease in [("In", (1.0, 0), (0.55, 14), "h"), ("Out", (0.55, 14), (1.0, 0), "h")]:
        add("AFX_Util", f"BG_Dim_Blur_{nm}", "3.1 Background Dim & Blur",
            ("Background layer: dims to 55% and blurs over 12 frames so text / overlays on the track above become legible."
             if nm == "In" else "Brings a dimmed + blurred background back to normal over 12 frames (pair with Dim_Blur_In)."), 12,
            [("brightness", {"level": kf((0, ease, f"{a[0]:g}"), (12, f"{b[0]:g}"))}),
             ("avfilter.gblur", {"av.sigma": kf((0, ease, a[1]), (12, b[1])), "av.sigmaV": kf((0, ease, a[1]), (12, b[1])),
                                 "av.steps": "1", "av.planes": "15"})])

    for nm, l0, l1 in [("In", 1.0, 0.42), ("Out", 0.42, 1.0)]:
        add("AFX_Util", f"Spotlight_Focus_{nm}", "3.2 Spotlight Vignette Focus",
            ("Animated spotlight: everything outside a soft ellipse darkens to 42% over 15 frames, pulling the eye to "
             "the subject. Move/resize the ellipse in the Alpha shapes effect." if nm == "In" else
             "Releases the spotlight: the darkened edges brighten back to normal over 15 frames."), 15,
            [spot(0.38, 0.5, 0.5, 0.30, 0.42, 0.35, 0, 1, "1"),
             ("brightness", {"level": kf((0, "h", f"{l0:g}"), (15, f"{l1:g}"))}), MASK_APPLY])

    band = f"{p.W * 0.1:.0f} {p.H * 0.45:.0f} {p.W * 0.8:.0f} {p.H * 0.09:.0f} 0.45"
    add("AFX_Util", "Highlighter_Wipe", "3.3 Highlighter Wipe",
        "Put it on a yellow Color clip above an article/PDF shot: a 45%-opacity marker band wipes on left-to-right "
        "in 12 frames. Move/resize the Transform rectangle over the line you want to highlight.", 12,
        [crop(kf((0, "h", f"0 0 1 {p.H}"), (12, p.full()))),
         ("qtblend", {"rect": band, "rotation": "0", "compositing": "0", "distort": "1"})])

    halves = {"Left": (p.full_part(0.25, 0, 0.5, 1), -0.25, 0), "Right": (p.full_part(0.25, 0, 0.5, 1), 0.25, 0),
              "Top": (p.full_part(0, 0.25, 1, 0.5), 0, -0.25), "Bottom": (p.full_part(0, 0.25, 1, 0.5), 0, 0.25)}
    for nm, (mask, dx, dy) in halves.items():
        pair = {"Left": "Right", "Right": "Left", "Top": "Bottom", "Bottom": "Top"}[nm]
        add("AFX_Util", f"Split_Screen_{nm}", "3.4 Split-Screen Presets",
            f"Crops the centre of the clip and places it in the {nm.lower()} half. Put the partner clip on another track "
            f"with Split_Screen_{pair}. {'Top/Bottom = stacked layout for vertical Shorts/Reels.' if nm in ('Top', 'Bottom') else ''}", 0,
            [crop(mask), transform(p.rect(1.0, dx, dy))])
        ox = dx * 4 if dx else 0
        oy = dy * 4 if dy else 0
        add("AFX_Util", f"Split_Screen_{nm}_Slide_In", "3.4 Split-Screen Presets",
            f"Same as Split_Screen_{nm}, but the half slides in from the {nm.lower()} edge (15 frames, cubic ease-out).", 15,
            [crop(mask), transform(kf((0, "h", p.rect(1.0, ox, oy)), (15, p.rect(1.0, dx, dy))))])

    add("AFX_Util", "Censor_Pixelate_Box", "3.5 Censor / Redact Blur Box",
        "Mosaic-pixelates a rectangle in the middle of the frame. Move/resize/keyframe it in the Alpha shapes effect "
        "(Position/Size) to cover faces, usernames or private data.", 0,
        [spot(0, 0.5, 0.5, 0.22, 0.25, 0.0, 0, 1), ("frei0r.pixeliz0r", {"0": "0.025", "1": "0.045", "2": "0",
                                # frei0r 1.x parameter names (Kdenlive <= 25.x), same values
                                "BlockSizeX": "0=0.025", "BlockSizeY": "0=0.045"}), MASK_APPLY])
    add("AFX_Util", "Censor_Blur_Box", "3.5 Censor / Redact Blur Box",
        "Heavy Gaussian blur inside a soft-edged rectangle – a less blocky redaction. Move/resize it in the Alpha "
        "shapes effect.", 0,
        [spot(0, 0.5, 0.5, 0.22, 0.25, 0.02, 0, 1),
         ("avfilter.gblur", {"av.sigma": "40", "av.sigmaV": "40", "av.steps": "3", "av.planes": "15"}), MASK_APPLY])

    add("AFX_Util", "Drop_Shadow_Polish", "5.5 Drop Shadow Polish",
        "Static two-layer shadow for text / PNG cut-outs: a crisp, slightly offset contact shadow plus a soft "
        "ambient one. No keyframes, so it never fights your animation. Needs Kdenlive 25.04+.", 0,
        [("dropshadow", {"radius": "3", "x": "5", "y": "6", "color": "#c8000000"}),
         ("dropshadow", {"radius": "18", "x": "0", "y": "16", "color": "#80000000"})])

    # ================================================================ AFX_Style
    add("AFX_Style", "Record_Scratch_Freeze", "4.3 Dramatic Desaturate ('Record Scratch' Freeze)",
        "Instant high-contrast black & white with a slow 100→110% push over 3 s – the 'yep, that's me' "
        "record-scratch moment. Combine with a freeze frame (Timeline ▸ Insert Freeze Frame).", 75,
        [("greyscale", {}), ("frei0r.contrast0r", {"Contrast": "0.72"}),
         transform(kf((0, "c", p.rect(1.0)), (75, p.rect(1.10))))])
    fl = [(0, 0, 1.0), (1, 0.02, 0.25), (2, -0.015, 1.0), (3, 0, 1.0), (5, 0.03, 0.1), (6, -0.01, 0.8), (8, 0, 1.0),
          (9, 0.015, 0.4), (10, 0, 1.0), (12, 0, 1.0)]
    add("AFX_Style", "Glitch_Flicker", "4.6 Glitch Flicker",
        "12 frames of erratic opacity drops with horizontal displacement and light block distortion – a "
        "signal-dropout flicker (use on footage over a background).", 12,
        [transform(kf(*[(f, "|", p.rect(1.0, dx, 0, o=o)) for f, dx, o in fl])),
         ("frei0r.glitch0r", {"0": kf((0, 0.5), (6, 0.3), (12, 0.0)), "1": "0.1", "2": kf((0, 0.3), (6, 0.2), (12, 0.0)),
                              "3": kf((0, 0.3), (6, 0.2), (12, 0.0))})], tags=["fast"])
    pulse = []  # (frame, easing, ellipse size): huge ellipse = no tint, small = red edges
    for i in range(3):
        pulse += [(i * 12, "e", 2.2), (i * 12 + 3, "f", 0.42)]
    pulse.append((36, "", 2.2))
    dmg = spot(0.38, 0.5, 0.5, 0.36, 0.40, 0.35, 0, 1, "1")
    dmg[1]["filter.Size X"] = kf(*[(f, t, f"{v * 0.9:g}") for f, t, v in pulse])
    dmg[1]["filter.Size Y"] = kf(*[(f, t, f"{v:g}") for f, t, v in pulse])
    add("AFX_Style", "Damage_Pulse_Red", "4.7 Red Alert / Damage Pulse",
        "Gaming 'taking damage' / warning: the screen edges pulse red three times (36 frames) while the centre "
        "stays clean. Edge ellipse is adjustable in the Alpha shapes effect.", 36,
        [dmg, ("frei0r.colorize", {"hue": "0.0", "saturation": "0.95", "lightness": "0.42"}),
         MASK_APPLY], tags=["fast"])

    # ================================================================ AFX_Audio
    def lp(f, poles="2"):
        return ("avfilter.lowpass", {"av.f": str(f), "av.t": "q", "av.w": "0.707", "av.p": poles, "av.m": "1"})

    def hp(f, poles="2"):
        return ("avfilter.highpass", {"av.f": str(f), "av.t": "q", "av.w": "0.707", "av.p": poles, "av.m": "1"})

    def eq(f, g, w=1.0):
        return ("avfilter.equalizer", {"av.f": str(f), "av.t": "q", "av.w": str(w), "av.g": str(g), "av.m": "1"})

    add("AFX_Audio", "Underwater_Muffled", "6.1 Underwater / Muffled Room",
        "Steep 24 dB/oct low-pass at 450 Hz (two stacked filters) with a little low-end warmth – audio behind a "
        "closed door, under water or in the next room.", 0,
        [lp(450), lp(450), eq(120, 3)], audio=True)
    def squash(drive, limit):
        # Kdenlive hides FFmpeg's acompressor/aecho (data/excluded_effects.txt), so dynamics use the
        # included Limiter: input drive into a fast limiter = hard 'radio' compression.
        return ("avfilter.alimiter", {"av.level_in": str(drive), "av.level_out": "1", "av.limit": str(limit),
                                      "av.attack": "2", "av.release": "40", "av.asc": "0", "av.level": "0"})

    def delay(metres, wet):
        # avfilter.compensationdelay: one echo tap (distance / speed of sound), dry signal kept
        return ("avfilter.compensationdelay", {"av.mm": "0", "av.cm": "0", "av.m": str(metres), "av.dry": "1",
                                               "av.wet": str(wet), "av.temp": "20"})

    add("AFX_Audio", "Telephone_Voice", "6.2 Walkie-Talkie / Telephone Voice",
        "Clean phone line: 400–3200 Hz band-pass (24 dB/oct top), a presence bump and limiter-squash compression.", 0,
        [hp(400), lp(3200), lp(3200), eq(1500, 5, 0.8), squash(2.5, 0.6)], audio=True)
    add("AFX_Audio", "Walkie_Talkie_Radio", "6.2 Walkie-Talkie / Telephone Voice",
        "Narrow 500–2600 Hz radio band with light bit-crush overdrive and hard limiter compression – walkie-talkie / "
        "police radio callouts.", 0,
        [hp(500), lp(2600), lp(2600),
         ("avfilter.acrusher", {"av.bits": "7", "av.mix": "0.35", "av.mode": "log", "av.aa": "0.7", "av.samples": "1"}),
         squash(4, 0.5)], audio=True)
    add("AFX_Audio", "Hall_Echo_Reverb", "6.3 Dramatic Echo / Hall Reverb",
        "Spacious multi-tap hall echo: three cascaded delays (≈60, 260 and 295 ms → taps up to ~0.6 s) with a "
        "safety limiter. Ominous moments, inner monologue, punchlines. Lower the 'wet' values for a subtler room.", 0,
        [delay(20, 0.55), delay(90, 0.5), delay(100, 0.45), lp(6000), squash(1, 0.89)], audio=True)
    add("AFX_Audio", "Voiceover_Quick_Polish", "6.4 Voiceover Quick Polish",
        "Starter vocal chain: 80 Hz high-pass (mic rumble), gentle loudness leveling towards -18 LUFS (Kdenlive's "
        "Dynamic Loudness, ±6 dB) and a -1 dBFS safety limiter.", 0,
        [hp(80),
         ("dynamic_loudness", {"target_loudness": "-18", "window": "2", "max_gain": "6", "min_gain": "-6", "max_rate": "3"}),
         squash(1.2, 0.89)], audio=True)
    return T


def afx_compositions():
    C = []

    def add(name, bp, desc, tag, values):
        C.append(dict(slug=f"afx_cam_{name.lower()}", category="AFX_Cam", name=name, desc=desc, tag=tag,
                      values=values, tags=[], bp=bp))
    add("Ken_Burns_Pan_Right_to_Left", "2.2 Smooth Ken Burns Drift",
        "Pans across a 120% image from right to left over the whole composition length (companion of Pan L→R).",
        "affine", {"rect": f"0c={R(-20, -10, 120, 120)};-1={R(0, -10, 120, 120)}"})
    add("Ken_Burns_Pan_Up", "2.2 Smooth Ken Burns Drift",
        "Tilts up across a 120% image (bottom → top) over the composition length – tall photos, buildings.",
        "affine", {"rect": f"0c={R(-10, -20, 120, 120)};-1={R(-10, 0, 120, 120)}"})
    add("Ken_Burns_Pan_Down", "2.2 Smooth Ken Burns Drift",
        "Tilts down across a 120% image (top → bottom) over the composition length.",
        "affine", {"rect": f"0c={R(-10, 0, 120, 120)};-1={R(-10, -20, 120, 120)}"})
    return C

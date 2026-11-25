"""OuzFX v1.2 – Out counterparts for intro animations that had none.

Every item names the intro it mirrors in `pair` (preset id) – used by tools/blueprint.py
for the In/Out table and by tools/out_tests.py for the continuity check (first Out frame
== last In frame).

Timing: Kdenlive re-bases effect-template keyframes on the clip START and drops
negative (end-relative) keyframes when a template is applied (KeyframeModel::
getAnimationStringWithOffset serializes with length 0), so Out *effect templates* are
built like the v1.0/v1.1 whip pushes: razor N frames before the end of the clip, drop the
template on that last piece; the final keyframe sits on the piece's last frame (N-1), so
the layer is completely gone on the last frame and stays gone if the piece is longer.
Out *compositions* use 0= / -1= keyframes and therefore always end exactly at the end of
the composition, whatever its length (same as the v1.0 Slide/Pop/Spin Out compositions).
"""
import math

from presets import P, kf, blur_kf, dblur_kf, transform, R, FULL
from presets_afx import pivot_rect, cover_scale, ease_in_out, crop

C1 = 1.70158
back_in = lambda t: (C1 + 1) * t ** 3 - C1 * t ** 2


def out_templates(p: P):
    T = []

    def add(cat, name, pair, desc, frames, effects, end="gone", tags=()):
        slug = f"afx_{cat.split('_')[1].lower()}_{name.lower()}"
        T.append(dict(slug=slug, category=cat, name=name, desc=desc, frames=frames, effects=effects,
                      tags=list(tags), pair=pair, end=end, audio=False))

    def razor(n):
        return (f"Razor {n} frames before the end of the clip and drop it on that last piece – the layer is gone on "
                f"the last frame (anything after stays hidden).")

    # ---------------------------------------------------------------- whip
    for nm, dx, dy, ang, inslug in [("Left", -1.1, 0, 0, "left"), ("Right", 1.1, 0, 0, "right"),
                                    ("Up", 0, -1.1, 90, "top"), ("Down", 0, 1.1, 90, "bottom")]:
        add("AFX_Move", f"Whip_Slide_Out_{nm}", f"ouzfx_anim_slide_in_{inslug}",
            f"Whip-slide OUT to the {nm.lower()}: accelerates off-screen (expo ease-in) while directional motion blur "
            f"builds up – the exact mirror of 'Anim · Slide In from {inslug.title()}' (12 frames). {razor(12)} "
            "Faster 6–8 frame camera-push tier: 'Fast · Motion-Blur Push Left' / 'AFX_Cam_Whip_Pan_Push_*'.", 12,
            [transform(kf((0, "p", p.rect(1.0)), (11, p.rect(1.0, dx, dy)))),
             dblur_kf(ang, (0, 0), (6, 10), (11, 60))], tags=["fast"])

    # ---------------------------------------------------------------- overshoot
    for nm, sx, sy in [("Left", -1, 0), ("Right", 1, 0), ("Top", 0, -1), ("Bottom", 0, 1)]:
        ang = 0 if sy == 0 else 90
        add("AFX_Move", f"Overshoot_Slide_Out_{nm}", f"ouzfx_afx_move_overshoot_slide_in_{nm.lower()}",
            f"Anticipation exit, the exact time-reverse of Overshoot_Slide_In_{nm}: winds up the other way (Kdenlive/MLT "
            f"back ease-in, ≈ 37% of the travel), then shoots out to the {nm.lower()} with a motion-blur tail "
            f"(14 frames). {razor(14)}", 14,
            [transform(kf((0, "v", p.rect(1.0)), (13, p.rect(1.0, 1.05 * sx, 1.05 * sy)))),
             dblur_kf(ang, (0, 0), (8, 6), (13, 40))], tags=["fast"])

    # ---------------------------------------------------------------- masked edge
    reveals = [("Up", 0, 0.5, p.full_part(0, 0, 1, 0.5)), ("Down", 0, -0.5, p.full_part(0, 0.5, 1, 0.5)),
               ("Left", 0.5, 0, p.full_part(0, 0, 0.5, 1)), ("Right", -0.5, 0, p.full_part(0.5, 0, 0.5, 1))]
    for nm, dx, dy, mask in reveals:
        add("AFX_Move", f"Masked_Edge_Reveal_{nm}_Out", f"ouzfx_afx_move_masked_edge_reveal_{nm.lower()}",
            f"Out half of Masked_Edge_Reveal_{nm}: the layer slides back into the invisible line it came from "
            f"(15 frames, expo ease-in). {razor(15)}", 15,
            [transform(kf((0, "p", p.rect(1.0)), (14, p.rect(1.0, dx, dy)))), crop(mask)])

    # ---------------------------------------------------------------- v1.0 intros without an Out
    add("AFX_Move", "Bounce_Drop_Out", "ouzfx_anim_bounce_in",
        "Mirror of 'Anim · Bounce In (Drop)': a few growing hops on the floor, then it launches out of the top "
        f"(20 frames, bounce ease-in). {razor(20)}", 20,
        [transform(kf((0, "B", p.rect(1.0)), (19, p.rect(1.0, 0, -1.05)))), blur_kf((0, 0))])
    add("AFX_Move", "Elastic_Zoom_Out", "ouzfx_anim_elastic_in",
        "Mirror of 'Anim · Elastic Zoom-In': wobbles, then snaps down to 40% and vanishes (20 frames, elastic "
        f"ease-in). {razor(20)}", 20,
        [transform(kf((0, "y", p.rect(1.0)), (19, p.rect(0.4, o=0)))), blur_kf((0, 0))])
    add("AFX_Move", "Blur_Out", "ouzfx_anim_blur_in",
        f"Mirror of 'Anim · Blur-In': dissolves into a heavy blur while fading out and growing to 104% (15 frames). "
        f"{razor(15)}", 15,
        [("avfilter.gblur", {"av.sigma": kf((0, "g", 0), (14, 40)), "av.sigmaV": kf((0, "g", 0), (14, 40)),
                             "av.steps": "1", "av.planes": "15"}),
         transform(kf((0, "g", p.rect(1.0)), (14, p.rect(1.04, o=0))))])

    # perspective screen (same stack as the v1.0 Perspective Screen presets – Drop Shadow = Kdenlive 25.04+)
    def c0(tl, tr, br, bl, alpha="0"):
        m = lambda v: f"{(v + 1) / 3:.4f}"
        return {"0": m(tl[0]), "1": m(tl[1]), "2": m(tr[0]), "3": m(tr[1]), "4": m(br[0]), "5": m(br[1]),
                "6": m(bl[0]), "7": m(bl[1]), "8": "0", "9": "0.5", "10": "0.5", "11": "0.166", "12": "1",
                "13": "0.01", "14": alpha}

    def corners_anim(a, b, frames, ease):
        return {k: (kf((0, ease, a[k]), (frames, b[k])) if len(k) == 1 and k in "01234567" else v) for k, v in a.items()}
    rounded = ("qtcrop", {"rect": p.full(), "radius": "0.035", "circle": "0", "color": "0x00000000"})
    shadow = ("dropshadow", {"radius": "25", "x": "14", "y": "22", "color": "#a0000000"})
    tilt = c0((0.06, 0.16), (0.90, 0.06), (0.90, 0.94), (0.06, 0.84))
    flat = c0((0.09, 0.09), (0.91, 0.09), (0.91, 0.91), (0.09, 0.91))
    tiny = c0((0.48, 0.48), (0.52, 0.48), (0.52, 0.52), (0.48, 0.52))
    add("AFX_Move", "Screen_Swing_Back_Out", "ouzfx_screen_tilt_to_flat",
        "Out half of 'Screen 3D · Swing to Front': the flat floating panel swings back to the tilted-left 3D view "
        "(25 frames, cubic ease-in). Razor 25 frames before the end. Kdenlive 25.04+ (Drop Shadow).", 25,
        [rounded, ("frei0r.c0rners", corners_anim(flat, tilt, 24, "g")), shadow], end="changed")
    add("AFX_Move", "Screen_Pop_Out", "ouzfx_screen_pop_in",
        "Out half of 'Screen 3D · Floating Screen · Pop In': the floating window anticipates, collapses to the centre "
        f"and fades (18 frames, back ease-in). {razor(18)} Kdenlive 25.04+ (Drop Shadow).", 18,
        [rounded, ("frei0r.c0rners", corners_anim(flat, tiny, 17, "v")), shadow,
         transform(kf((0, "g", p.rect(1.0)), (17, p.rect(1.0, o=0))))])

    # ---------------------------------------------------------------- card / hinge
    cflat = c0((0, 0), (1, 0), (1, 1), (0, 1), "0.5")
    for nm, end in [("Left", c0((-0.95, 0.18), (-0.15, 0.02), (-0.15, 0.98), (-0.95, 0.82), "0.5")),
                    ("Right", c0((1.15, 0.02), (1.95, 0.18), (1.95, 0.82), (1.15, 0.98), "0.5"))]:
        add("AFX_Move", f"Card_3D_Swing_Out_{nm}", f"ouzfx_afx_move_card_3d_swing_in_{nm.lower()}",
            f"Card / tweet / document turns away in 3D perspective and swings out to the {nm.lower()} (18 frames, "
            f"cubic ease-in). Mirror of Card_3D_Swing_In_{nm}. {razor(18)}", 18,
            [("frei0r.c0rners", corners_anim(cflat, end, 17, "g")), blur_kf((0, 0), (6, 0), (17, 3))])

    def hinge(px, py, theta, frames):
        keys = [(f, theta(f / (frames - 1))) for f in range(frames)]
        return [transform(kf(*[(f, "", pivot_rect(p, a, px, py)) for f, a in keys]),
                          kf(*[(f, "", f"{a:.2f}") for f, a in keys])), blur_kf((0, 0), (10, 0), (frames - 1, 3))]
    for nm, px, a1 in [("Top_Left", 0, -95), ("Top_Right", 1, 95)]:
        add("AFX_Move", f"Hinge_Swing_Out_{nm}", f"ouzfx_afx_move_hinge_swing_in_{nm.lower()}",
            f"Out half of Hinge_Swing_In_{nm}: dips the other way, then swings up and away around the "
            f"{nm.replace('_', '-').lower()} corner (16 frames, back ease-in). {razor(16)}", 16,
            hinge(px, 0, lambda t: a1 * back_in(t), 16))

    # ---------------------------------------------------------------- PiP
    margin = 0.03
    for nm, ax, ay in [("Top_Left", 0, 0), ("Top_Right", 1, 0), ("Bottom_Left", 0, 1), ("Bottom_Right", 1, 1)]:
        dx = margin if ax == 0 else -margin
        dy = margin * p.W / p.H if ay == 0 else -margin * p.W / p.H
        if p.H > p.W:
            dx, dy = (margin * p.H / p.W if ax == 0 else -margin * p.H / p.W), (margin if ay == 0 else -margin)
        add("AFX_Move", f"PiP_Snap_{nm}_Out", f"ouzfx_afx_move_pip_snap_{nm.lower()}",
            f"Out half of PiP_Snap_{nm}: the 32% corner picture grows back to full screen and loses its rounded "
            "corners (12 frames, cubic ease-in). Razor where the PiP should end and drop it on the right-hand piece "
            "(after PiP_Snap_" + nm + ").", 12,
            [crop(p.full(), kf((0, "g", "0.08"), (11, "0"))),
             transform(kf((0, "g", p.rect(0.32, dx, dy, ax=ax, ay=ay)), (11, p.rect(1.0))))], end="rest")

    # ---------------------------------------------------------------- text
    add("AFX_Move", "Text_Word_Pop_Shorts_Out", "ouzfx_afx_move_text_word_pop_shorts",
        "Caption pop OUT for Shorts/Reels: 100% → 105% → 85% and gone in 4 frames (mirror of Text_Word_Pop_Shorts). "
        "Drop it on the last 4 frames of a caption clip.", 4,
        [transform(kf((0, "e", p.rect(1.0)), (1, "d", p.rect(1.05)), (3, p.rect(0.85, o=0)))), blur_kf((0, 0))],
        tags=["fast"])
    add("AFX_Move", "Text_Rise_Fade_Out", "ouzfx_text_rise",
        f"Lower-third exit, mirror of 'Text · Text Rise': sinks 6% while fading out (12 frames, cubic ease-in). {razor(12)}",
        12, [transform(kf((0, "g", p.rect(1.0)), (11, p.rect(1.0, 0, 0.06, o=0)))), blur_kf((0, 0), (4, 0), (11, 2))])
    for tier, fr in [("Fast", 25), ("Slow", 50)]:
        add("AFX_Move", f"Text_Typewriter_Wipe_{tier}_Out", f"ouzfx_afx_move_text_typewriter_wipe_{tier.lower()}",
            f"Backspace-style exit: a linear right-to-left crop erases the line over {fr} frames (mirror of "
            f"Text_Typewriter_Wipe_{tier}). {razor(fr)}", fr,
            [crop(kf((0, p.full()), (fr - 1, f"0 0 1 {p.H}"))), blur_kf((0, 0))])
    jit = [(0, 0.0, 1.0), (1, 0.0, 1.0), (2, -0.004, 0.55), (3, 0.006, 1.0), (4, -0.008, 0.15), (5, 0.012, 1.0), (6, 0.0, 0.0)]
    rh = [0, 0, -4, 8, -10, 14, 0]
    add("AFX_Move", "Text_Glitch_Out", "ouzfx_afx_move_text_glitch_in",
        "Title glitches off: steady, then erratic opacity drops, jitter and RGB tearing until it is gone on frame 6 "
        "(mirror of Text_Glitch_In). Drop it on the last 7 frames of the title.", 7,
        [transform(kf(*[(f, "|", p.rect(1.0, dx, 0, o=o)) for f, dx, o in jit])),
         ("avfilter.rgbashift", {"av.rh": kf(*[(f, "|" if f < 6 else "", v) for f, v in enumerate(rh)]),
                                 "av.bh": kf(*[(f, "|" if f < 6 else "", -v) for f, v in enumerate(rh)]),
                                 "av.edge": "smear"})], tags=["fast"])

    # ---------------------------------------------------------------- AFX_Util / AFX_Cam
    halves = {"Left": (p.full_part(0.25, 0, 0.5, 1), -0.25, 0), "Right": (p.full_part(0.25, 0, 0.5, 1), 0.25, 0),
              "Top": (p.full_part(0, 0.25, 1, 0.5), 0, -0.25), "Bottom": (p.full_part(0, 0.25, 1, 0.5), 0, 0.25)}
    for nm, (mask, dx, dy) in halves.items():
        add("AFX_Util", f"Split_Screen_{nm}_Slide_Out", f"ouzfx_afx_util_split_screen_{nm.lower()}_slide_in",
            f"Out half of Split_Screen_{nm}_Slide_In: the {nm.lower()} half slides back out of its edge (15 frames, "
            f"cubic ease-in). {razor(15)}", 15,
            [crop(mask), transform(kf((0, "g", p.rect(1.0, dx, dy)), (14, p.rect(1.0, dx * 4, dy * 4))))])
    band = f"{p.W * 0.1:.0f} {p.H * 0.45:.0f} {p.W * 0.8:.0f} {p.H * 0.09:.0f} 0.45"
    add("AFX_Util", "Highlighter_Wipe_Out", "ouzfx_afx_util_highlighter_wipe",
        f"Out half of Highlighter_Wipe: the marker band retracts right-to-left (12 frames, cubic ease-in). {razor(12)}",
        12, [crop(kf((0, "g", p.full()), (11, f"0 0 1 {p.H}"))),
             ("qtblend", {"rect": band, "rotation": "0", "compositing": "0", "distort": "1"})])
    for tier, deg in [("Subtle_8deg", 8), ("Strong_15deg", 15)]:
        keys = []
        for f in list(range(0, 19, 2)) + [19]:
            a = deg * (1 - ease_in_out(f / 19))
            keys.append((f, a, cover_scale(p, a) if f < 19 else 1.0))
        add("AFX_Cam", f"Dutch_Angle_{tier}_Out", f"ouzfx_afx_cam_dutch_angle_{tier.lower()}",
            f"Out half of Dutch_Angle_{tier}: eases the horizon from {deg}° back to level and the auto-zoom back to "
            "100% over 20 frames. Razor where the tilt should end and drop it on the right-hand piece.", 20,
            [transform(kf(*[(f, "", p.rect(s)) for f, a, s in keys]), kf(*[(f, "", f"{a:.2f}") for f, a, s in keys])),
             blur_kf((0, 0))], end="rest")
    return T


def out_compositions():
    C = []

    def add(cat, name, pair, desc, tag, values, end="bottom", tags=()):
        C.append(dict(slug=f"afx_{cat.split('_')[1].lower()}_{name.lower()}", category=cat, name=name, desc=desc,
                      tag=tag, values=values, tags=list(tags), pair=pair, end=end))

    for nm, svc, inslug in [("Left", "left", "left"), ("Right", "right", "right"), ("Up", "up", "up"), ("Down", "down", "down")]:
        add("AFX_Cam", f"Whip_Push_Out_{nm}", f"ouzfx_comp_whip_{inslug}",
            f"Whip-pan push transition: the outgoing clip (lower track) whips out to the {nm.lower()} while the incoming "
            f"clip (upper track) pushes in behind it – expo ease-in-out, so it is slow at the edges and a blur-fast "
            "smear in the middle. Overlap the two clips by 6–12 frames and drop it on the overlap. Built on Kdenlive's "
            "Push composition (frei0r sleid0r).", f"frei0r.sleid0r_push-{svc}", {"position": "0r=0;-1=1"},
            end="top", tags=["fast"])
    for nm, sx, sy in [("Left", -1, 0), ("Right", 1, 0), ("Top", 0, -1), ("Bottom", 0, 1)]:
        add("AFX_Move", f"Overshoot_Slide_Out_{nm}_AnyLength", f"ouzfx_afx_move_overshoot_slide_in_{nm.lower()}",
            f"Composition version of Overshoot_Slide_Out_{nm}: the upper clip anticipates and shoots out to the "
            f"{nm.lower()} (back ease-in), always ending exactly at the end of the composition. Put it over the END of "
            "the clip.", "qtblend", {"rect": f"0v={FULL};-1={R(105 * sx, 105 * sy, 100, 100)}"})
    add("AFX_Move", "Bounce_Drop_Out_AnyLength", "ouzfx_anim_bounce_in",
        "Composition version of Bounce_Drop_Out: growing hops, then the upper clip launches out of the top, ending at "
        "the end of the composition.", "qtblend", {"rect": f"0B={FULL};-1={R(0, -105, 100, 100)}"})
    add("AFX_Move", "Elastic_Zoom_Out_AnyLength", "ouzfx_anim_elastic_in",
        "Composition version of Elastic_Zoom_Out: wobble, then the upper clip snaps to 40% and vanishes at the end of "
        "the composition.", "qtblend", {"rect": f"0y={FULL};-1={R(30, 30, 40, 40, 0)}"})
    add("AFX_Move", "Text_Rise_Fade_Out_AnyLength", "ouzfx_text_rise",
        "Composition version of Text_Rise_Fade_Out for a title on the upper track: sinks 6% and fades out by the end "
        "of the composition.", "qtblend", {"rect": f"0g={FULL};-1={R(0, 6, 100, 100, 0)}"})
    add("AFX_Move", "PiP_Corner_Pop_Out", "ouzfx_comp_picture_in_picture",
        "Out half of 'Animations · Picture-in-Picture Corner (Pop)': the 30% bottom-right bubble anticipates and "
        "collapses into the corner by the end of the composition. Put it right after the PiP composition, over the "
        "last frames of the facecam clip.", "qtblend", {"rect": f"0v={R(67, 66, 30, 30)};-1={R(84, 84, 0, 0, 0)}"})
    return C

#!/usr/bin/env python3
"""Blueprint coverage audit (v1.1): maps every item of the 'Kdenlive FX Pack Expansion
Blueprint' to the v1.0 presets that already covered it or to the new AFX files.
Cross-checks the mapping against pack/catalog.json and writes docs/BLUEPRINT_COVERAGE.md.
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

CATS = {"1": "Object & Graphic Movements", "2": "Camera Motion & Framing", "3": "Focus, Callout & Explainer Utilities",
        "4": "Stylistic Visuals & Impact Accents", "5": "Text & Kinetic Title Presets", "6": "Audio FX Presets"}

# id, blueprint item, status, existing v1.0 presets, note
ITEMS = [
    ("1.1", "Smooth Slide-In / Slide-Out (4 directions)", "present",
     ["ouzfx_anim_slide_in_left", "ouzfx_anim_slide_in_right", "ouzfx_anim_slide_in_top", "ouzfx_anim_slide_in_bottom",
      "ouzfx_comp_slide_out_left", "ouzfx_comp_slide_out_right", "ouzfx_comp_slide_out_up", "ouzfx_comp_slide_out_down"],
     "In = effect templates with expo ease-out; Out = compositions with expo ease-in (already split In/Out)."),
    ("1.2", "Overshoot / Bounce Slide", "new", [], "4 directions, back ease-out."),
    ("1.3", "Whip-Slide (with simulated motion blur)", "present",
     ["ouzfx_anim_slide_in_left", "ouzfx_anim_whip_in", "ouzfx_fast_motion_slide_l"],
     "The v1.0 slides already carry a directional-blur peak; Whip-In is the 6-frame fast tier. Missing push directions are added under 2.5."),
    ("1.4", "Masked Edge Reveal", "new", [], "Transform slide + static crop mask, emerges from the centre line (4 directions)."),
    ("1.5", "Elastic Pop-In / Pop-Out", "present",
     ["ouzfx_anim_pop_in", "ouzfx_anim_elastic_in", "ouzfx_comp_pop_in", "ouzfx_comp_pop_out", "ouzfx_text_pop"],
     "Back-overshoot pop-in (0→~108→100%) and anticipation pop-out already exist."),
    ("1.6", "Drop & Gravity Bounce", "present", ["ouzfx_anim_bounce_in"], "Drops from the top edge with bounce easing (decaying rebounds)."),
    ("1.7", "Idle Float / Gentle Hover", "new", [],
     "Closest v1.0 presets (Text Wiggle = fast ±3° wiggle, Walking Bounce = camera bob) are different motions."),
    ("1.8", "Perspective Card Tilt / 3D Swing-In", "partial",
     ["ouzfx_screen_tilt_left", "ouzfx_screen_tilt_right", "ouzfx_screen_tilt_back", "ouzfx_screen_tilt_to_flat"],
     "Static tilts and an in-place swing existed; added the missing swing-IN from off-screen (left/right)."),
    ("1.9", "Hinge / Pendulum Swing-In", "new", [], "Top-left hinge, top-right hinge, top-centre pendulum."),
    ("1.10", "Corner PiP Snap (4 corners)", "partial", ["ouzfx_comp_picture_in_picture"],
     "v1.0 had one bottom-right pop-in composition; added full-screen→corner snaps for all 4 corners (rounded edges, shadow via 5.5)."),
    ("1.11", "Spin-In / Vortex Exit", "present", ["ouzfx_anim_spin_in", "ouzfx_comp_spin_in", "ouzfx_comp_spin_out"], ""),
    ("2.1", "Zoom Punch (In / Out)", "present",
     ["ouzfx_zoom_punch_in", "ouzfx_zoom_punch_in_out", "ouzfx_fast_smash_cut", "ouzfx_zoom_boom"], ""),
    ("2.2", "Smooth Ken Burns Drift (in / out / pan)", "partial",
     ["ouzfx_zoom_ken_burns_in", "ouzfx_zoom_ken_burns_out", "ouzfx_comp_ken_burns_in", "ouzfx_comp_ken_burns_out", "ouzfx_comp_ken_burns_pan"],
     "Zoom in/out and pan L→R existed; added the missing pan directions (R→L, up, down)."),
    ("2.3", "Handheld Camera Sway", "present", ["ouzfx_shake_handheld_light", "ouzfx_shake_micro_jitter"], ""),
    ("2.4", "Impact Shake / Screen Quake (Light, Medium, Heavy)", "partial", ["ouzfx_shake_heavy_impact", "ouzfx_shake_earthquake"],
     "Heavy tier existed; added the Light and Medium tiers."),
    ("2.5", "Whip Pan Push (4 directions)", "partial", ["ouzfx_fast_motion_slide_l", "ouzfx_comp_whip_left"],
     "Push-left (effect) and whip compositions existed; added push right / up / down."),
    ("2.6", "Heartbeat Pulse", "new", [], "Beat Pulse ×4 is uniform single pulses; heartbeat = slow double 'lub-dub' + darkening throb."),
    ("2.7", "Dutch Angle Tilt", "new", [], "8° and 15° tiers with automatic cover-zoom."),
    ("2.8", "Cinematic Letterbox Reveal", "partial", ["ouzfx_look_bars_slide_in", "ouzfx_look_cinematic_239"],
     "Bars slide-in existed; added the matching slide-out (In/Out split)."),
    ("3.1", "Background Dim & Blur", "new", [], "In and Out."),
    ("3.2", "Spotlight Vignette Focus (animated)", "partial", ["ouzfx_look_soft_vignette"],
     "Only a static vignette existed; added animated spotlight In / Out."),
    ("3.3", "Highlighter Wipe", "new", [], "For a Color clip: 45% marker band with left-to-right crop wipe."),
    ("3.4", "Split-Screen Presets (L/R, T/B, optional slide)", "new", [], "4 static halves + 4 slide-in versions."),
    ("3.5", "Censor / Redact Blur Box", "new", [], "Pixelate and heavy-blur versions (Alpha shapes mask)."),
    ("3.6", "Magnifying Zoom Callout (quadrants, back to 100%)", "partial",
     ["ouzfx_zoom_screen_tl", "ouzfx_zoom_screen_tr", "ouzfx_zoom_screen_bl", "ouzfx_zoom_screen_br", "ouzfx_zoom_screen_c", "ouzfx_zoom_screen_out"],
     "Zoom-in to each quadrant existed, but the return only worked from the centre; added a return for each corner."),
    ("4.1", "RGB Split / Chromatic Aberration Burst", "present", ["ouzfx_glitch_rgb_split_hit", "ouzfx_glitch_digital_burst"], ""),
    ("4.2", "Flash Cut / Exposure Spike (white & warm)", "present", ["ouzfx_flash_white", "ouzfx_flash_black", "ouzfx_style_film_burn"],
     "White flash and warm over-exposure flash already exist."),
    ("4.3", "Dramatic Desaturate ('Record Scratch' Freeze)", "new", [],
     "B&W Flashback is a static film look; this adds high-contrast B&W + slow push."),
    ("4.4", "VHS / Retro CRT Stack", "present", ["ouzfx_style_vhs"], ""),
    ("4.5", "Dreamy Bloom / Halation Glow", "present", ["ouzfx_style_light_leak"], "Glow + lifted, warm highlights (halation look)."),
    ("4.6", "Glitch Flicker", "new", [], "Opacity drops + horizontal displacement + light block distortion."),
    ("4.7", "Red Alert / Damage Pulse", "new", [], "Red Moment tints the whole frame; this pulses only the edges."),
    ("5.1", "Short-Form Word Pop (85→105→100%)", "new", [], "New speed tier: Text Pop is an 8-frame 30→100% pop."),
    ("5.2", "Rise & Fade Lower Third", "present", ["ouzfx_text_rise"], "Rises 6% of the frame height (≈ 65 px at 1080p) with fade."),
    ("5.3", "Typewriter Line Wipe", "new", [], "Fast (1 s) and Slow (2 s). Note: v1.0 slug text_typewriter_flash is the 'Highlight Flash', not a wipe."),
    ("5.4", "Glitch-In Title", "new", [], ""),
    ("5.5", "Drop Shadow Polish", "new", [], "Static two-layer shadow, Kdenlive 25.04+."),
    ("6.1", "Underwater / Muffled Room", "new", [], ""),
    ("6.2", "Walkie-Talkie / Telephone Voice", "new", [], "Two variants: clean telephone and crunchy radio."),
    ("6.3", "Dramatic Echo / Hall Reverb", "new", [], "Kdenlive hides FFmpeg aecho/acompressor, so built from included delay + limiter effects."),
    ("6.4", "Voiceover Quick Polish", "new", [], "High-pass + Dynamic Loudness leveler + limiter."),
]


def main():
    cat = json.load(open(os.path.join(ROOT, "pack", "catalog.json")))
    ids = {e["id"]: e for e in cat["effects"] + cat["compositions"]}
    new_by_bp = {}
    for e in cat["effects"] + cat["compositions"]:
        if e.get("bp"):
            new_by_bp.setdefault(e["bp"].split()[0], []).append(e)
    errors = []
    for iid, title, status, existing, note in ITEMS:
        for x in existing:
            if x not in ids:
                errors.append(f"{iid}: unknown existing preset {x}")
        if status in ("new", "partial") and not new_by_bp.get(iid):
            errors.append(f"{iid}: marked {status} but no new file")
        if status == "present" and new_by_bp.get(iid):
            errors.append(f"{iid}: marked present but has new files (duplicate?)")
    known = {i[0] for i in ITEMS}
    for k in new_by_bp:
        if k not in known:
            errors.append(f"new files reference unknown blueprint item {k}")
    if errors:
        print("\n".join(errors))
        return 1
    sfx = json.load(open(os.path.join(ROOT, "sfx", "sfx.json")))
    count = {s: sum(1 for i in ITEMS if i[2] == s) for s in ("present", "partial", "new")}
    lines = ["# Blueprint coverage (v1.1)", "",
             "Audit of every item in the *Kdenlive FX Pack: Expansion Blueprint* against the v1.0 pack, done before",
             "building anything, so nothing is implemented twice. **Present** = an existing preset already does essentially",
             "the same thing (nothing added). **Partial** = the effect existed but a variant was missing (direction, In/Out",
             "half, intensity tier) – only that variant was added. **New** = not in v1.0, implemented in v1.1.", "",
             f"Totals: **{len(ITEMS)} blueprint items** – {count['present']} already present, {count['partial']} partial "
             f"(missing variants added), {count['new']} new. New files: "
             f"{sum(len(v) for v in new_by_bp.values())} presets + {len(sfx)} sound effects.", "",
             "| Category | Items | Present | Partial | New | New preset files |", "|---|---|---|---|---|---|"]
    for c, name in CATS.items():
        its = [i for i in ITEMS if i[0].split(".")[0] == c]
        nf = sum(len(new_by_bp.get(i[0], [])) for i in its)
        lines.append(f"| {c}. {name} | {len(its)} | {sum(i[2] == 'present' for i in its)} | {sum(i[2] == 'partial' for i in its)} | "
                     f"{sum(i[2] == 'new' for i in its)} | {nf} |")
    lines.append(f"| + Sound effects (requested with the audio presets) | – | – | – | – | {len(sfx)} WAV files |")
    lines.append("")
    for c, name in CATS.items():
        lines += [f"## {c}. {name}", "", "| # | Blueprint item | Status | Existing v1.0 preset(s) | New in v1.1 | Notes |",
                  "|---|---|---|---|---|---|"]
        for iid, title, status, existing, note in ITEMS:
            if iid.split(".")[0] != c:
                continue
            ex = "<br>".join(f"`{x}`" for x in existing) or "–"
            nw = "<br>".join(f"`{e['id']}`" for e in new_by_bp.get(iid, [])) or "– (no duplicate built)"
            st = {"present": "✅ present", "partial": "➕ partial", "new": "🆕 new"}[status]
            lines.append(f"| {iid} | {title} | {st} | {ex} | {nw} | {note} |")
        lines.append("")
    lines += ["## Sound effects (new)", "", "| File | Length | Description |", "|---|---|---|"]
    for s in sfx:
        lines.append(f"| `{s['file']}` | {s['seconds']:.2f} s | {s['desc']} |")
    lines += ["", "## Design tips from the blueprint (section 7)", "",
              "* **Normalized geometry** – every preset is authored in fractions of the frame and generated per resolution "
              "(1080p, 4K, vertical 9:16) because Kdenlive's Transform widget only round-trips pixel rectangles; "
              "`install.sh --profile` picks the set. Mask/spot presets use resolution-independent 0–1 coordinates.",
              "* **Split In / Out** – new presets come as In/Out pairs where it matters (Dim & Blur, Spotlight, Bars, Zoom Callout returns).",
              "* **Speed / intensity tiers** – Impact Shake Light/Medium (+ v1.0 Heavy), Idle Float Gentle/Strong, Dutch Angle 8°/15°, "
              "Typewriter Fast/Slow.",
              "* **Naming** – new presets use `OuzFX AFX_Move_` / `AFX_Cam_` / `AFX_Style_` / `AFX_Util_` / `AFX_Audio_`. "
              "v1.0 names were kept unchanged so existing projects keep working.", ""]
    open(os.path.join(ROOT, "docs", "BLUEPRINT_COVERAGE.md"), "w").write("\n".join(lines))
    print("docs/BLUEPRINT_COVERAGE.md written:", count)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Changelog

## v1.3.0 – 2026-11-25

Highlights release: animated arrows, boxes, circles and labels for pointing at things on screen, styled with the
Ouz Labs brand kit (colours, fonts and rules extracted to [docs/BRAND.md](docs/BRAND.md)).

### Added – Highlights (27 assets, 318 alpha clips, 45 title templates)
* **Overlay clips:** VP9 WebM with alpha, 30 fps, square 1080 px (1080p and vertical) and 2160 px (4K). The point of interest is the clip centre.
  * Each asset has three parts: `_in` (entrance plus 2 s idle), `_loop` (2 s seamless idle) and `_out` (exit). `click_ripple` is one-shot.
  * **Arrows:** straight arrows pointing right/left/up/down (draw-on, tip nudge, slide-back exit), plus hand-drawn curved arrows pointing down-right and down-left.
  * **Boxes:** `box_draw_16x9` / `1x1` / `wide` (stroke draw-on, 16 px radius), `box_pop_16x9` (elastic scale-pop) and `focus_brackets` (corner brackets snap in).
  * **Circles:** `circle_draw`, `circle_pop`, `ellipse_draw`, and `pulse_ring` (sonar rings).
  * **Marks:** `scribble_circle` and `underline_swipe` (hand-drawn, with a boil loop), plus `check_draw` and `cross_draw`.
  * **Pointers:** `ping_dot` and `click_ripple`.
  * **Badges:** `step_badge_01…05` and the `new_sticker` (Acid Volt sticker with a 5 px Lab Chalk outline).
  * **Colours:** Signal Tangerine for everything; Acid Volt and Lab Chalk variants for the core arrows, boxes, circles and marks.
* **Label title templates** (`titles/<profile>/`, 1080p / 4K / vertical). The label is the template text (`%s`): type it in *Add Template Title*, and change it later in Clip Properties ▸ Apply.
  * Tags: Tangerine, Volt, Cobalt and Slate.
  * Box + label and box-tag-only versions (Tangerine, Volt and Chalk). The box tag lines up with `box_draw_16x9`.
  * Circle + label, step badge, NEW sticker (any word), corner "Lab Tag" series label and a callout note panel.
* **Brand fonts** (all SIL OFL): Bricolage Grotesque, Plus Jakarta Sans and JetBrains Mono, shipped in `fonts/` with their licences.
* **Generators:** `tools/brand.py`, `tools/make_highlights.py` (cairocffi + Pillow → ffmpeg libvpx-vp9 alpha; `--prores` writes ProRes 4444 fallbacks) and `tools/make_titles.py` (positions text from melt-rendered ink boxes).
* **Tests:** `tools/highlight_tests.py`:
  * melt alpha composite of every overlay: 318/318 passed.
  * In → Loop → Out seam check: 104/104 passed.
  * All 45 title templates render through melt.
  * Checked in Kdenlive 24.12.3: Library listing, alpha over V1, Add Template Title, and editing the text via Clip Properties.
* **Installers:**
  * `install.sh` copies highlights to `<data>/ouzfx/highlights` and the Library panel (*OuzFX Highlights*), and titles to `<data>/titles`. It also installs the fonts to `~/.local/share/fonts/ouzfx` (skip with `--no-fonts`). `--list` shows highlight and title counts, and `--uninstall` removes all of it.
  * `install.ps1` does the same on Windows, with a per-user font install.
* **Release assets:** KDE Store archives for *Kdenlive Title Templates* (`ouzfx-title-templates-<profile>`).

### Notes
* There are no new effect templates. Animate labels with the existing *Text Pop*, *Word Pop* and other In/Out templates.
* These were deliberately not duplicated: the highlighter wipe, censor boxes, spotlight and zoom callouts already exist. The new shapes are outline and pointer graphics, not masks or zooms.
* MLT's kdenlivetitle producer reads `font-weight` on the legacy Qt5 scale (50 = normal, 75 = bold, 81 = extra-bold), so the templates use those values.

## v1.2.0 – 2026-11-25

In/Out release: every entrance / intro animation in the pack (templates and compositions) was audited for a matching
exit; intros that already had one were left alone, the rest got an Out preset. Full table:
[docs/BLUEPRINT_COVERAGE.md › In/Out pairs](docs/BLUEPRINT_COVERAGE.md#inout-pairs-v12).

### Added – 37 Out effect templates + 12 compositions (1080p / 4K / vertical)
* **Whip out, 4 directions**
  * `AFX_Move_Whip_Slide_Out_Left/Right/Up/Down` – 12-frame expo ease-in exit with building motion blur (mirror of
    *Slide In from …*; the 6–8 frame fast tier already existed as *Motion-Blur Push Left* / `AFX_Cam_Whip_Pan_Push_*`).
  * `AFX_Cam_Whip_Push_Out_Left/Right/Up/Down` compositions – two-clip whip-pan push: the outgoing clip whips out while
    the incoming clip pushes in (Kdenlive's Push composition with expo ease-in-out).
* **AFX_Move** – Overshoot_Slide_Out ×4, Masked_Edge_Reveal_*_Out ×4, Bounce_Drop_Out, Elastic_Zoom_Out, Blur_Out,
  Card_3D_Swing_Out L/R, Hinge_Swing_Out top-left/top-right, PiP_Snap_*_Out ×4 (back to full screen),
  Screen_Pop_Out, Screen_Swing_Back_Out, Text_Word_Pop_Shorts_Out, Text_Rise_Fade_Out, Text_Typewriter_Wipe_Fast/Slow_Out,
  Text_Glitch_Out.
* **AFX_Util** – Split_Screen_Left/Right/Top/Bottom_Slide_Out, Highlighter_Wipe_Out.
* **AFX_Cam** – Dutch_Angle_Subtle_8deg_Out, Dutch_Angle_Strong_15deg_Out (back to level).
* **Out compositions** that always end at the composition end: Overshoot_Slide_Out_*_AnyLength ×4,
  Bounce_Drop_Out_AnyLength, Elastic_Zoom_Out_AnyLength, Text_Rise_Fade_Out_AnyLength, PiP_Corner_Pop_Out.
* `tools/out_tests.py` – melt renders every Out as the last piece of a clip: first frame identical to the last frame of
  its intro, last frame = background only (or back at rest). 49/49 passed.
* `install.sh --list` shows Out presets and the composition breakdown.

### Notes
* Kdenlive anchors effect-template keyframes to the clip start and drops end-relative (negative) keyframes when a
  template is applied, so Out templates are used like the whip pushes: razor N frames before the end and drop the
  template on that last piece (the layer is gone on its last frame). Out compositions use `-1=` and always end at the
  composition end.
* Corrected descriptions: Kdenlive/MLT "back" easing overshoots ≈ 37% of the travel (Overshoot_Slide_In, Pop Out),
  not the ~8% previously written. Motion unchanged.

## v1.1.0 – 2026-11-25

Expansion blueprint release. Every blueprint item was first audited against v1.0 and only missing items or missing
variants were built – no duplicates. Full mapping: [docs/BLUEPRINT_COVERAGE.md](docs/BLUEPRINT_COVERAGE.md)
(41 items: 12 already present, 8 partial → missing variants added, 21 new).

### Added
* **60 effect templates + 3 compositions** named `OuzFX AFX_<Category>_<Name>` (search `AFX_` in Kdenlive):
  * **AFX_Move (23)** – Overshoot Slide-In ×4, Masked Edge Reveal ×4, Idle Float Gentle/Strong, 3D Card Swing-In L/R,
    Hinge Swing-In top-left/top-right, Pendulum Swing Settle, PiP Snap ×4 corners, Text Word Pop (Shorts 85→105→100 %),
    Text Typewriter Wipe Fast/Slow, Text Glitch-In.
  * **AFX_Cam (13 + 3 compositions)** – Impact Shake Light/Medium (Heavy already existed), Whip Pan Push Right/Up/Down,
    Heartbeat Pulse, Dutch Angle 8°/15°, Zoom Callout Return ×4 corners, Cinematic Bars Slide-Out;
    compositions Ken Burns Pan Right→Left / Up / Down.
  * **AFX_Util (16)** – Background Dim & Blur In/Out, Spotlight Focus In/Out, Highlighter Wipe, Split Screen ×4 + Slide-In ×4,
    Censor Pixelate Box, Censor Blur Box, Drop Shadow Polish (Kdenlive 25.04+).
  * **AFX_Style (3)** – Record Scratch Freeze (high-contrast B&W + push), Glitch Flicker, Damage Pulse Red.
  * **AFX_Audio (5)** – Underwater Muffled, Telephone Voice, Walkie-Talkie Radio, Hall Echo Reverb, Voiceover Quick Polish.
    Built only from audio effects Kdenlive does not hide (its exclusion list removes FFmpeg aecho/acompressor).
* **16 original sound effects** (`sfx/`, 48 kHz 16-bit stereo WAV, peak −1 dBFS, click-free fades): 5 risers
  (incl. reverse cymbal, tension, downlifter), 4 pops, 5 whooshes (incl. whip swoosh, reverse suck), 2 impacts.
  Installed to `<data>/ouzfx/sfx/` and to `<data>/library/OuzFX SFX/` so they appear in Kdenlive's **Library** panel.
* `tools/presets_afx.py`, `tools/make_sfx.py`, `tools/audio_tests.py` (melt-rendered measurements of every audio preset and
  format checks of every SFX), `tools/blueprint.py` (coverage audit, cross-checked against the catalog).
* `install.sh --list` now shows a per-category breakdown (v1.0, AFX categories, compositions, lumas, overlays, SFX).

### Fixed
* **Static values of v1.0 presets were dropped when applied in Kdenlive.** Kdenlive re-reads animated parameters through
  `KeyframeModel::getAnimationStringWithOffset`, which returns an empty string for a plain value such as `0.5`. All animated
  parameters (incl. colours and rectangles) are now written as keyframe strings (`0=value`), so e.g. Cinematic Bars and
  vignettes keep their values. Verified by saving a project in
  Kdenlive 24.12.3 and reading the stored filters back.
* Test renders now use Kdenlive's centre rotation for the Transform effect (melt defaults to top-left), so rotation
  previews (Spin, Dutch Angle, Hinge…) match what Kdenlive shows.
* `tools/validate.py` also rejects effects listed in Kdenlive's `excluded_effects.txt` (Kdenlive hides any template that
  contains one).

## v1.0.0 – 2026-11-25

First release: 61 effect templates, 25 compositions, 16 luma wipes (HD + vertical), 2 overlay clips; 1080p / 4K / vertical
profiles; Linux (native + Flatpak) and Windows installers; KDE Store archives.

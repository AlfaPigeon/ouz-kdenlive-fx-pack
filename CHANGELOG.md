# Changelog

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

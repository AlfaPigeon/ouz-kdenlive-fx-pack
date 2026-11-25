#!/usr/bin/env python3
"""Generate README.md from pack/catalog.json + docs/test-results.json."""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO = "AlfaPigeon/kdenlive-fx-pack"
cat = json.load(open(os.path.join(ROOT, "pack", "catalog.json")))
res = {r["id"]: r for r in json.load(open(os.path.join(ROOT, "docs", "test-results.json")))}
VERSION = open(os.path.join(ROOT, "VERSION")).read().strip()

ORDER = ["Fast-Paced", "Camera Shake", "Dynamic Zoom", "Screen Zoom", "Animations", "Perspective Screen",
         "Transitions", "Glitch & Stylize", "Text & Titles", "Overlays", "Luma Wipes",
         "AFX_Move", "AFX_Cam", "AFX_Util", "AFX_Style", "AFX_Audio"]
AFX_TITLES = {"AFX_Move": "AFX_Move · object & text movement (v1.1)", "AFX_Cam": "AFX_Cam · camera & framing (v1.1)",
              "AFX_Util": "AFX_Util · focus, callout & explainer utilities (v1.1)",
              "AFX_Style": "AFX_Style · stylistic accents (v1.1)", "AFX_Audio": "AFX_Audio · audio effect templates (v1.1)"}
SFX = json.load(open(os.path.join(ROOT, "sfx", "sfx.json")))
import sys
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_highlights as MH  # noqa: E402
HLRES = json.load(open(os.path.join(ROOT, "docs", "highlight-test-results.json")))
TITLES = json.load(open(os.path.join(ROOT, "titles", "index.json")))
N_HL = {sz: sum(1 for k in HLRES["overlays"] if k.startswith(sz + "/")) for sz in ("1080", "2160")}
N_HL_ASSETS = len(MH.ASSETS)


def dur(f):
    return "static" if f == 0 else f"{f} f"


def table(items, kind):
    rows = ["| Preview | Name (search in Kdenlive) | What it does | Length |", "|---|---|---|---|"]
    for it in items:
        r = res.get(it["id"], {})
        prev = f'<img src="docs/previews/{r["preview"]}" width="200">' if r.get("preview") else ""
        flag = " ⚡" if "fast" in it.get("tags", []) else ""
        length = dur(it["frames"]) if kind == "effect" else "stretches"
        if it.get("audio"):
            prev, length = "🔊 audio", "static"
        rows.append(f'| {prev} | **{it["display"]}**{flag}<br><sub>`{it["id"]}` · {"effect template" if kind == "effect" else "composition"}</sub> | {it["desc"]} | {length} |')
    return "\n".join(rows)


n_eff, n_comp, n_luma = len(cat["effects"]), len(cat["compositions"]), len(cat["lumas"])
n_audio = sum(1 for e in cat["effects"] if e.get("audio"))
n_afx = sum(1 for e in cat["effects"] + cat["compositions"] if e["id"].startswith("ouzfx_afx_") and not e.get("pair"))
outs_e = [e for e in cat["effects"] if e.get("pair")]
outs_c = [e for e in cat["compositions"] if e.get("pair")]
OUTRES = {r["id"]: r for r in json.load(open(os.path.join(ROOT, "docs", "out-test-results.json")))}
total = n_eff + n_comp + n_luma
passed = sum(1 for r in res.values() if r["ok"])

out = [f"""# OuzFX · Kdenlive Effects & Transitions Pack

**{total} free, Kdenlive-native presets for fast-paced YouTube / Shorts editing:** camera shake, punch-in & boom zooms,
screen-recording zooms, 3D perspective screen share, slide / pop / spin / whip animations, glitch & RGB-split hits,
flash frames, film burn, VHS, cinematic bars, text pops, explainer tools (spotlight, split screen, censor box, highlighter),
{n_audio} voice/audio presets, {len(SFX)} original sound effects (risers, pops, whooshes, impacts) and {n_luma} custom luma wipes.

> **New in v1.3 – Highlights:** {N_HL_ASSETS} animated highlight overlays in the Ouz Labs brand colours (arrows from 4
> directions + hand-drawn curved arrows, outline boxes, focus brackets, circles, pulse rings, scribble circles, underline
> swipes, check / cross marks, ping dots, click ripples, step badges, a NEW sticker). Each comes as In / Loop / Out
> alpha WebM clips ({N_HL["1080"]} at 1080 px + {N_HL["2160"]} at 4K). There are also {len(TITLES)} editable label title templates in the brand fonts.
> See [Highlights](#highlights--arrows-boxes-circles--labels-v13) and [docs/BRAND.md](docs/BRAND.md).
>
> **New in v1.2:** Out (exit) versions of every intro that lacked one – {len(outs_e)} effect templates and {len(outs_c)}
> compositions, incl. **whip-out in all 4 directions** (`AFX_Move_Whip_Slide_Out_*` + the two-clip `AFX_Cam_Whip_Push_Out_*`
> transitions). See [In/Out pairs](#inout-pairs-v12) and [docs/BLUEPRINT_COVERAGE.md](docs/BLUEPRINT_COVERAGE.md#inout-pairs-v12).
>
> **New in v1.1:** {n_afx} `OuzFX AFX_*` presets from the expansion blueprint (only the items that were not already in the
> pack – see [docs/BLUEPRINT_COVERAGE.md](docs/BLUEPRINT_COVERAGE.md)), {n_audio} audio templates, {len(SFX)} sound effects
> and a fix that makes static values of v1.0 presets load correctly in Kdenlive. See [CHANGELOG.md](CHANGELOG.md).

Made for the Ouz Labs YouTube channel. MIT licensed, works with stock Kdenlive (nothing to compile) and installs like any
Kdenlive add-on: plain XML + images dropped into Kdenlive's own data folders.

* **{n_eff} effect templates** – Kdenlive "effect groups", show up under **Effects ▸ Templates**
* **{n_comp} compositions** – show up in the **Compositions** panel, keyframes stretch to the composition length
* **{n_luma} luma wipes** (HD + vertical) – appear in every Wipe / Luma composition and same-track mix
  ({n_audio} of them are **audio** templates: telephone, walkie-talkie, underwater, hall echo, voice-over polish)
* **{len(SFX)} sound effects** (48 kHz WAV) – appear in Kdenlive's **Library** panel under *OuzFX SFX*
* **{N_HL_ASSETS} highlight animations** (arrows, boxes, circles, marks, badges – In/Loop/Out alpha WebM) in Kdenlive's
  **Library** panel under *OuzFX Highlights*, + **{len(TITLES)} label title templates** (Project ▸ Add Template Title)
* 2 royalty-free overlay clips (light leak, film burn) for Screen/Add blending
* Every visual preset is test-rendered with MLT `melt` ({passed}/{len(res)} passed) – the previews below are those renders – and the
  pack was loaded and applied inside a real Kdenlive (24.12.3) session.

Everything is prefixed **OuzFX** – type `OuzFX` in the Effects or Compositions search box to see the whole pack, or
`AFX_` for the v1.1 additions (`AFX_Move_`, `AFX_Cam_`, `AFX_Util_`, `AFX_Style_`, `AFX_Audio_`).

<img src="docs/screenshots/effects-panel.png" width="360"> <img src="docs/screenshots/compositions-panel.png" width="360">

## Install

### Linux (Arch, Debian/Ubuntu, Fedora…, native package, AppImage or Flatpak)

```bash
git clone https://github.com/{REPO}.git && cd kdenlive-fx-pack && ./install.sh
```

or without git:

```bash
curl -L https://github.com/{REPO}/archive/refs/heads/main.tar.gz | tar xz && kdenlive-fx-pack-main/install.sh
```

`install.sh` auto-detects native and Flatpak Kdenlive and installs into whichever exists:

| Kdenlive build | Data folder used |
|---|---|
| distro package / AppImage / self-built | `~/.local/share/kdenlive/` (`$XDG_DATA_HOME/kdenlive`) |
| Flatpak (`org.kde.kdenlive`) | `~/.var/app/org.kde.kdenlive/data/kdenlive/` |

Options: `--profile 1080p|4k|vertical` (match your project resolution, default 1080p), `--native`, `--flatpak`, `--both`,
`--list`, `--uninstall`, `--no-fonts`. **Restart Kdenlive** after installing. The installer also puts the three free brand
fonts (OFL) in `~/.local/share/fonts/ouzfx` so the label titles render correctly (`--no-fonts` skips that).

```bash
./install.sh --profile 4k        # 3840×2160 projects
./install.sh --profile vertical  # 1080×1920 Shorts / Reels / TikTok projects
./install.sh --uninstall         # remove everything (uses the install manifest)
```

### Windows

Download the release zip, extract it, then in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\\install.ps1            # or -Profile 4k / -Profile vertical
powershell -ExecutionPolicy Bypass -File .\\install.ps1 -Uninstall
```

Manual copy: `pack\\<profile>\\effect-templates\\*.xml` → `%AppData%\\kdenlive\\effect-templates\\`,
`pack\\<profile>\\transitions\\*.xml` → `%AppData%\\kdenlive\\transitions\\` (replace `@LUMADIR@` with your lumas path),
`pack\\lumas\\HD\\ouzfx` → `%LocalAppData%\\kdenlive\\lumas\\HD\\ouzfx`.

### Manual / any OS

| What | Copy from | Copy to (`<data>` = folder from the table above) |
|---|---|---|
| Effect templates | `pack/<profile>/effect-templates/*.xml` | `<data>/effect-templates/` |
| Compositions | `pack/<profile>/transitions/*.xml` (replace `@LUMADIR@` with `<data>/lumas`) | `<data>/transitions/` |
| Luma wipes | `pack/lumas/HD/ouzfx/`, `pack/lumas/VERTICAL/ouzfx/` | `<data>/lumas/HD/ouzfx/`, `<data>/lumas/VERTICAL/ouzfx/` |
| Highlight overlays | `highlights/1080/` (1080p & vertical) or `highlights/2160/` (4K) | `<data>/library/OuzFX Highlights/` (and/or anywhere) |
| Label title templates | `titles/<profile>/*.kdenlivetitle` | `<data>/titles/` |
| Brand fonts | `fonts/*.ttf` | `~/.local/share/fonts/` (Windows: double-click ▸ Install) |

### KDE Store / "Download New Effects"

Release assets include KDE-Store-ready archives (`ouzfx-effect-templates-*.tar.gz` for the *Kdenlive Effect Templates*
category and `ouzfx-luma-wipes-hd-*.tar.gz` for *Kdenlive FX* (lumas)). Once published there they can be installed from inside
Kdenlive via **Effects ▸ Download New Effects** / the Wipe method **Download** button. See [docs/KDE_STORE.md](docs/KDE_STORE.md).

## Requirements

* **Kdenlive 24.08 or newer** (easing keyframe types such as back/elastic/bounce). Kdenlive 25.04+ recommended.
* **Kdenlive 25.04+** for the *Perspective Screen* presets and `AFX_Util_Drop_Shadow_Polish` (they use the Drop Shadow
  effect added in 25.04; older Kdenlive silently hides those templates).
* Uses only effects that ship with Kdenlive: Transform (qtblend), Box Blur, Directional Blur, Gaussian Blur, Brightness,
  Crop/Rounded corners (qtcrop), Corners (frei0r), Drop Shadow, RGB Shift, Chroma Shift, Glitch0r, Scanlines, Grain,
  Dust, Colorize, Glow, Saturation, Greyscale, Vignette, Contrast, Pixelize, Alpha shapes (mask), and for audio: Low/High
  pass, Equalizer, Bitcrusher, Compensation Delay, Dynamic Loudness, Limiter. frei0r-based presets need the **frei0r-plugins** package, which
  Kdenlive depends on in Arch (`frei0r-plugins`), Debian/Ubuntu, Flatpak and the AppImage/Windows builds.

## How to use

* **Effect templates** (Effects ▸ Templates, or search `OuzFX`): drag onto a clip. Keyframes are anchored to the **start of
  the clip**, so razor (`Shift+R`) where the hit should happen and drop the preset on the right-hand piece. Each template
  lands as a small, editable effect stack (e.g. Transform + Box Blur) – tweak strength in the Effect Stack.
  Lengths are in frames (designed at 25/30 fps; at 50/60 fps everything is twice as snappy).
* **Compositions** (Compositions panel, search `OuzFX`): put the clip on V2 above the clip it should reveal, then drag the
  composition onto the overlap. Their keyframes use `0=` / `-1=` so they always span the whole composition – make it
  6–12 frames for whips and zoom-throughs, seconds for Ken Burns.
* **Audio templates** (`AFX_Audio_`): Effects ▸ Templates, drag onto an audio clip (or the audio part of an A/V clip).
* **Sound effects**: open the **Library** panel (View ▸ Library) ▸ *OuzFX SFX* ▸ risers / pops / whooshes / impacts and
  drag a file onto an audio track, or Project Bin ▸ **Add Clip** ▸ `<data>/ouzfx/sfx/`.
* **Luma wipes**: any Wipe composition or same-track mix (select two adjacent clips ▸ `U`) ▸ *Wipe Method* ▸ `ouzfx_*`.
* **Resolution**: Kdenlive's Transform widget only round-trips pixel rectangles (percentage rects are mis-read by the UI),
  so effect templates and compositions are generated per resolution – install the profile matching your project
  (`--profile 1080p|4k|vertical`). Durations/easing are identical across profiles.

## Fast-paced editing kit ⚡

Research summary (sources below) – what makes MrBeast / Ali Abdaal / tech-YouTube / TikTok edits feel fast, and the matching preset:

| Technique | Why it works | OuzFX preset |
|---|---|---|
| Zoom punch on the beat (100→115-130 %, ease-out) | hides jump cuts, adds rhythm | `Zoom · Punch-In 115%`, `Zoom · Punch In-Out (Beat)`, `Fast · Beat Pulse ×4` |
| "Zoom cut" wide→close (MrBeast) | instant reframing without new footage | `Fast · Zoom Cut (Hard 130%)` |
| Boom zoom / smash cut | emphasis on reveals and punchlines | `Zoom · Boom Zoom`, `Fast · Smash Cut In`, `Fast · Rush Zoom` |
| Shake on impact (a few frames, peak on the beat) | physical "hit" feeling | `Shake · Heavy Impact`, `Fast · Impact Hit`, `Text · Text Slam` |
| 1–2 frame white/black flash | masks a cut, resets the eye | `Stylize · Flash Frame (White)`, `Stylize · Dip Flash (Black)` |
| Whip pan / motion-blur slide (match direction) | seamless energetic scene change | `Trans · Whip Pan *`, `Anim · Whip-In`, `Fast · Motion-Blur Push Left` |
| RGB split / glitch hit | digital energy on drops | `Stylize · RGB Split Hit`, `Stylize · Digital Glitch Burst`, `Wipe · Glitch Blocks` |
| Freeze frame + pop | call out a moment ("this guy…") | `Fast · Freeze-Frame Pop` + Kdenlive freeze |
| Stress colour (MrBeast red moment) | emotional emphasis | `Stylize · Red Moment` |
| Text pop / kinetic typography | on-screen keywords on the exact line | `Text · Text Pop`, `Text Rise`, `Text Slam`, `Highlight Flash` |
| Screen-recording zoom to cursor | readable tutorials / code | `Screen Zoom · Zoom to …`, `Zoom Back Out` |
| Film burn / light leak | warm transition between segments | `Stylize · Film Burn Flash`, `Wipe · Film Burn Wipe`, `overlays/` clips |
| Speed ramps | slow-mo on the hit, fast through the build-up | Kdenlive **Time Remap** (Clip ▸ Time Remap): add 2 keyframes, drag the speed handle; pair with `Rush Zoom` |
| J / L cuts | audio leads/trails the picture – smoother talking-head cuts | split audio (`Ungroup` or `Alt`-drag), trim the audio clip past the video cut – no effect needed |

Rules of thumb from the sources: land every move on the beat, keep hits to a few frames, use one or two transition styles
per video, default to the hard cut, and remember retention comes from new information, not effects alone.

"""]

HL_GROUPS = [("arrows", "Arrows"), ("boxes", "Boxes & brackets"), ("circles", "Circles & rings"),
             ("marks", "Marks"), ("pointers", "Pointers"), ("badges", "Badges & stickers")]
hl = [f"""## Highlights · arrows, boxes, circles & labels (v1.3)

Animated highlights to point at things on screen, styled with the Ouz Labs brand kit ([docs/BRAND.md](docs/BRAND.md)):
**Signal Tangerine `#FF5A26`** by default, plus **Acid Volt `#C8FF2E`** and **Lab Chalk `#F4F4F0`** variants of the core shapes.
The style follows the kit: 12 px strokes, 16 px rounded frames, sticker badges with a 5 px Lab Chalk outline, and "elastic pops
meet mechanical clicks" timing. A soft Carbon Slate shadow keeps them readable on bright footage.

* **Pre-rendered alpha clips** (VP9 WebM with alpha, 30 fps) are generated by [`tools/make_highlights.py`](tools/make_highlights.py).
  They are **square** (1080×1080, or 2160×2160 for 4K), so the same file works in 16:9 and 9:16 projects. The **arrow tip / shape
  centre is the centre of the clip**.
* Every shape has three parts that cut together seamlessly:
  * `_in` – the entrance plus a 2 s idle.
  * `_loop` – a 2 s seamless idle (nudge, breathe, hand-drawn boil). Repeat it to hold the shape longer.
  * `_out` – the exit.
  * `click_ripple` is a single one-shot clip.
* **Label templates** use the brand fonts: JetBrains Mono tags, Plus Jakarta Sans callout text and a Bricolage Grotesque sticker.
  You type the label text, so there's nothing to re-render.

**How to use**

1. **Library panel** (View ▸ Library) ▸ *OuzFX Highlights* ▸ group ▸ drag `…_in_tangerine.webm` onto a track **above** your footage.
   Kdenlive composites tracks automatically, and the transparent parts show the footage underneath.
2. Select the clip ▸ add **Transform** (Effects ▸ search "Transform") and move / scale it so the **centre** sits on the object.
   For arrows, the **tip** is the centre.
3. Need it longer? Put `…_loop_…` right after the `_in` clip and repeat it as often as you need, then end with `…_out_…`.
   To drop a shape early, cut the `_in` clip anywhere and put the `_out` clip after it.
4. **Labels:** Project ▸ **Add Template Title…** ▸ pick an `ouzfx_*` template ▸ type the text in the *Text* box ▸ OK.
   To change it later, open **Clip Properties** ▸ first tab, edit the text and click **Apply**. To animate it, drop *Text Pop*,
   *Word Pop* or any OuzFX In/Out template on it. Pair `ouzfx_box_tag_*` with `box_draw_16x9`: they line up 1:1 in 1080p/vertical
   projects.

<img src="docs/screenshots/highlights-library.png" width="300"> <img src="docs/screenshots/highlights-template-title.png" width="420">

Tags fit about 10 characters, the corner lab tag about 22, and the sticker 3–5. For longer text, double-click the title clip
to open Kdenlive's Title editor and drag the pill wider. The default label colours are Carbon Slate text on Tangerine and Volt,
and Lab Chalk text on Cobalt and Slate.

At **25 fps** the clips keep their real-time speed (Kdenlive drops frames to match), so timing and seams stay the same.
At 50/60 fps they play at 30 fps motion. If a Kdenlive build ever shows a black square instead of transparency, run
`python3 tools/make_highlights.py --prores` for ProRes 4444 `.mov` fallbacks in `highlights-prores/`.
"""]
for g, title in HL_GROUPS:
    assets = [A for A in MH.ASSETS if A.group == g]
    if not assets:
        continue
    hl.append(f"### {title}\n")
    if os.path.exists(os.path.join(ROOT, "docs", "previews", f"highlights_{g}.gif")):
        hl.append(f'<img src="docs/previews/highlights_{g}.gif" width="600">\n')
    hl.append("| Asset | Colours | Clips | Motion |\n|---|---|---|---|")
    for A in assets:
        clips = "one-shot, 20 f" if A.single else f"in {A.intro} f + 60 f idle · loop 60 f · out {A.out} f"
        hl.append(f"| `{A.name}` | {', '.join(A.colors)} | {clips} | {A.desc} |")
    hl.append("")
hl.append('### Label title templates (`titles/<profile>/`, installed to `<data>/titles/`)\n\n'
          '<img src="docs/previews/highlights_titles.jpg" width="720">\n\n| Template | What it is |\n|---|---|')
for k, v in TITLES.items():
    hl.append(f"| `{k}` | {v} |")
out.append("\n".join(hl) + "\n")

by_cat = {}
for it in cat["effects"]:
    by_cat.setdefault(it["category"], {"effect": [], "comp": []})["effect"].append(it)
for it in cat["compositions"]:
    by_cat.setdefault(it["category"], {"effect": [], "comp": []})["comp"].append(it)

out.append("## The presets\n\n⚡ = part of the fast-paced kit\n")
out.append("The v1.0 categories come first, the v1.1 `AFX_*` additions after the luma table.\n")
for c in ORDER:
    if c not in by_cat:
        continue
    if c.startswith("AFX_"):
        continue
    g = by_cat[c]
    out.append(f"### {c}\n")
    if g["effect"]:
        out.append(table(g["effect"], "effect") + "\n")
    if g["comp"]:
        out.append(table(g["comp"], "comp") + "\n")

out.append("### Luma wipe images\n\n| Preview | File | Shape |\n|---|---|---|")
for l in cat["lumas"]:
    r = res.get(l["name"], {})
    prev = f'<img src="docs/previews/{r["preview"]}" width="200">' if r.get("preview") else ""
    out.append(f"| {prev} | `{l['name']}.png` | {l['desc']} |")

for c in ORDER:
    if not c.startswith("AFX_") or c not in by_cat:
        continue
    g = {k: [i for i in v if not i.get("pair")] for k, v in by_cat[c].items()}
    out.append(f"\n### {AFX_TITLES[c]}\n")
    if c == "AFX_Audio":
        out.append("Built only from audio effects Kdenlive ships and does not hide (FFmpeg `aecho`/`acompressor` are on Kdenlive's "
                   "exclusion list, so the echo uses Compensation Delay taps and the leveler uses Dynamic Loudness + Limiter). "
                   "Each one is checked by `tools/audio_tests.py` (band energy / echo tail / peak level).\n")
    if g["effect"]:
        out.append(table(g["effect"], "effect") + "\n")
    if g["comp"]:
        out.append(table(g["comp"], "comp") + "\n")

out.append("\n### In/Out pairs (v1.2)\n\n"
           "Exit animations for every intro that had none (time-mirrored, ease-in). **Effect templates**: razor N frames "
           "before the end of the clip and drop the Out template on that last piece – the layer is gone on its last frame "
           "(Kdenlive anchors template keyframes to the clip start, so this is how an Out template lines up with the clip end). "
           "**Compositions** (`…_AnyLength`, `Whip_Push_Out_*`, `PiP_Corner_Pop_Out`) always end exactly at the end of the "
           "composition, whatever its length. Intros that already had an Out (Slide/Pop/Spin/Fade-Scale/Zoom-Through Out, "
           "Whip-In ↔ Motion-Blur Push, Bars, Dim & Blur, Spotlight, Callout returns) were not rebuilt – full table in "
           "[docs/BLUEPRINT_COVERAGE.md](docs/BLUEPRINT_COVERAGE.md#inout-pairs-v12).\n")
out.append("**Whip out, 4 directions:** `AFX_Move_Whip_Slide_Out_Left/Right/Up/Down` (12-frame templates with motion blur, mirror "
           "of *Slide In*), the fast 6–8 frame tier `Fast · Motion-Blur Push Left` + `AFX_Cam_Whip_Pan_Push_Right/Up/Down`, and "
           "`AFX_Cam_Whip_Push_Out_*` compositions – the outgoing clip whips out while the next one pushes in (overlap two "
           "clips on V1/V2 by 6–12 frames).\n")
out.append(table(outs_e, "effect") + "\n")
out.append(table(outs_c, "comp") + "\n")

out.append("\n### Sound effects (`sfx/`)\n\nOriginal, synthesized by [`tools/make_sfx.py`](tools/make_sfx.py) (MIT like the rest of the pack – free to use in any video). "
           "48 kHz 16-bit stereo, peak −1 dBFS, click-free fades. Installed to `<data>/ouzfx/sfx/` and `<data>/library/OuzFX SFX/` "
           "(Kdenlive **Library** panel).\n\n<img src=\"docs/screenshots/library-sfx.png\" width=\"360\">\n\n| Group | File | Length | Sound |\n|---|---|---|---|")
for x in SFX:
    out.append(f"| {x['group']} | `{os.path.basename(x['file'])}` | {x['seconds']:.2f} s | {x['desc']} |")

out.append(f"""

### Overlay clips (`overlays/`, installed to `<data>/ouzfx/overlays/`)

| File | Use |
|---|---|
| `ouzfx_light_leak.mp4` | 4 s warm light leak – put on a track above, Composition ▸ *Composite and transform* ▸ Compositing: **Screen** |
| `ouzfx_film_burn.mp4` | 1.6 s film-burn flash for segment transitions (Screen / Plus) |

## Building & testing

Everything is generated from [`tools/presets.py`](tools/presets.py) (v1.0) and [`tools/presets_afx.py`](tools/presets_afx.py) (v1.1 AFX) and [`tools/presets_out.py`](tools/presets_out.py) (v1.2 Outs):

```bash
python3 tools/build.py                    # writes pack/ (3 resolutions), lumas, catalog
python3 tools/validate.py /usr/share/kdenlive   # schema check vs. Kdenlive's own effect definitions
python3 tools/render_tests.py             # melt render of every preset + previews + docs/test-results.json
python3 tools/make_sfx.py && python3 tools/audio_tests.py   # sound effects + audio preset measurements
python3 tools/out_tests.py                # Out presets: continuity with their intro + end state
python3 tools/blueprint.py                # blueprint coverage + In/Out audit -> docs/BLUEPRINT_COVERAGE.md
python3 tools/make_highlights.py          # v1.3 highlight overlays (needs cairocffi, numpy, Pillow, ffmpeg+libvpx)
python3 tools/make_titles.py              # v1.3 label title templates (needs melt + the brand fonts)
python3 tools/highlight_tests.py && python3 tools/highlight_previews.py   # alpha/seam/title tests + README previews
python3 tools/gen_readme.py && tools/package.sh   # README + release archives in dist/
```

Validation done for v{VERSION}:

* `xmllint` + `validate.py` against Kdenlive **git master** effect definitions (all ids/params exist) and against Debian's
  Kdenlive 24.12 data (all OK except Drop Shadow, which is 25.04+ – documented above).
* v1.3 Highlights: `tools/highlight_tests.py` composites every 1080 overlay in melt over a test still. It checks that the
  corners stay untouched (real transparency), the shape is visible and every clip decodes as VP9 with alpha at 30 fps with the right size:
  **{HLRES["summary"]["overlays_ok"]}/{HLRES["summary"]["overlays"]} clips passed**. It also checks the seams: _in end → _loop start → _out start, and the loop wrap,
  must be no bigger than one frame step of the loop itself (**{HLRES["summary"]["seams_ok"]}/{HLRES["summary"]["seams"]} passed**). All
  {HLRES["summary"]["titles"]} title templates (3 profiles) render through melt's `kdenlivetitle` producer with the brand fonts. In Kdenlive 24.12.3,
  the clips appear in the Library panel and composite with alpha over V1. *Add Template Title* lists the templates, the
  typed text appears in the tag, and Clip Properties ▸ *Apply* changes it
  ([screenshot](docs/screenshots/highlights-template-text-edit.png)).
* v1.2 Out presets: `tools/out_tests.py` renders each one as the last piece of a clip – first frame identical to the
  last frame of its intro, last frame = background only (or back at rest): **{sum(r["ok"] for r in OUTRES.values())}/{len(OUTRES)} passed**
  (`docs/out-test-results.json`). The Whip Push composition and an Out template were applied in Kdenlive 24.12.3 and the
  saved project re-checked (expo easing and end keyframe intact).
* {n_audio} audio templates rendered through melt on a synthetic voice and measured (band attenuation, echo tail, peak);
  all {len(SFX)} sound effects checked for 48 kHz / peak ≤ −1 dBFS / click-free edges – see `docs/audio-test-results.json`.
* Every visual effect template, composition and luma rendered through MLT 7.30 `melt` at 1920×1080 (filters/transitions parse,
  no errors, and the picture measurably changes): **{passed}/{len(res)} passed** – see `docs/test-results.json`.
* Loaded in a real **Kdenlive 24.12.3** session (Xvfb): all templates appear under *Effects ▸ Templates*, all compositions
  in the *Compositions* panel; applied *Anim · Slide In from Left* to a trimmed clip and *Zoom · Ken Burns Push-In* as a
  composition and checked keyframes/monitor output ([screenshot](docs/screenshots/slide-in-mid-frame.png)).
  v1.1: the `AFX_*` templates (incl. all {n_audio} audio ones – [screenshot](docs/screenshots/audio-templates.png)) list in
  the same session, the SFX show in the Library panel, and applied templates were saved to a project and re-checked
  for intact keyframe values.
* Keyframe/offset behaviour checked against Kdenlive's source (`EffectStackModel::fromXml`,
  `KeyframeModel::getAnimationStringWithOffset`, `KeyframeModelList::checkConsistency`, `EffectsRepository::parseCustomAssetFile`):
  all animated parameters of an effect share the same keyframe positions, so Kdenlive never has to "repair" them.

## Credits & sources

* Kdenlive formats: [Kdenlive source](https://invent.kde.org/multimedia/kdenlive) (`data/effects/templates`, `data/knewstuff/*.knsrc`,
  `src/effects/effectsrepository.cpp`), [Kdenlive 22.04 effect templates announcement](https://kdenlive.org/news/releases/22.04.0/),
  [Kdenlive 24.08 easing modes](https://kdenlive.org/news/releases/24.08.0/), [Effects manual](https://docs.kdenlive.org/en/effects_and_filters.html),
  [KDE Store category request T14146](https://phabricator.kde.org/T14146), [MLT keyframe/animation docs](https://www.mltframework.org/docs/propertyanimation/).
* Fast-paced editing research:
  [Inkroy – Best transitions for edits (shake, zoom, flash, blur)](https://inkroy.com/learn/best-capcut-transitions-for-edits),
  [CapCut jugg edit tutorial – shakes, zooms, glitch cuts](https://capcutguide.com/capcut-jugg-edit/),
  [Velocity edits / speed ramps guide](https://capecutapks.com/how-to-create-velocity-edits-in-capcut-a-step-by-step-guide-for-beginners-2026/),
  [Olaf Motion – Reels transitions: zoom, whip, glitch, shake, light leaks](https://olafmotion.com/explore/reels-transitions-after-effects/),
  [Increditors – Hormozi, Ali Abdaal & MrBeast editing styles](https://increditors.com/an-ultimate-guide-to-alex-hormozi-ali-abdaal-and-mr-beast-video-editing-style-and-methods/),
  [Moonshot – Ali Abdaal editing style](https://makemoonshot.co/blog/ali-abdaal-editing-style),
  [SambaraVid – Ali Abdaal podcast editing (J/L cuts, whip pans)](https://sambaravid.com/tips-to-edit-like-ali-abdaal-video-podcast/),
  [VideoHero – Learn from a MrBeast video](https://www.videohero.com/blog/MrBeast-and-video-editing),
  [Vidpros – Mario Joos on retention editing](https://vidpros.com/retention-editing-what-you-can-learn-from-mario-joos/).
* All presets, lumas, overlays and preview media are original work generated by the scripts in `tools/`.

## License

[MIT](LICENSE) © 2026 Oğuz Kaan Özsoy · Ouz Labs
""")
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write("\n".join(out))
print("README written")

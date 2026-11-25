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
         "Transitions", "Glitch & Stylize", "Text & Titles", "Overlays", "Luma Wipes"]


def dur(f):
    return "static" if f == 0 else f"{f} f"


def table(items, kind):
    rows = ["| Preview | Name (search in Kdenlive) | What it does | Length |", "|---|---|---|---|"]
    for it in items:
        r = res.get(it["id"], {})
        prev = f'<img src="docs/previews/{r["preview"]}" width="200">' if r.get("preview") else ""
        flag = " ⚡" if "fast" in it.get("tags", []) else ""
        length = dur(it["frames"]) if kind == "effect" else "stretches"
        rows.append(f'| {prev} | **{it["display"]}**{flag}<br><sub>`{it["id"]}` · {"effect template" if kind == "effect" else "composition"}</sub> | {it["desc"]} | {length} |')
    return "\n".join(rows)


n_eff, n_comp, n_luma = len(cat["effects"]), len(cat["compositions"]), len(cat["lumas"])
total = n_eff + n_comp + n_luma
passed = sum(1 for r in res.values() if r["ok"])

out = [f"""# OuzFX · Kdenlive Effects & Transitions Pack

**{total} free, Kdenlive-native presets for fast-paced YouTube / Shorts editing:** camera shake, punch-in & boom zooms,
screen-recording zooms, 3D perspective screen share, slide / pop / spin / whip animations, glitch & RGB-split hits,
flash frames, film burn, VHS, cinematic bars, text pops and {n_luma} custom luma wipes.

Made for the Ouz Labs YouTube channel. MIT licensed, works with stock Kdenlive (nothing to compile) and installs like any
Kdenlive add-on: plain XML + images dropped into Kdenlive's own data folders.

* **{n_eff} effect templates** – Kdenlive "effect groups", show up under **Effects ▸ Templates**
* **{n_comp} compositions** – show up in the **Compositions** panel, keyframes stretch to the composition length
* **{n_luma} luma wipes** (HD + vertical) – appear in every Wipe / Luma composition and same-track mix
* 2 royalty-free overlay clips (light leak, film burn) for Screen/Add blending
* Every preset is test-rendered with MLT `melt` ({passed}/{len(res)} passed) – the previews below are those renders – and the
  pack was loaded and applied inside a real Kdenlive (24.12.3) session.

Everything is prefixed **OuzFX** – type `OuzFX` in the Effects or Compositions search box to see the whole pack.

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
`--list`, `--uninstall`. **Restart Kdenlive** after installing.

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

### KDE Store / "Download New Effects"

Release assets include KDE-Store-ready archives (`ouzfx-effect-templates-*.tar.gz` for the *Kdenlive Effect Templates*
category and `ouzfx-luma-wipes-hd-*.tar.gz` for *Kdenlive FX* (lumas)). Once published there they can be installed from inside
Kdenlive via **Effects ▸ Download New Effects** / the Wipe method **Download** button. See [docs/KDE_STORE.md](docs/KDE_STORE.md).

## Requirements

* **Kdenlive 24.08 or newer** (easing keyframe types such as back/elastic/bounce). Kdenlive 25.04+ recommended.
* **Kdenlive 25.04+** for the *Perspective Screen* presets (they use the Drop Shadow effect added in 25.04;
  older Kdenlive silently hides those six templates).
* Uses only effects that ship with Kdenlive: Transform (qtblend), Box Blur, Directional Blur, Gaussian Blur, Brightness,
  Crop/Rounded corners (qtcrop), Corners (frei0r), Drop Shadow, RGB Shift, Chroma Shift, Glitch0r, Scanlines, Grain,
  Dust, Colorize, Glow, Saturation, Greyscale, Vignette. frei0r-based presets need the **frei0r-plugins** package, which
  Kdenlive depends on in Arch (`frei0r-plugins`), Debian/Ubuntu, Flatpak and the AppImage/Windows builds.

## How to use

* **Effect templates** (Effects ▸ Templates, or search `OuzFX`): drag onto a clip. Keyframes are anchored to the **start of
  the clip**, so razor (`Shift+R`) where the hit should happen and drop the preset on the right-hand piece. Each template
  lands as a small, editable effect stack (e.g. Transform + Box Blur) – tweak strength in the Effect Stack.
  Lengths are in frames (designed at 25/30 fps; at 50/60 fps everything is twice as snappy).
* **Compositions** (Compositions panel, search `OuzFX`): put the clip on V2 above the clip it should reveal, then drag the
  composition onto the overlap. Their keyframes use `0=` / `-1=` so they always span the whole composition – make it
  6–12 frames for whips and zoom-throughs, seconds for Ken Burns.
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

by_cat = {}
for it in cat["effects"]:
    by_cat.setdefault(it["category"], {"effect": [], "comp": []})["effect"].append(it)
for it in cat["compositions"]:
    by_cat.setdefault(it["category"], {"effect": [], "comp": []})["comp"].append(it)

out.append("## The presets\n\n⚡ = part of the fast-paced kit\n")
for c in ORDER:
    if c not in by_cat:
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

out.append(f"""

### Overlay clips (`overlays/`, installed to `<data>/ouzfx/overlays/`)

| File | Use |
|---|---|
| `ouzfx_light_leak.mp4` | 4 s warm light leak – put on a track above, Composition ▸ *Composite and transform* ▸ Compositing: **Screen** |
| `ouzfx_film_burn.mp4` | 1.6 s film-burn flash for segment transitions (Screen / Plus) |

## Building & testing

Everything is generated from [`tools/presets.py`](tools/presets.py):

```bash
python3 tools/build.py                    # writes pack/ (3 resolutions), lumas, catalog
python3 tools/validate.py /usr/share/kdenlive   # schema check vs. Kdenlive's own effect definitions
python3 tools/render_tests.py             # melt render of every preset + previews + docs/test-results.json
python3 tools/gen_readme.py && tools/package.sh   # README + release archives in dist/
```

Validation done for v{VERSION}:

* `xmllint` + `validate.py` against Kdenlive **git master** effect definitions (all ids/params exist) and against Debian's
  Kdenlive 24.12 data (all OK except Drop Shadow, which is 25.04+ – documented above).
* Every effect template, composition and luma rendered through MLT 7.30 `melt` at 1920×1080 (filters/transitions parse,
  no errors, and the picture measurably changes): **{passed}/{len(res)} passed** – see `docs/test-results.json`.
* Loaded in a real **Kdenlive 24.12.3** session (Xvfb): all templates appear under *Effects ▸ Templates*, all compositions
  in the *Compositions* panel; applied *Anim · Slide In from Left* to a trimmed clip and *Zoom · Ken Burns Push-In* as a
  composition and checked keyframes/monitor output ([screenshot](docs/screenshots/slide-in-mid-frame.png)).
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

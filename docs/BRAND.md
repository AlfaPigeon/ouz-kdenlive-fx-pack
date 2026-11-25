# OuzFX brand kit — values used by the Highlights pack

Extracted from the brand kit PDF (*Tactile Neo-Lab Aesthetic*). The PDF is image-only, so
the colours below are the published hex codes, cross-checked by sampling the rendered swatches.
Machine-readable copy: [`tools/brand.py`](../tools/brand.py).

## Colours

| Name | Hex | RGB | Role |
|---|---|---|---|
| **Carbon Slate** | `#141619` | 20, 22, 25 | Dark backgrounds; text on light accents |
| **Lab Chalk** | `#F4F4F0` | 244, 244, 240 | Warm light canvas; sticker outlines |
| **Signal Tangerine** | `#FF5A26` | 255, 90, 38 | Primary focal accent (default highlight colour) |
| **Blueprint Cobalt** | `#2D5BFF` | 45, 91, 255 | Charts, UI, data |
| **Acid Volt** | `#C8FF2E` | 200, 255, 46 | Micro status highlight (LEDs, “NEW”, success) |

**60 / 30 / 10 rule:** 60% neutrals (Slate / Chalk), 30% supporting (footage, UI frames, Cobalt),
10% accents (≈7% Tangerine, ≈3% Volt). In practice, use **one** highlight per moment, Tangerine first.
Use Volt for small status things, and Chalk when Tangerine clashes with warm footage.

Text on accents: Carbon Slate text on Tangerine and Volt tags, and Lab Chalk text on Cobalt and Slate tags (for contrast).

## Typography (all free, SIL Open Font License, shipped in [`fonts/`](../fonts))

| Role | Font | Weight | Used for |
|---|---|---|---|
| Display | **Bricolage Grotesque** | ExtraBold 800 (Bold 700) | Hero words, thumbnails, the “NEW” sticker |
| Body | **Plus Jakarta Sans** | SemiBold 600 (Medium 500) | Captions, lists, lower thirds, callout text |
| Mono | **JetBrains Mono** | Bold 700 (Medium 500) | Lab tags, labels, step numbers, timestamps |

Display tracking is tight, −2% to −4% (the templates use −3%). The mono labels are uppercase with slightly open tracking.
All three fonts are free, so no substitutes are needed. If a font is missing, Kdenlive falls back silently.
Run `./install.sh --fonts` (or `--native`, which includes fonts) to install them to `~/.local/share/fonts/ouzfx`.

## Style rules applied

- **Crisp 16px rounded frames:** every box, tag and panel uses a 16 px corner radius (at 1080 scale).
- **Sticker cutouts with a crisp 5px Lab Chalk outline:** used on the step badges and the NEW sticker.
- **Lab Tag:** JetBrains Mono uppercase label. The corner series tag uses an Acid Volt LED dot, like the "OL" badge.
- **Tactile pacing: elastic pops meet mechanical clicks.** Shapes pop in with a small elastic overshoot (about 8%)
  or draw on with a fast ease-out (0.4–0.6 s). Idle motion is subtle (about 1.5% breathing or a short nudge).
  Exits are quick (0.25–0.33 s).
- **Max 3 focal points:** don't stack more than three highlights at once.
- Highlight stroke weight is 12 px at 1080 (24 px at 4K), with a soft Carbon Slate drop shadow so it stays readable on bright footage.
- Logo / tagline (not used in the overlays): geometric flask mark; *Curious. Crisp. Inventive.*

#!/usr/bin/env python3
"""Build the OuzFX pack: effect templates (per resolution), compositions, lumas.

usage: python3 tools/build.py            # writes ./pack
"""
import math
import os
import random
import shutil
import sys
from xml.sax.saxutils import escape, quoteattr

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import presets  # noqa: E402
import presets_afx  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PACK = os.path.join(ROOT, "pack")
PREFIX = "OuzFX"
PROFILES = {"1080p": (1920, 1080), "4k": (3840, 2160), "vertical": (1080, 1920)}

CAT_SHORT = {
    "Camera Shake": "Shake", "Dynamic Zoom": "Zoom", "Screen Zoom": "Screen Zoom",
    "Animations": "Anim", "Perspective Screen": "Screen 3D", "Glitch & Stylize": "Stylize",
    "Overlays": "Look", "Fast-Paced": "Fast", "Text & Titles": "Text", "Transitions": "Trans",
    "Luma Wipes": "Wipe",
}


def display_name(item):
    if item["category"].startswith("AFX_"):
        return f"{PREFIX} {item['category']}_{item['name']}"
    return f"{PREFIX} {CAT_SHORT[item['category']]} · {item['name']}"


def all_effects(p):
    return presets.effect_templates(p) + presets_afx.afx_templates(p)


def all_compositions():
    return presets.compositions() + presets_afx.afx_compositions()


def effect_id(item):
    return f"ouzfx_{item['slug']}"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# ---------------------------------------------------------------- effects
import json as _json
import re as _re

PARAMS = _json.load(open(os.path.join(os.path.dirname(__file__), "kdenlive_params.json")))


def key_frames(value):
    if "=" not in value:
        return None
    return [int(_re.match(r"-?\d+", part).group()) for part in value.split(";") if part]


def normalize(eid, props, where):
    """Write every animated parameter as an MLT keyframe string.

    * Kdenlive requires every animated parameter of one effect to have keyframes at the
      same positions (KeyframeModelList::checkConsistency, otherwise it shows 'Missing
      keyframe detected' and patches it) -> constants are expanded to the keyed frames.
    * When a template is applied, EffectStackModel::fromXml passes animated values through
      KeyframeModel::getAnimationStringWithOffset(), which returns an EMPTY string for a
      plain value such as "0.5" (MLT creates no animation for it). So even static values
      must be written as a single keyframe: "0=0.5"."""
    keyed = {k: key_frames(str(v)) for k, v in props.items() if key_frames(str(v))}
    union = sorted({f for ks in keyed.values() for f in ks}) or [0]
    for k, ks in keyed.items():
        if sorted(ks) != union:
            raise ValueError(f"{where}: {eid}.{k} keyframes {ks} != {union}")
    out = dict(props)
    for p in PARAMS.get(eid, []):
        if not p["animated"] or p["name"] in keyed:
            continue
        if p["name"].startswith("kdenlive:"):
            if union != [0]:
                raise ValueError(f"{where}: {eid} has fake param {p['name']} - do not keyframe this effect")
            continue
        val = props.get(p["name"], p["default"])
        if val is None or "%" in str(val):
            if p["name"] not in props and union == [0]:
                continue  # leave unset: Kdenlive fills in its own default
            raise ValueError(f"{where}: cannot expand {eid}.{p['name']}={val}")
        out[p["name"]] = ";".join(f"{f}={val}" for f in union)
    return out

def effect_template_xml(item):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             f'<effectgroup id={quoteattr(effect_id(item))} parentIn="0"'
             + (' type="customAudio"' if item.get("audio") else "") + '>',
             f'    <name>{escape(display_name(item))}</name>',
             f'    <description>{escape(item["desc"])}</description>']
    for eid, props in item["effects"]:
        props = normalize(eid, props, item["slug"])
        if not props:
            lines.append(f'    <effect id={quoteattr(eid)}/>')
            continue
        lines.append(f'    <effect id={quoteattr(eid)}>')
        for k, v in props.items():
            lines.append(f'        <property name={quoteattr(k)}>{escape(str(v))}</property>')
        lines.append('    </effect>')
    lines.append('</effectgroup>')
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- compositions
# Parameter blocks follow the schema of Kdenlive's data/transitions/*.xml.

QTBLEND_PARAMS = [
    ("animatedrect", "rect", 'default="0 0 %width %height 1"', "Rectangle"),
    ("keyframe", "rotation", 'max="360" min="-360" default="0" notintimeline="1" suffix="°"', "Rotation"),
    ("list", "compositing", 'default="0" paramlist="0;11;12;13;14;15;16;17;18;19;20;21;22;23;24;25;26;27;28;29;6;8"', "Compositing"),
    ("bool", "distort", 'default="0" min="0" max="1"', "Distort"),
    ("bool", "rotate_center", 'default="1" min="0" max="1"', "Rotate from center"),
]
QTBLEND_LIST = ('<paramlistdisplay>Alpha blend,Xor,Plus,Multiply,Screen,Overlay,Darken,Lighten,Color dodge,'
                'Color burn,Hard light,Soft light,Difference,Exclusion,Bitwise or,Bitwise and,Bitwise xor,'
                'Bitwise nor,Bitwise nand,Bitwise not xor,Destination in,Destination out</paramlistdisplay>')
AFFINE_PARAMS = [
    ("animatedrect", "rect", 'default="0 0 %width %height 1"', "Rectangle"),
    ("keyframe", "rotate_x", 'max="1800" min="-1800" default="0" factor="10" notintimeline="1"', "Rotate X"),
    ("keyframe", "rotate_y", 'max="1800" min="-1800" default="0" factor="10" notintimeline="1"', "Rotate Y"),
    ("keyframe", "rotate_z", 'max="1800" min="-1800" default="0" factor="10" notintimeline="1"', "Rotate Z"),
    ("bool", "distort", 'default="0" min="0" max="1"', "Distort"),
    ("fixed", "keyed", 'default="1" min="1" max="1"', None),
    ("bool", "repeat_off", 'default="1" min="0" max="1"', "Disable repeat"),
    ("bool", "mirror_off", 'default="1" min="0" max="1"', "Disable mirror"),
]
LUMA_PARAMS = [
    ("urllist", "resource", 'paramlist="%lumaPaths" filter="Luma files (*.png *.pgm);;Videos (*.mp4 *.mov *.avi *.mpeg)" '
                            'newstuff=":data/kdenlive_wipes.knsrc" optional="1"', "Wipe Method"),
    ("double", "softness", 'max="100" min="0" default="0" factor="100"', "Softness"),
    ("bool", "alpha_over", 'max="1" min="0" default="0"', "Use transparency"),
    ("bool", "fix_background_alpha", 'max="1" min="0" default="1"', "Make padding transparent"),
    ("bool", "invert", 'max="1" min="0" default="0"', "Invert"),
    ("bool", "reverse", 'max="1" min="0" default="0"', "Reverse"),
]


COMP_ANIMATED = {"qtblend": ["rect", "rotation"], "affine": ["rect", "rotate_x", "rotate_y", "rotate_z"], "luma": []}


def pct_rect_to_px(value, w, h):
    """'0q=-100% 0% 100% 100% 100%;-1=...' -> pixel rects. Kdenlive's rect widget
    shows/re-saves percentage rects incorrectly, so ship pixels per profile."""
    def conv(m):
        x, y, rw, rh, o = (float(v) for v in m.groups())
        return f"{x * w / 100:.0f} {y * h / 100:.0f} {rw * w / 100:.0f} {rh * h / 100:.0f} {o / 100:g}"
    return _re.sub(r"(-?[\d.]+)% (-?[\d.]+)% (-?[\d.]+)% (-?[\d.]+)% (-?[\d.]+)%", conv, value)


def composition_xml(item, w, h):
    params = {"qtblend": QTBLEND_PARAMS, "affine": AFFINE_PARAMS, "luma": LUMA_PARAMS}[item["tag"]]
    vals = dict(item["values"])
    if "rect" in vals:
        vals["rect"] = pct_rect_to_px(vals["rect"], w, h)
    keyed = [key_frames(vals[k]) for k in COMP_ANIMATED[item["tag"]] if k in vals and key_frames(vals[k])]
    if keyed:
        union = sorted(set(keyed[0]), key=lambda f: (f < 0, f))
        for k in COMP_ANIMATED[item["tag"]]:
            if k in vals:
                assert sorted(key_frames(vals[k]), key=lambda f: (f < 0, f)) == union, (item["slug"], k)
            else:
                vals[k] = ";".join(f"{f}=0" for f in union)
    item = dict(item, values=vals)
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<!DOCTYPE kpartgui>',
           f'<transition tag="{item["tag"]}" id={quoteattr("ouzfx_" + item["slug"])}>',
           f'    <name>{escape(display_name(item))}</name>',
           f'    <description>{escape(item["desc"])}</description>',
           '    <author>Oğuz Kaan Özsoy (OuzFX)</author>']
    for ptype, pname, attrs, label in params:
        val = item["values"].get(pname)
        vattr = f' value={quoteattr(val)}' if val is not None else ""
        if label is None:
            out.append(f'    <parameter type="{ptype}" name="{pname}" {attrs}{vattr}/>')
            continue
        out.append(f'    <parameter type="{ptype}" name="{pname}" {attrs}{vattr}>')
        out.append(f'        <name>{label}</name>')
        if pname == "compositing":
            out.append("        " + QTBLEND_LIST)
        out.append('    </parameter>')
    out.append('</transition>')
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- lumas

def luma_field(name, w, h):
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    u, v = x / (w - 1), y / (h - 1)
    cx, cy = u - 0.5, (v - 0.5) * h / w
    r = np.sqrt(cx ** 2 + cy ** 2)
    ang = np.arctan2(cx, -cy)  # 0 at 12 o'clock, clockwise
    rnd = np.random.default_rng(1234)
    if name == "ouzfx_radial":
        f = r / r.max()
    elif name == "ouzfx_radial_soft":
        f = (r / r.max()) ** 0.6
    elif name == "ouzfx_diagonal_tl":
        f = (u + v) / 2
    elif name == "ouzfx_diagonal_tr":
        f = ((1 - u) + v) / 2
    elif name == "ouzfx_clock":
        f = (ang % (2 * np.pi)) / (2 * np.pi)
    elif name == "ouzfx_blinds_h":
        f = (v * 8) % 1.0
    elif name == "ouzfx_blinds_v":
        f = (u * 12) % 1.0
    elif name == "ouzfx_diamond":
        f = (np.abs(u - 0.5) + np.abs(v - 0.5))
    elif name == "ouzfx_burn":
        acc = np.zeros((h, w))
        for octave, amp in [(4, 1.0), (8, 0.5), (16, 0.25), (32, 0.12)]:
            g = rnd.random((octave + 1, int(octave * w / h) + 2))
            img = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
            acc += amp * np.asarray(img, dtype=np.float64) / 255
        acc = (acc - acc.min()) / (acc.max() - acc.min())
        f = 0.55 * acc + 0.45 * (1 - (u * 0.6 + v * 0.4))  # burns from bottom-right corner area
        f = 1 - f
    elif name == "ouzfx_glitch_blocks":
        bh, bw = h // 12, w // 16
        g = rnd.random((12 + 1, 16 + 1))
        rows = rnd.random(12 + 1)
        f = np.zeros((h, w))
        for i in range(13):
            for j in range(17):
                ys, xs = i * bh, j * bw
                f[ys:ys + bh, xs:xs + bw] = 0.6 * g[i, j] + 0.4 * rows[i]
    elif name == "ouzfx_zigzag":
        teeth = 10
        f = u + 0.08 * np.abs(((v * teeth) % 1.0) - 0.5)
    elif name == "ouzfx_barn_doors":
        f = np.abs(u - 0.5) * 2
    elif name == "ouzfx_spiral":
        f = ((ang % (2 * np.pi)) / (2 * np.pi) * 0.25 + r / r.max() * 0.75)
    elif name == "ouzfx_heart":
        X = cx * 2.4
        Y = -cy * 2.4 * (w / h) * (h / w) * 1.0 + 0.15
        Y = -(v - 0.5) * 2.4 * h / w + 0.25
        val = (X ** 2 + Y ** 2 - 0.25) ** 3 - X ** 2 * Y ** 3
        f = np.cbrt(val)
    elif name == "ouzfx_pixel_dissolve":
        cell = 32
        g = rnd.random((h // cell + 2, w // cell + 2))
        f = g[(y // cell).astype(int), (x // cell).astype(int)]
    elif name == "ouzfx_swipe_up_soft":
        f = 1 - v + 0.05 * np.sin(u * np.pi * 2)
    else:
        raise KeyError(name)
    f = (f - f.min()) / (f.max() - f.min())
    return f


def save_luma(f, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    arr = np.round(f * 65535).astype(np.uint16)
    Image.fromarray(arr).save(path, optimize=True)


# ---------------------------------------------------------------- main

def main():
    if os.path.isdir(PACK):
        shutil.rmtree(PACK)
    catalog = {"effects": [], "compositions": [], "lumas": []}
    for prof, (w, h) in PROFILES.items():
        for item in all_effects(presets.P(w, h)):
            write(os.path.join(PACK, prof, "effect-templates", effect_id(item) + ".xml"), effect_template_xml(item))
            if prof == "1080p":
                catalog["effects"].append(dict(item, id=effect_id(item), display=display_name(item)))
    for item in all_compositions():
        for prof, (w, h) in PROFILES.items():
            write(os.path.join(PACK, prof, "transitions", "ouzfx_" + item["slug"] + ".xml"), composition_xml(item, w, h))
        catalog["compositions"].append(dict(item, id="ouzfx_" + item["slug"], display=display_name(item),
                                            values_1080p=dict(item["values"], rect=pct_rect_to_px(item["values"]["rect"], 1920, 1080))
                                            if "rect" in item["values"] else item["values"]))
    for name, desc in presets.LUMAS:
        for folder, (w, h) in {"HD": (1920, 1080), "VERTICAL": (1080, 1920)}.items():
            save_luma(luma_field(name, w, h), os.path.join(PACK, "lumas", folder, "ouzfx", name + ".png"))
        catalog["lumas"].append(dict(name=name, desc=desc))
    import json
    for c in catalog["effects"]:
        c["effects"] = [e[0] for e in c["effects"]]
    write(os.path.join(PACK, "catalog.json"), json.dumps(catalog, indent=1, ensure_ascii=False))
    print(f"effects: {len(catalog['effects'])} x {len(PROFILES)} profiles, "
          f"compositions: {len(catalog['compositions'])}, lumas: {len(catalog['lumas'])}")


if __name__ == "__main__":
    main()

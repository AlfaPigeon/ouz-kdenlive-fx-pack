#!/usr/bin/env python3
"""v1.2 Out-preset tests (melt): every Out preset is rendered as the LAST piece of a clip
and checked for
  * continuity – its first frame matches the last frame of the intro it mirrors,
  * end state  – on the last frame the layer is gone (only the background is left), back at
                 rest, or (for in-place moves) clearly changed,
  * compositions – first frame = full outgoing picture, last frame = only the clip that
                 remains (0= / -1= keyframes always end at the composition end).
Writes docs/out-test-results.json and /tmp/out-sheet.png (first/middle/last frame of each, for spot checks).
"""
import json
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import render_tests as RT  # noqa: E402

ROOT, MEDIA = RT.ROOT, RT.MEDIA
EQ = 3.0  # mean abs difference (0-255) below which two 480x270 frames count as identical


def fg_for(item):
    n = item["name"]
    if n.startswith("Text_") or item.get("category") == "Text & Titles":
        return MEDIA + "/title.png"
    if any(k in n for k in ("Overshoot", "Card_3D", "Hinge", "Bounce", "Swing_In", "Pop_In (")):
        return MEDIA + "/sticker.png"
    if n.startswith("Screen_") or item.get("category") == "Perspective Screen":
        return MEDIA + "/screen.png"
    if "Highlighter" in n:
        return MEDIA + "/yellow.png"
    return MEDIA + "/a.png"


def frames_of(xml, length):
    with tempfile.TemporaryDirectory() as td:
        rc, fr, bad = RT.render(xml, td, length)
        return rc, RT.frame_arrays(fr), bad


def group_xml(item, length, fg):
    return RT.mlt_for_group(os.path.join(ROOT, "pack", "1080p", "effect-templates", item["id"] + ".xml"), length, fg)


def plain(fg, length=1):
    bgp = RT.producer("bg", MEDIA + "/bg.png", length) + "</producer>"
    tracks = '<track producer="bg"/>'
    fgp = ""
    if fg:
        fgp = RT.producer("fg", fg, length) + "</producer>"
        tracks += '<track producer="fg"/>'
    return (f'<mlt>{RT.PROFILE}{bgp}{fgp}<tractor id="t" in="0" out="{length - 1}"><multitrack>{tracks}</multitrack>'
            '<transition><property name="mlt_service">qtblend</property><property name="a_track">0</property>'
            '<property name="b_track">1</property><property name="always_active">1</property></transition></tractor></mlt>')


def d(a, b):
    return float(np.abs(a - b).mean())


def main():
    cat = json.load(open(os.path.join(ROOT, "pack", "catalog.json")))
    eff = {e["id"]: e for e in cat["effects"]}
    results, sheet = [], []
    bg_only = frames_of(plain(None), 1)[1][0]
    for item in [e for e in cat["effects"] if e.get("pair")]:
        fg = fg_for(eff[item["pair"]]) if fg_for(item).endswith("a.png") else fg_for(item)
        n = item["frames"]
        rc, fr, bad = frames_of(group_xml(item, n, fg), n)
        intro = eff[item["pair"]]
        _, ifr, _ = frames_of(group_xml(intro, intro["frames"] + 1, fg), intro["frames"] + 1)
        cont = d(fr[0], ifr[-1])
        rest = frames_of(plain(fg), 1)[1][0]
        if item["end"] == "gone":
            endv, endok = d(fr[-1], bg_only), d(fr[-1], bg_only) < EQ
        elif item["end"] == "rest":
            endv, endok = d(fr[-1], rest), d(fr[-1], rest) < EQ
        else:
            endv, endok = d(fr[-1], fr[0]), d(fr[-1], fr[0]) > 1.0
        ok = rc == 0 and not bad and len(fr) == n and cont < EQ and endok
        results.append(dict(kind="effect", id=item["id"], pair=item["pair"], frames=n, continuity=round(cont, 2),
                            end=item["end"], end_metric=round(endv, 2), ok=bool(ok)))
        print(f"{'OK ' if ok else 'BAD'} {item['id']:48} n={n:2} continuity={cont:5.2f} end({item['end']})={endv:5.2f} {bad[:1]}")
        sheet.append((item["id"], [fr[0], fr[len(fr) // 2], fr[-1]]))
    a_img, b_img = MEDIA + "/a.png", MEDIA + "/b.png"
    top = frames_of(RT.mlt_for_transition("qtblend", {"rect": "0 0 1920 1080 1"}, 1), 1)[1][0]
    bottom = frames_of(RT.mlt_for_transition("qtblend", {"rect": "0 0 1920 1080 0"}, 1), 1)[1][0]
    for item in [c for c in cat["compositions"] if c.get("pair")]:
        L = 20
        rc, fr, bad = frames_of(RT.mlt_for_transition(item["tag"], dict(item["values_1080p"]), L), L)
        if item["end"] == "top":      # push: starts on the outgoing (lower) clip, ends on the incoming (upper)
            first, last = d(fr[0], bottom), d(fr[-1], top)
        else:                          # out composition: upper clip leaves, lower clip remains
            first, last = (d(fr[0], top) if "PiP" not in item["name"] else 0.0), d(fr[-1], bottom)
        ok = rc == 0 and not bad and len(fr) == L and first < EQ and last < EQ
        results.append(dict(kind="comp", id=item["id"], pair=item["pair"], first=round(first, 2), last=round(last, 2), ok=bool(ok)))
        print(f"{'OK ' if ok else 'BAD'} {item['id']:48} comp first={first:5.2f} last={last:5.2f} {bad[:1]}")
        sheet.append((item["id"], [fr[0], fr[L // 2], fr[-1]]))
    json.dump(results, open(os.path.join(ROOT, "docs", "out-test-results.json"), "w"), indent=1)
    # contact sheet: first / middle / last frame of every Out preset
    tw, th, lab = 200, 112, 230
    img = Image.new("RGB", (lab + 3 * tw, len(sheet) * th), (20, 20, 24))
    dr = ImageDraw.Draw(img)
    for i, (name, frs) in enumerate(sheet):
        dr.text((4, i * th + th // 2 - 6), name.replace("ouzfx_afx_", ""), fill=(230, 230, 230))
        for j, f in enumerate(frs):
            img.paste(Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).resize((tw - 4, th - 4)), (lab + j * tw, i * th + 2))
    img.save("/tmp/out-sheet.png")
    bad = [r for r in results if not r["ok"]]
    print(f"\n{len(results) - len(bad)}/{len(results)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

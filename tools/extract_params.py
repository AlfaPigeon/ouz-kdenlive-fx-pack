#!/usr/bin/env python3
"""Extract parameter metadata (name, type, default) for the Kdenlive effects
and compositions OuzFX uses, from a Kdenlive source checkout's data/ folder.
Writes tools/kdenlive_params.json (committed, so building needs no checkout).

usage: extract_params.py /path/to/kdenlive/data
"""
import glob
import json
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import presets  # noqa: E402
import presets_afx  # noqa: E402
import presets_out  # noqa: E402

ANIMATED = {"simplekeyframe", "keyframe", "animated", "animatedrect", "rect", "animatedfakerect",
            "animatedpoint", "animatedfakepoint", "color", "colorwheel", "roto-spline"}


def main(datadir):
    used = set()
    for it in presets.effect_templates(presets.P(1920, 1080)) + presets_afx.afx_templates(presets.P(1920, 1080)) + presets_out.out_templates(presets.P(1920, 1080)):
        used.update(e[0] for e in it["effects"])
    best = {}
    for path in glob.glob(os.path.join(datadir, "effects", "**", "*.xml"), recursive=True):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        for e in ([root] if root.tag.endswith("effect") else list(root)):
            if not str(e.tag).endswith("effect"):
                continue
            if not e.get("tag"):
                continue  # effect-template entries (properties only), not definitions
            eid = e.get("id") or e.get("tag")
            if eid not in used:
                continue
            ver = float(e.get("version", "0"))
            if eid in best and best[eid][0] > ver:
                continue
            params = []
            for p in e:
                if str(p.tag).endswith("parameter"):
                    params.append({"name": p.get("name"), "type": p.get("type"), "default": p.get("default"),
                                   "animated": p.get("type") in ANIMATED})
            best[eid] = (ver, params)
    out = {k: v[1] for k, v in sorted(best.items())}
    missing = used - set(out)
    if missing:
        print("MISSING", missing)
    json.dump(out, open(os.path.join(HERE, "kdenlive_params.json"), "w"), indent=1)
    print(f"{len(out)} effects written")


if __name__ == "__main__":
    main(sys.argv[1])

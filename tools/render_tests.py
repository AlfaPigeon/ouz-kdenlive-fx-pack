#!/usr/bin/env python3
"""Render every preset with melt (MLT) to prove the filters/transitions parse and
actually change the picture, and write GIF/PNG previews to docs/previews.

usage: render_tests.py [--no-previews] [slug ...]
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MEDIA = os.path.join(ROOT, "tools", "testmedia")
PREV = os.path.join(ROOT, "docs", "previews")
W, H, FPS = 1920, 1080, 25
PW, PH = 480, 270
PROFILE = (f'<profile description="HD 1080p 25 fps" width="{W}" height="{H}" progressive="1" '
           f'sample_aspect_num="1" sample_aspect_den="1" display_aspect_num="16" display_aspect_den="9" '
           f'frame_rate_num="{FPS}" frame_rate_den="1" colorspace="709"/>')


def producer(pid, img, length):
    return (f'<producer id="{pid}" in="0" out="{length - 1}"><property name="resource">{img}</property>'
            f'<property name="length">{length}</property><property name="mlt_service">qimage</property>'
            f'<property name="ttl">1</property>')


def props(d):
    return "".join(f'<property name="{escape(k)}">{escape(str(v))}</property>' for k, v in d.items())


def mlt_for_group(xmlpath, length, fg):
    root = ET.parse(xmlpath).getroot()
    filters = ""
    for e in root.findall("effect"):
        d = {p.get("name"): (p.text or "") for p in e.findall("property")}
        filters += f'<filter><property name="mlt_service">{e.get("id")}</property>{props(d)}</filter>'
    return (f'<mlt>{PROFILE}{producer("bg", MEDIA + "/bg.png", length)}</producer>'
            f'{producer("fg", fg, length)}{filters}</producer>'
            f'<tractor id="t" in="0" out="{length - 1}"><multitrack><track producer="bg"/><track producer="fg"/></multitrack>'
            f'<transition><property name="mlt_service">qtblend</property><property name="a_track">0</property>'
            f'<property name="b_track">1</property><property name="always_active">1</property></transition></tractor></mlt>')


def mlt_for_transition(tag, values, length, a=MEDIA + "/a.png", b=MEDIA + "/b.png"):
    return (f'<mlt>{PROFILE}{producer("b", b, length)}</producer>{producer("a", a, length)}</producer>'
            f'<tractor id="t" in="0" out="{length - 1}"><multitrack><track producer="b"/><track producer="a"/></multitrack>'
            f'<transition in="0" out="{length - 1}"><property name="mlt_service">{tag}</property><property name="a_track">0</property>'
            f'<property name="b_track">1</property>{props(values)}</transition></tractor></mlt>')


def render(mlt_xml, outdir, length):
    path = os.path.join(outdir, "t.mlt")
    with open(path, "w") as fh:
        fh.write(mlt_xml)
    cmd = ["melt", path, "-consumer", f"avformat:{outdir}/f%04d.png", "vcodec=png", "progressive=1", f"width={PW}", f"height={PH}",
           "sample_aspect_num=1", "sample_aspect_den=1", "display_aspect_num=16", "display_aspect_den=9",
           "rescale=bilinear", "real_time=0"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    frames = sorted(glob.glob(f"{outdir}/f*.png"))
    bad = [l for l in r.stderr.splitlines() if any(w in l.lower() for w in ("failed", "invalid", "error", "unknown")) and "csp: unknown" not in l]
    return r.returncode, frames, bad


def frame_arrays(frames):
    return [np.asarray(Image.open(f).convert("RGB"), dtype=np.int16) for f in frames]


def to_gif(frames, out, fps=12.5):
    pattern = os.path.join(os.path.dirname(frames[0]), "f%04d.png")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-start_number", "1", "-i", pattern,
                    "-vf", f"fps={fps},scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=80[p];[s1][p]paletteuse=dither=bayer:bayer_scale=4",
                    "-loop", "0", out], check=True)


def main(argv):
    previews = "--no-previews" not in argv
    only = [a for a in argv if not a.startswith("--")]
    cat = json.load(open(os.path.join(ROOT, "pack", "catalog.json")))
    os.makedirs(PREV, exist_ok=True)
    results = []
    # baseline for "did anything change" checks
    with tempfile.TemporaryDirectory() as td:
        base = {}
        for name, img in [("a", MEDIA + "/a.png"), ("screen", MEDIA + "/screen.png")]:
            xml = (f'<mlt>{PROFILE}{producer("bg", MEDIA + "/bg.png", 1)}</producer>{producer("fg", img, 1)}</producer>'
                   f'<tractor id="t" in="0" out="0"><multitrack><track producer="bg"/><track producer="fg"/></multitrack>'
                   f'<transition><property name="mlt_service">qtblend</property><property name="a_track">0</property>'
                   f'<property name="b_track">1</property><property name="always_active">1</property></transition></tractor></mlt>')
            _, fr, _ = render(xml, td, 1)
            base[name] = frame_arrays(fr)[0]
            for f in fr:
                os.remove(f)

    def check(kind, item, xml, length, basekey):
        with tempfile.TemporaryDirectory() as td:
            rc, frames, bad = render(xml, td, length)
            ok = rc == 0 and len(frames) == length and not bad
            arrs = frame_arrays(frames) if frames else []
            ref = base.get(basekey)
            if ref is not None:
                diff = max(float(np.abs(a - ref).mean()) for a in arrs) if arrs else 0
            else:
                diff = max(float(np.abs(a - arrs[0]).mean()) for a in arrs) if arrs else 0
            changed = diff > 1.0
            prev = None
            if previews and frames:
                if length == 1:
                    prev = f"{item['id']}.png"
                    Image.open(frames[0]).resize((320, 180)).save(os.path.join(PREV, prev), optimize=True)
                else:
                    prev = f"{item['id']}.gif"
                    to_gif(frames, os.path.join(PREV, prev))
            results.append(dict(kind=kind, id=item["id"], frames=len(frames), expected=length, rc=rc,
                                warnings=bad[:3], mean_abs_diff=round(diff, 2), ok=bool(ok and changed), preview=prev))
            print(f"{'OK ' if ok and changed else 'BAD'} {kind:5} {item['id']:38} frames={len(frames)}/{length} diff={diff:.1f} {bad[:1]}")

    for item in cat["effects"]:
        if only and item["slug"] not in only and item["id"] not in only:
            continue
        frames = item["frames"]
        length = 1 if frames == 0 else min(max(frames + 12, 30), 90)
        fg = MEDIA + ("/screen.png" if item["category"] == "Perspective Screen" else "/a.png")
        xmlpath = os.path.join(ROOT, "pack", "1080p", "effect-templates", item["id"] + ".xml")
        check("effect", item, mlt_for_group(xmlpath, length, fg), length,
              "screen" if "screen" in fg else "a")
    for item in cat["compositions"]:
        if only and item["slug"] not in only and item["id"] not in only:
            continue
        vals = dict(item["values_1080p"])
        if "resource" in vals:
            vals["resource"] = vals["resource"].replace("@LUMADIR@", os.path.join(ROOT, "pack", "lumas"))
        check("comp", item, mlt_for_transition(item["tag"], vals, 30), 30, None)
    for l in cat["lumas"]:
        if only and l["name"] not in only:
            continue
        item = {"id": l["name"]}
        vals = {"resource": os.path.join(ROOT, "pack", "lumas", "HD", "ouzfx", l["name"] + ".png"), "softness": "0.1"}
        check("luma", item, mlt_for_transition("luma", vals, 30), 30, None)
    if not only:
        json.dump(results, open(os.path.join(ROOT, "docs", "test-results.json"), "w"), indent=1)
    bad = [r for r in results if not r["ok"]]
    print(f"\n{len(results) - len(bad)}/{len(results)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

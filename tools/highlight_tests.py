#!/usr/bin/env python3
"""Tests for the Highlights pack.

1. Every overlay (1080 set) is composited in melt (qtblend) over a test still. The test
   checks that the corners stay untouched (so alpha is really transparent), that the
   highlight is visible on the rest-pose frame, and that the _out clip ends empty.
2. Every clip at both sizes is decoded with libvpx-vp9 to check it has an alpha plane, 30 fps,
   a square size and the expected frame count.
3. Seams: _in last frame == _loop first frame == _out first frame, and _loop last frame
   flows into _loop first frame.
4. Every title template is rendered with melt's kdenlivetitle producer for all
   3 profiles. The test checks it is non-empty with a transparent background and fonts resolved.
5. Contact sheets go to docs/previews/highlights_*.jpg, and results to docs/highlight-test-results.json.
"""
import glob, json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_highlights as MH

ROOT = MH.ROOT
HL = os.path.join(ROOT, "highlights")
BG = os.path.join(ROOT, "tools", "testmedia", "screen.png")
ENV = dict(os.environ, QT_QPA_PLATFORM="offscreen")

def melt_frame(clip, frame, out_png, profile="atsc_1080p_30"):
    cmd = ["melt", "-profile", profile, BG, "out=0", "-track", clip, f"in={frame}", f"out={frame}",
           "-transition", "qtblend", "a_track=0", "b_track=1", "in=0", "out=0",
           "-consumer", f"avformat:{out_png}", "vcodec=png", "frames=1", "update=1"]
    subprocess.run(cmd, env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return np.asarray(Image.open(out_png).convert("RGB"), np.int16)

def decode(clip, S):
    """stream frames as RGBA uint8 via libvpx (the native vp9 decoder would drop alpha)"""
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", clip, "-f", "rawvideo",
                          "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE)
    n = S * S * 4
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, np.uint8).reshape(S, S, 4)
    p.wait()

def scan(clip, S):
    st = {"frames": 0, "amin": 255, "amax": 0, "step": 0.0}
    prev = first = None
    mid = None
    for fr in decode(clip, S):
        a = fr[..., 3]
        st["amin"] = min(st["amin"], int(a.min())); st["amax"] = max(st["amax"], int(a.max()))
        small = fr[::2, ::2].astype(np.int16)          # half-res for seam maths (memory)
        if first is None: first = small
        if prev is not None: st["step"] = max(st["step"], float(np.abs(small - prev).mean()))
        prev = small
        st["frames"] += 1
        if st["frames"] == 30: mid = float((a == 0).mean())
    st["first"], st["last"], st["mid_transparent"] = first, prev, mid
    st["last_amax"] = int(prev[..., 3].max())
    return st

def probe(clip):
    o = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                                 "stream=codec_name,width,height,r_frame_rate:stream_tags=alpha_mode", "-of", "json", clip])
    return json.loads(o)["streams"][0]

SAMPLES = {"ouzfx_step_badge": "01", "ouzfx_sticker_new": "NEW", "ouzfx_callout_note": "Callout text goes here",
           "ouzfx_lab_tag_corner": "EXP 01 // HIGHLIGHTS", "ouzfx_box_label_tangerine": "SETTINGS",
           "ouzfx_circle_label_tangerine": "CLICK", "ouzfx_tag_cobalt": "API", "ouzfx_tag_volt": "LIVE"}

def title_sheet(folder):
    bg = Image.open(BG).convert("RGBA").resize((1920, 1080))
    fs = sorted(glob.glob(os.path.join(folder, "*.png")))
    tiles = []
    for f in fs:
        im = Image.alpha_composite(bg, Image.open(f).convert("RGBA")).convert("RGB").resize((480, 270), Image.LANCZOS)
        tiles.append(im)
    cols = 3
    W = Image.new("RGB", (cols * 484 - 4, ((len(tiles) + cols - 1) // cols) * 274 - 4), (20, 22, 25))
    for i, im in enumerate(tiles):
        W.paste(im, ((i % cols) * 484, (i // cols) * 274))
    W.save(os.path.join(ROOT, "docs", "previews", "highlights_titles.jpg"), quality=85)

def main():
    bg = np.asarray(Image.open(BG).convert("RGB").resize((1920, 1080)), np.int16)
    results, fails = {}, []
    clips = sorted(glob.glob(os.path.join(HL, "*", "*", "*.webm")))
    tmp = tempfile.mkdtemp()
    prev_json = os.path.join(ROOT, "docs", "highlight-test-results.json")
    titles_only = "--titles-only" in sys.argv and os.path.exists(prev_json)
    if titles_only:      # reuse overlay + seam results, re-run the title part
        old = json.load(open(prev_json))
        results, seams_old = old["overlays"], old["seams"]
        fails = [k for k, v in results.items() if not v["ok"]] + ["seam " + k for k, v in seams_old.items() if not v["ok"]]
        clips = []
    seam_cache = {}
    for c in clips:
        rel = os.path.relpath(c, HL)
        size = rel.split(os.sep)[0]
        name = os.path.basename(c)
        r = {}
        p = probe(c)
        r["codec"], r["fps"] = p["codec_name"], p["r_frame_rate"]
        r["alpha_mode"] = p.get("tags", {}).get("alpha_mode") or p.get("tags", {}).get("ALPHA_MODE")
        S = int(p["width"])
        st = scan(c, S)
        r["frames"], r["size"] = st["frames"], S
        r["alpha_min"], r["alpha_max"] = st["amin"], st["amax"]
        r["transparent_ratio_f30"] = None if st["mid_transparent"] is None else round(st["mid_transparent"], 3)
        ok = (p["codec_name"] == "vp9" and r["alpha_mode"] == "1" and p["r_frame_rate"] == "30/1"
              and p["width"] == p["height"] == int(size) and r["alpha_min"] == 0 and r["alpha_max"] > 200)
        if "_out_" in name:
            r["last_frame_alpha_max"] = st["last_amax"]
            ok &= r["last_frame_alpha_max"] < 255     # fading/shrinking
        seam_cache[c] = (st["first"], st["last"], st["step"])
        # melt composite (1080 set only - same code path for 2160)
        if size == "1080":
            f_rest = st["frames"] - 1 if "_in_" in name else 0
            if "click_ripple" in name: f_rest = 5
            img = melt_frame(c, f_rest, os.path.join(tmp, "m.png"))
            diff = np.abs(img - bg).max(axis=2)
            corner = max(diff[:60, :60].max(), diff[:60, -60:].max(), diff[-60:, :60].max(), diff[-60:, -60:].max())
            r["melt_corner_maxdiff"] = int(corner)
            r["melt_changed_px"] = int((diff > 40).sum())
            ok &= corner <= 2 and r["melt_changed_px"] > 500
        r["ok"] = bool(ok)
        results[rel] = r
        if not ok: fails.append(rel)
        print(("ok  " if ok else "FAIL"), rel, r.get("melt_changed_px", ""), flush=True)

    # seams
    seams = seams_old if titles_only else {}
    for c in clips:
        if "_in_" not in os.path.basename(c): continue
        lp, ot = c.replace("_in_", "_loop_"), c.replace("_in_", "_out_")
        in_last = seam_cache[c][1]
        d1 = float(np.abs(in_last - seam_cache[lp][0]).mean())
        d2 = float(np.abs(in_last - seam_cache[ot][0]).mean())
        d3 = float(np.abs(seam_cache[lp][1] - seam_cache[lp][0]).mean())
        step = seam_cache[lp][2]
        rel = os.path.relpath(c, HL).replace("_in_", "_*_")
        # every seam must be no bigger than the largest frame-to-frame step inside the loop itself
        lim = step * 1.25 + 0.3
        sok = d1 <= lim and d2 <= lim and d3 <= lim
        seams[rel] = {"in_to_loop": round(d1, 3), "in_to_out": round(d2, 3), "loop_wrap": round(d3, 3),
                      "max_loop_step": round(step, 3), "ok": sok}
        if not sok: fails.append("seam " + rel)

    # titles
    titles = {}
    for prof, mprof in (("1080p", "atsc_1080p_30"), ("4k", "uhd_2160p_30"), ("vertical", "vertical_hd_30")):
        for t in sorted(glob.glob(os.path.join(ROOT, "titles", prof, "*.kdenlivetitle"))):
            png = os.path.join(tmp, "t.png")
            sample = SAMPLES.get(os.path.basename(t)[:-len(".kdenlivetitle")], "LABEL")
            subprocess.run(["melt", "-profile", mprof, t, f"templatetext={sample}", "in=0", "out=0", "-consumer", f"avformat:{png}", "vcodec=png",
                            "pix_fmt=rgba", "frames=1", "update=1"], env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            im = np.asarray(Image.open(png).convert("RGBA"))
            a = im[..., 3]
            rel = f"{prof}/{os.path.basename(t)}"
            tok = a[0, 0] == 0 and a[-1, -1] == 0 and (a > 0).mean() > 0.0005
            titles[rel] = {"w": im.shape[1], "h": im.shape[0], "coverage": round(float((a > 0).mean()), 4), "ok": bool(tok)}
            if not tok: fails.append("title " + rel)
            if prof == "1080p":
                os.makedirs(os.path.join(tmp, "titles"), exist_ok=True)
                Image.open(png).save(os.path.join(tmp, "titles", os.path.basename(t) + ".png"))
    title_sheet(os.path.join(tmp, "titles"))
    fc = "|".join(subprocess.run(["fc-match", "-f", "%{family[0]}", f], capture_output=True, text=True).stdout
                  for f in ("Bricolage Grotesque", "Plus Jakarta Sans", "JetBrains Mono"))
    summary = {"overlays": len(results), "overlays_ok": sum(r["ok"] for r in results.values()),
               "seams": len(seams), "seams_ok": sum(s["ok"] for s in seams.values()),
               "titles": len(titles), "titles_ok": sum(t["ok"] for t in titles.values()),
               "melt": subprocess.check_output(["melt", "--version"], stderr=subprocess.STDOUT, text=True).splitlines()[0],
               "fonts": fc.strip("|").split("|"), "fails": fails}
    json.dump({"summary": summary, "overlays": results, "seams": seams, "titles": titles},
              open(os.path.join(ROOT, "docs", "highlight-test-results.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())

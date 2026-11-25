#!/usr/bin/env python3
"""Check the AFX_Audio effect templates with melt and the generated SFX files.

* every audio template is applied (exactly as written in pack/1080p/effect-templates)
  to a synthetic voice-like test signal and rendered by melt to WAV;
* the result must render without errors and show the expected acoustic change
  (band energy / tail / peak);
* every sfx/*.wav must be 48 kHz, peak about -1 dBFS, start/end at silence.
Writes docs/audio-test-results.json.
"""
import glob
import json
import os
import subprocess
import sys
import tempfile
import wave
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SR = 48000


def read_wav(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, w.getnchannels()) / 32768
        return w.getframerate(), a


def make_voice(path):
    t = np.arange(int(3.5 * SR)) / SR
    sig = np.zeros_like(t)
    on = t < 2.0
    f0 = 120 + 20 * np.sin(2 * np.pi * 1.5 * t)
    ph = 2 * np.pi * np.cumsum(f0) / SR
    for k in range(1, 60):
        if 120 * k > 9000:
            break
        sig += np.sin(k * ph) / k
    rng = np.random.default_rng(3)
    sig += 0.3 * rng.standard_normal(len(t))           # breath / fricatives (broadband)
    sig += 0.6 * np.sin(2 * np.pi * 35 * t)            # 35 Hz rumble for the high-pass checks
    sig *= on * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t) ** 2)
    sig[: int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))
    sig = sig / np.abs(sig).max() * 0.7
    pcm = (np.stack([sig, sig], 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def band_db(a, lo, hi, start=0.0, end=2.0):
    x = a[int(start * SR):int(end * SR), 0]
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return 10 * np.log10(spec[(f >= lo) & (f < hi)].sum() + 1e-12)


def rms_db(a, start, end):
    x = a[int(start * SR):int(end * SR)]
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)


def render(template, src, out):
    root = ET.parse(template).getroot()
    filters = ""
    for e in root.findall("effect"):
        d = {p.get("name"): (p.text or "") for p in e.findall("property")}
        filters += (f'<filter><property name="mlt_service">{e.get("id")}</property>'
                    + "".join(f'<property name="{escape(k)}">{escape(v)}</property>' for k, v in d.items()) + "</filter>")
    xml = (f'<mlt><profile width="640" height="360" frame_rate_num="25" frame_rate_den="1" progressive="1"/>'
           f'<producer id="p" in="0" out="{int(3.5 * 25) - 1}"><property name="resource">{src}</property>'
           f'<property name="mlt_service">avformat</property>{filters}</producer>'
           f'<playlist id="pl"><entry producer="p" in="0" out="{int(3.5 * 25) - 1}"/></playlist></mlt>')
    mlt = out + ".mlt"
    open(mlt, "w").write(xml)
    r = subprocess.run(["melt", mlt, "-consumer", f"avformat:{out}", "vn=1", "acodec=pcm_s16le", f"frequency={SR}",
                        "channels=2", "real_time=0"], capture_output=True, text=True, timeout=300)
    bad = [l for l in r.stderr.splitlines() if any(w in l.lower() for w in ("failed", "invalid", "error", "unknown"))]
    return r.returncode, bad


EXPECT = {
    # name: (description, check(dry, wet) -> (ok, detail))
    "underwater_muffled": ("high band (2-8 kHz) at least 20 dB quieter",
                           lambda d, w: _drop(d, w, 2000, 8000, 20)),
    "telephone_voice": ("<150 Hz and >5 kHz each at least 15 dB quieter",
                        lambda d, w: _both(_drop(d, w, 20, 150, 15), _drop(d, w, 5000, 12000, 15))),
    "walkie_talkie_radio": ("<150 Hz and >5 kHz each at least 15 dB quieter",
                            lambda d, w: _both(_drop(d, w, 20, 150, 15), _drop(d, w, 5000, 12000, 15))),
    "hall_echo_reverb": ("audible echo tail (> -40 dB re. signal) in the 1.5 s of silence after the signal",
                         lambda d, w: _tail(d, w, 30)),
    "voiceover_quick_polish": ("35 Hz rumble at least 10 dB quieter and peak <= -0.8 dBFS",
                               lambda d, w: _both(_drop(d, w, 25, 45, 10), _peak(w, -0.8))),
}


def _drop(d, w, lo, hi, need):
    # compare relative to the 300-1500 Hz voice band so make-up gain does not hide the change
    rel = lambda a: band_db(a, lo, hi) - band_db(a, 300, 1500)
    delta = rel(d) - rel(w)
    return delta >= need, f"{lo}-{hi} Hz down {delta:.1f} dB (need {need})"


def _tail(d, w, need):
    wet = rms_db(w, 2.05, 3.4) - rms_db(w, 0.2, 2.0)
    dry = rms_db(d, 2.05, 3.4) - rms_db(d, 0.2, 2.0)
    return wet - dry >= need and wet > -40, f"echo tail {wet:.1f} dB re. signal (dry tail {max(dry, -120):.0f} dB)"


def _peak(w, maxdb):
    pk = 20 * np.log10(np.abs(w).max())
    return pk <= maxdb, f"peak {pk:.2f} dBFS"


def _both(a, b):
    return a[0] and b[0], f"{a[1]}; {b[1]}"


def main():
    results = []
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "voice.wav")
        make_voice(src)
        dry_path = os.path.join(td, "dry.wav")
        open(os.path.join(td, "empty.xml"), "w").write('<effectgroup id="dry"/>')
        rc, bad = render(os.path.join(td, "empty.xml"), src, dry_path)
        _, dry = read_wav(dry_path)
        for path in sorted(glob.glob(os.path.join(ROOT, "pack", "1080p", "effect-templates", "ouzfx_afx_audio_*.xml"))):
            key = os.path.basename(path)[len("ouzfx_afx_audio_"):-4]
            out = os.path.join(td, key + ".wav")
            rc, bad = render(path, src, out)
            ok = rc == 0 and not bad and os.path.exists(out)
            detail = "render failed"
            if ok:
                sr, wet = read_wav(out)
                ok_len = abs(len(wet) - len(dry)) < SR * 0.1
                good, detail = EXPECT[key][1](dry, wet)
                ok = ok and ok_len and good
            results.append(dict(kind="audio-template", id="ouzfx_afx_audio_" + key, ok=bool(ok), check=EXPECT[key][0],
                                detail=detail, warnings=bad[:3]))
            print(f"{'OK ' if ok else 'BAD'} audio {key:26} {detail} {bad[:1]}")
    for f in sorted(glob.glob(os.path.join(ROOT, "sfx", "*", "*.wav"))):
        sr, a = read_wav(f)
        pk = 20 * np.log10(np.abs(a).max())
        edge = max(np.abs(a[:16]).max(), np.abs(a[-16:]).max())
        ok = sr == 48000 and -1.3 <= pk <= -0.9 and edge < 0.01
        detail = f"{sr} Hz, {len(a) / sr:.2f} s, peak {pk:.2f} dBFS, edge {edge:.4f}"
        results.append(dict(kind="sfx", id=os.path.relpath(f, ROOT), ok=bool(ok), detail=detail))
        print(f"{'OK ' if ok else 'BAD'} sfx   {os.path.basename(f):36} {detail}")
    json.dump(results, open(os.path.join(ROOT, "docs", "audio-test-results.json"), "w"), indent=1)
    bad = [r for r in results if not r["ok"]]
    print(f"\n{len(results) - len(bad)}/{len(results)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

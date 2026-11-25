#!/usr/bin/env python3
"""Synthesize the OuzFX sound-effect clips (risers, pops, whooshes, impacts).

100% generated from noise and oscillators with numpy – no samples, no third-party
audio – so the files are original and MIT-licensed like the rest of the pack.
Output: sfx/<group>/ouzfx_<name>.wav  (48 kHz, 16-bit stereo, peak -1 dBFS,
short fades so they never click).

usage: python3 tools/make_sfx.py
"""
import json
import os
import wave

import numpy as np

SR = 48000
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "sfx")
rng = np.random.default_rng(20261125)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def noise(dur, color="white"):
    n = rng.standard_normal(int(dur * SR))
    if color == "pink":
        spec = np.fft.rfft(n)
        f = np.fft.rfftfreq(len(n), 1 / SR)
        f[0] = f[1]
        n = np.fft.irfft(spec / np.sqrt(f), len(n))
    return n / (np.abs(n).max() + 1e-9)


def moving_bandpass(x, fc, q=1.2, nfft=2048, hop=256):
    """Time-varying band-pass by overlap-add spectral shaping. fc: centre Hz per sample."""
    win = np.hanning(nfft)
    pad = np.concatenate([np.zeros(nfft), x, np.zeros(nfft)])
    fcp = np.concatenate([np.full(nfft, fc[0]), fc, np.full(nfft, fc[-1])])
    out = np.zeros_like(pad)
    norm = np.zeros_like(pad)
    freqs = np.fft.rfftfreq(nfft, 1 / SR)
    lf = np.log(np.maximum(freqs, 1.0))
    for start in range(0, len(pad) - nfft, hop):
        seg = pad[start:start + nfft] * win
        c = max(fcp[start + nfft // 2], 20.0)
        width = 1.0 / q
        g = np.exp(-0.5 * ((lf - np.log(c)) / width) ** 2)
        out[start:start + nfft] += np.fft.irfft(np.fft.rfft(seg) * g, nfft) * win
        norm[start:start + nfft] += win ** 2
    out = out / np.maximum(norm, 1e-6)
    return out[nfft:nfft + len(x)]


def sweep(f0, f1, dur, shape="exp", wave_="sine"):
    t = t_axis(dur)
    if shape == "exp":
        f = f0 * (f1 / f0) ** (t / dur)
    else:
        f = f0 + (f1 - f0) * (t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    if wave_ == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1.0) - 1, f
    return np.sin(ph), f


def env_adsr(n, a, r, curve=1.0):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na) ** curve
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** curve
    return e


def lowpass1(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def stereo(x, pan=None, width=0.0):
    """pan: array or scalar in [-1, 1]; width adds a decorrelated side signal."""
    if pan is None:
        pan = 0.0
    pan = np.broadcast_to(pan, x.shape)
    l = x * np.cos((pan + 1) * np.pi / 4)
    r = x * np.sin((pan + 1) * np.pi / 4)
    if np.any(width):
        d = int(0.011 * SR)
        side = np.concatenate([np.zeros(d), x[:-d]]) * width
        l, r = l + side * 0.5, r - side * 0.5
    return np.stack([l, r], axis=1)


def finish(st, fade_in=0.003, fade_out=0.02, peak_db=-1.0):
    n = len(st)
    e = np.ones(n)
    fi, fo = max(int(fade_in * SR), 1), max(int(fade_out * SR), 1)
    e[:fi] = np.linspace(0, 1, fi)
    e[-fo:] = np.linspace(1, 0, fo) ** 2
    st = st * e[:, None]
    st -= st.mean(axis=0)  # no DC offset
    st[:fi] *= np.linspace(0, 1, fi)[:, None]
    st[-fo:] *= np.linspace(1, 0, fo)[:, None]
    peak = np.abs(st).max()
    return st * (10 ** (peak_db / 20) / peak)


def write_wav(path, st):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pcm = np.clip(np.round(st * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ------------------------------------------------------------------ designs

def riser(dur, f0=300, f1=7000, tone=(180, 1100)):
    t = t_axis(dur)
    x = t / dur
    n = moving_bandpass(noise(dur, "pink"), f0 * (f1 / f0) ** (x ** 1.4), q=1.5)
    n /= np.abs(n).max()
    s1, _ = sweep(tone[0], tone[1], dur, wave_="saw")
    s2, _ = sweep(tone[0] * 1.01, tone[1] * 1.01, dur, wave_="saw")
    tones = lowpass1((s1 + s2) * 0.5, 2500)
    trem = 1 - 0.35 * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(2 + 14 * x ** 2) / SR))
    mix = (0.75 * n + 0.35 * tones / np.abs(tones).max()) * (x ** 2.2) * trem
    return stereo(mix, pan=0.0, width=0.6 * x)


def reverse_cymbal(dur):
    t = t_axis(dur)
    n = moving_bandpass(noise(dur), np.full(len(t), 7500.0), q=0.7)
    decay = np.exp(-t / (dur / 4.5))
    return stereo((n / np.abs(n).max() * decay)[::-1], width=0.7)


def tension_riser(dur):
    t = t_axis(dur)
    x = t / dur
    layers = 0
    for det in (0.995, 1.0, 1.006):
        s, _ = sweep(110 * det, 440 * det, dur, wave_="saw")
        layers = layers + s
    layers = lowpass1(layers / 3, 1800)
    rate = np.cumsum(3 + 22 * x ** 2) / SR
    trem = 0.55 + 0.45 * np.sin(2 * np.pi * rate)
    hiss = moving_bandpass(noise(dur), 2000 * (5 ** x), q=1.2)
    mix = (layers / np.abs(layers).max() * trem + 0.3 * hiss / np.abs(hiss).max()) * x ** 1.8
    return stereo(mix, width=0.5)


def pop(f0, f1, dur, click=0.0, decay=25.0, harmonics=0.2):
    t = t_axis(dur)
    s, f = sweep(f0, f1, dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) + harmonics * np.sin(2 * ph)
    e = np.exp(-t * decay) * np.minimum(1, t / 0.0015)
    out = body * e
    if click:
        cl = noise(dur) * np.exp(-t * 900) * click
        out = out + cl
    return stereo(out)


def whoosh(dur, f_lo=250, f_hi=3500, q=1.1, pan=(-0.7, 0.7), sub=0.0, peak_at=0.55, bright=1.0):
    t = t_axis(dur)
    x = t / dur
    bell = np.where(x < peak_at, (x / peak_at) ** 2, ((1 - x) / (1 - peak_at)) ** 1.6)
    fc = f_lo + (f_hi - f_lo) * bell ** 1.2 * bright
    n = moving_bandpass(noise(dur, "pink"), fc, q=q)
    n = n / np.abs(n).max() * bell
    if sub:
        s, _ = sweep(90, 38, dur)
        n = n + sub * s * bell ** 1.5
    p = pan[0] + (pan[1] - pan[0]) * x
    return stereo(n, pan=p, width=0.25)


def impact(dur, kick=(70, 32), noise_amt=0.6, tail=2.2):
    t = t_axis(dur)
    s, f = sweep(kick[0], kick[1], dur)
    body = s * np.exp(-t * tail)
    crack = moving_bandpass(noise(dur), np.full(len(t), 1800.0), q=0.6) * np.exp(-t * 28)
    crack /= np.abs(crack).max()
    rumble = moving_bandpass(noise(dur, "pink"), np.full(len(t), 90.0), q=1.0) * np.exp(-t * tail * 0.8)
    rumble /= np.abs(rumble).max()
    return stereo(body + noise_amt * crack + 0.4 * rumble, width=0.3)


SFX = [
    ("risers", "riser_short_2s", "Short riser (2 s): filtered noise + detuned saw sweep that builds into a cut.",
     lambda: finish(riser(2.0), fade_in=0.05, fade_out=0.012)),
    ("risers", "riser_long_4s", "Long build-up riser (4 s) with accelerating tremolo – intros, reveals.",
     lambda: finish(riser(4.0, 200, 8000, (110, 880)), fade_in=0.1, fade_out=0.012)),
    ("risers", "riser_reverse_cymbal_2s", "Reverse-cymbal swell (2 s) that sucks into the cut.",
     lambda: finish(reverse_cymbal(2.0), fade_in=0.05, fade_out=0.008)),
    ("risers", "riser_tension_3s", "Tension riser (3 s): rising detuned synth with speeding tremolo.",
     lambda: finish(tension_riser(3.0), fade_in=0.08, fade_out=0.012)),
    ("risers", "downlifter_2s", "Downlifter (2 s): the riser in reverse – falls away after a drop.",
     lambda: finish(riser(2.0)[::-1].copy(), fade_in=0.004, fade_out=0.3)),
    ("pops", "pop_soft", "Soft pop (90 ms) – captions, stickers, gentle UI pops.",
     lambda: finish(pop(950, 320, 0.09, 0.0, 38), fade_out=0.01)),
    ("pops", "pop_hard", "Hard pop (80 ms) with a click transient – punchy text slams.",
     lambda: finish(pop(1600, 180, 0.08, 0.9, 45, 0.35), fade_out=0.01)),
    ("pops", "pop_bubble", "Bubble 'bloop' (120 ms) with an upward pitch – emojis, notifications.",
     lambda: finish(pop(380, 1250, 0.12, 0.0, 30, 0.1), fade_out=0.012)),
    ("pops", "pop_click_ui", "Tiny UI click (30 ms) – cursor clicks, checkmarks, counters.",
     lambda: finish(pop(2400, 1800, 0.03, 0.5, 160, 0.0), fade_out=0.006)),
    ("whooshes", "whoosh_fast", "Fast whoosh (0.4 s, panned L→R) – slides and quick transitions.",
     lambda: finish(whoosh(0.4, 300, 4500, 1.2, peak_at=0.5), fade_out=0.03)),
    ("whooshes", "whoosh_slow", "Slow airy whoosh (1.2 s) – Ken Burns, fades, soft reveals.",
     lambda: finish(whoosh(1.2, 200, 2500, 0.9, pan=(-0.4, 0.4), peak_at=0.6), fade_in=0.02, fade_out=0.06)),
    ("whooshes", "whoosh_heavy", "Heavy whoosh (0.8 s) with a sub sweep – zoom-throughs, big moves.",
     lambda: finish(whoosh(0.8, 150, 2200, 1.0, pan=(-0.3, 0.3), sub=0.8, peak_at=0.55), fade_out=0.05)),
    ("whooshes", "swoosh_whip", "Whip swoosh (0.25 s), bright and snappy – whip pans, Whip-In.",
     lambda: finish(whoosh(0.25, 800, 7000, 1.4, pan=(0.8, -0.8), peak_at=0.4), fade_out=0.02)),
    ("whooshes", "whoosh_reverse_suck", "Reverse 'suck' whoosh (0.6 s) that ends on the cut.",
     lambda: finish(whoosh(0.6, 250, 3800, 1.1, pan=(0.0, 0.0), peak_at=0.85), fade_out=0.008)),
    ("impacts", "impact_boom", "Cinematic boom (1.6 s): sub kick + crack + rumble – Boom Zoom, Impact Hit.",
     lambda: finish(impact(1.6), fade_out=0.15)),
    ("impacts", "impact_punch", "Short punchy hit (0.5 s) – shakes, smash cuts, text slams.",
     lambda: finish(impact(0.5, (120, 45), 0.9, 7.0), fade_out=0.05)),
]


def main():
    meta = []
    for group, name, desc, fn in SFX:
        st = fn()
        path = os.path.join(OUT, group, f"ouzfx_{name}.wav")
        write_wav(path, st)
        meta.append(dict(group=group, file=f"sfx/{group}/ouzfx_{name}.wav", name=name, desc=desc,
                         seconds=round(len(st) / SR, 3)))
        print(f"{group:9} ouzfx_{name}.wav  {len(st) / SR:.2f}s")
    json.dump(meta, open(os.path.join(OUT, "sfx.json"), "w"), indent=1)


if __name__ == "__main__":
    main()

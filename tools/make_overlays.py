#!/usr/bin/env python3
"""Generate royalty-free overlay clips (light leak, film burn) for Screen/Add blending."""
import os
import subprocess
import numpy as np

OUT = os.path.join(os.path.dirname(__file__), "..", "overlays")
W, H, FPS = 1280, 720, 25


def blob_frames(n, blobs, seed):
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    params = [(rng.uniform(-0.2, 1.2), rng.uniform(-0.2, 1.2), rng.uniform(0.15, 0.45), rng.uniform(-0.6, 0.6),
               rng.uniform(-0.3, 0.3), c) for c in blobs]
    for i in range(n):
        t = i / n
        img = np.zeros((H, W, 3), np.float32)
        env = np.sin(np.pi * t) ** 1.5
        for (bx, by, r, vx, vy, col) in params:
            cx, cy = (bx + vx * t) * W, (by + vy * t) * H
            d2 = ((x - cx) ** 2 + (y - cy) ** 2) / (r * W) ** 2
            img += np.exp(-d2)[..., None] * np.array(col, np.float32)
        img = np.clip(img * env, 0, 1)
        yield (img * 255).astype(np.uint8).tobytes()


def encode(name, frames, n):
    os.makedirs(OUT, exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "26", "-preset", "slow",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", os.path.join(OUT, name)], stdin=subprocess.PIPE)
    for fr in frames:
        p.stdin.write(fr)
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    encode("ouzfx_light_leak.mp4", blob_frames(100, [(1.0, 0.55, 0.15), (1.0, 0.3, 0.1), (0.9, 0.75, 0.4)], 3), 100)
    encode("ouzfx_film_burn.mp4", blob_frames(40, [(1.0, 0.45, 0.05), (1.0, 0.85, 0.5), (1.0, 0.2, 0.0), (1.0, 0.6, 0.2)], 9), 40)
    print("ok")

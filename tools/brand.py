"""OuzFX brand kit values (source: docs/BRAND.md, extracted from the brand kit PDF)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "fonts")

# name: (hex, role)
COLORS = {
    "slate":     ("#141619", "Carbon Slate - dark backgrounds, text on light accents"),
    "chalk":     ("#F4F4F0", "Lab Chalk - warm light canvas, sticker outlines"),
    "tangerine": ("#FF5A26", "Signal Tangerine - primary focal accent (~7%)"),
    "cobalt":    ("#2D5BFF", "Blueprint Cobalt - charts, UI, data"),
    "volt":      ("#C8FF2E", "Acid Volt - micro status highlight (~3%)"),
}

def rgb(name):
    h = COLORS[name][0].lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def rgbf(name):
    return tuple(c / 255.0 for c in rgb(name))

FONTS = {
    # role: (family, file, variation name, css weight)
    "display": ("Bricolage Grotesque", "BricolageGrotesque-Variable.ttf", "ExtraBold", 800),
    "body":    ("Plus Jakarta Sans", "PlusJakartaSans-Variable.ttf", "SemiBold", 600),
    "mono":    ("JetBrains Mono", "JetBrainsMono-Variable.ttf", "Bold", 700),
}

def font_path(role):
    return os.path.join(FONT_DIR, FONTS[role][1])

# geometry rules at 1080 reference scale
CORNER_RADIUS = 16      # "crisp 16px rounded frames"
STICKER_OUTLINE = 5     # "crisp 5px Lab Chalk outline"
STROKE = 12             # highlight stroke weight (1080 ref)
TRACKING = -0.03        # -2% .. -4% on display type

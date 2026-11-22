"""Golden Hour Ramen — one bowl, one star ingredient.

Composition (1024 x 1024): a big bowl seen from a 3/4 top angle, centred
slightly low, warm light from the left, dark wood table, warm bokeh
behind. The star is the ajitama egg, halved, its orange yolk glossy and
melting at the middle of the bowl. No text anywhere in the picture.
"""

import math
import random

from canvas import Canvas, mix

W = H = 1024

# ---- palette ------------------------------------------------------------
BG_TOP = (0.13, 0.08, 0.04)      # dark warm brown
BG_BOTTOM = (0.05, 0.03, 0.02)
TABLE_TOP = (0.23, 0.14, 0.07)    # dark wood
TABLE_BOTTOM = (0.10, 0.06, 0.03)
GLOW = (1.0, 0.62, 0.20)          # golden-hour light
BOWL_OUT = (0.10, 0.12, 0.20)     # deep indigo ceramic
BOWL_IN = (0.16, 0.19, 0.30)
BOWL_RIM = (0.85, 0.55, 0.25)     # warm rim light
BROTH_IN = (0.98, 0.72, 0.25)     # golden broth, bright centre
BROTH_OUT = (0.72, 0.38, 0.08)
NOODLE = (0.95, 0.78, 0.35)       # glossy yellow noodles
NOODLE_DARK = (0.80, 0.55, 0.15)
EGG_WHITE = (0.98, 0.95, 0.88)
YOLK_IN = (1.0, 0.62, 0.08)       # molten orange yolk
YOLK_OUT = (0.85, 0.35, 0.02)
GREEN = (0.25, 0.65, 0.25)        # fresh scallion
GREEN_DARK = (0.12, 0.40, 0.15)
NORI = (0.05, 0.10, 0.05)
PINK = (0.95, 0.55, 0.60)         # narutomaki swirl
CHOP = (0.55, 0.32, 0.12)         # wooden chopsticks


def _bokeh(c, seed=11):
    rnd = random.Random(seed)
    spots = [(180, 150, 58, 0.13), (840, 120, 44, 0.10),
             (930, 300, 30, 0.08), (90, 330, 36, 0.07),
             (700, 60, 26, 0.09), (330, 90, 20, 0.07)]
    for _ in range(10):
        spots.append((rnd.randint(40, 984), rnd.randint(30, 320),
                      rnd.randint(10, 22), rnd.uniform(0.04, 0.09)))
    for cx, cy, r, a in spots:
        c.ellipse(cx, cy, r, r, (1.0, 0.75, 0.35), a, soft=r * 0.5)


def _table(c):
    for y in range(640, H):
        t = (y - 640) / (H - 640)
        col = mix(TABLE_TOP, TABLE_BOTTOM, t)
        base = y * W
        for x in range(W):
            c.px[base + x] = col
    # soft wood sheen catching the left light
    c.radial_glow(180, 900, 420, (0.55, 0.32, 0.10), 0.20)
    # faint plank seams
    for y in (760, 890):
        for x in range(W):
            c.blend(x, y, (0.03, 0.02, 0.01), 0.35)


def _bowl(c):
    cx, cy = 512, 600
    # body: big dark ellipse, lower half reads as the bowl's side
    c.ellipse_gradient(cx, cy + 30, 350, 250, BOWL_IN, (0.05, 0.06, 0.12),
                       soft=6.0)
    # foot ring
    c.ellipse(cx, cy + 235, 150, 34, (0.05, 0.06, 0.11), 0.9, soft=4.0)
    # rim highlight on the left where the light hits
    c.ellipse(cx - 210, cy - 20, 120, 34, BOWL_RIM, 0.35, soft=14.0,
              rot=-0.25)
    # inner rim (broth surface sits inside this)
    c.ellipse_gradient(cx, cy - 10, 315, 138, BROTH_IN, BROTH_OUT, soft=5.0)
    # glossy light streak on the broth, left side
    c.ellipse(cx - 150, cy - 55, 130, 26, (1.0, 0.9, 0.6), 0.35,
              soft=16.0, rot=-0.15)


def _noodles(c):
    rnd = random.Random(23)
    # wavy strands fanned across the broth, mostly left and centre
    for i in range(9):
        yb = 545 + i * 11 + rnd.randint(-4, 4)
        amp = rnd.uniform(7, 14)
        wl = rnd.uniform(90, 150)
        ph = rnd.uniform(0, 6.28)
        col = NOODLE if i % 2 == 0 else NOODLE_DARK
        c.wavy_band(260, 770, yb, amp, wl, ph, 13, col, 0.95)
    # a lifted clump: noodles raised by the chopsticks, upper right
    for i in range(5):
        yb = 470 + i * 10
        c.wavy_band(560, 760, yb, 9, 110, i * 0.9, 12,
                    NOODLE if i % 2 == 0 else NOODLE_DARK, 0.95)
    # chopsticks resting diagonally over the lifted clump
    c.thick_line(700, 190, 585, 480, 13, CHOP, 0.95)
    c.thick_line(735, 205, 625, 485, 13, (0.48, 0.27, 0.10), 0.95)
    # chopstick tips catching light
    c.thick_line(700, 190, 668, 268, 13, (0.75, 0.5, 0.22), 0.5)


def _egg_half(c, cx, cy, rot):
    """One halved ajitama: white body, molten orange yolk, gloss dot."""
    c.ellipse(cx, cy, 74, 88, EGG_WHITE, 1.0, soft=4.0, rot=rot)
    c.ellipse(cx, cy, 62, 76, (0.94, 0.88, 0.75), 1.0, soft=4.0, rot=rot)
    # yolk: bright centre melting to deep orange rim
    c.ellipse_gradient(cx, cy + 6, 46, 54, YOLK_IN, YOLK_OUT, soft=5.0,
                       rot=rot)
    # molten drip: yolk spilling a little over the white at the bottom
    c.ellipse(cx - 6, cy + 52, 20, 14, YOLK_IN, 0.95, soft=5.0, rot=rot)
    # gloss highlight on the yolk
    c.ellipse(cx - 16, cy - 18, 16, 10, (1.0, 0.95, 0.75), 0.75,
              soft=6.0, rot=rot)
    # gloss on the white
    c.ellipse(cx - 30, cy - 40, 18, 9, (1.0, 1.0, 1.0), 0.35, soft=7.0,
              rot=rot)


def _toppings(c):
    # narutomaki: white fish cake with a pink swirl, left of the eggs
    c.ellipse(300, 585, 42, 40, (0.97, 0.94, 0.90), 1.0, soft=3.0)
    c.ellipse(300, 585, 30, 28, PINK, 0.9, soft=3.0)
    c.ellipse(300, 585, 18, 16, (0.97, 0.94, 0.90), 1.0, soft=2.0)
    c.ellipse(300, 585, 7, 6, PINK, 1.0, soft=2.0)
    # nori sheet standing at the back right of the bowl
    c.ellipse(738, 545, 26, 58, NORI, 1.0, soft=4.0, rot=0.28)
    c.ellipse(732, 538, 15, 42, (0.10, 0.18, 0.10), 0.8, soft=4.0,
              rot=0.28)
    # scallion rings scattered over the broth
    rnd = random.Random(41)
    spots = [(380, 640), (640, 640), (700, 600), (330, 640), (560, 660),
             (420, 690), (680, 660), (250, 590), (760, 590), (480, 620)]
    for (x, y) in spots:
        r = rnd.randint(9, 13)
        c.ellipse(x, y, r, r * 0.8, GREEN_DARK, 1.0, soft=2.0)
        c.ellipse(x, y, r - 3, (r - 3) * 0.8, GREEN, 1.0, soft=2.0)
        c.ellipse(x, y, 3, 2, (0.15, 0.45, 0.15), 1.0, soft=1.0)


def _steam(c):
    """Thin translucent rising wisps above the bowl."""
    rnd = random.Random(5)
    for i in range(4):
        x0 = 380 + i * 90 + rnd.randint(-15, 15)
        y = 470
        prev = None
        while y > 210:
            x = x0 + 42 * math.sin((470 - y) / 70.0 + i * 1.3)
            if prev is not None:
                c.thick_line(prev[0], prev[1], x, y, 9,
                             (1.0, 0.95, 0.85), 0.06)
            prev = (x, y)
            y -= 8
    # soft glow above the broth: heat shimmer
    c.ellipse(512, 480, 260, 60, (1.0, 0.85, 0.6), 0.10, soft=40.0)


def draw():
    c = Canvas(W, H)
    c.vertical_gradient(BG_TOP, BG_BOTTOM)
    c.radial_glow(150, 120, 520, GLOW, 0.30)   # golden hour, from the left
    _bokeh(c)
    _table(c)
    _bowl(c)
    _noodles(c)
    # the star: two egg halves, front and centre
    _egg_half(c, 452, 600, -0.12)
    _egg_half(c, 585, 608, 0.10)
    _toppings(c)
    _steam(c)
    # chopsticks again on top so they read over the steam wisps
    c.thick_line(700, 190, 585, 480, 13, CHOP, 0.95)
    c.thick_line(735, 205, 625, 485, 13, (0.48, 0.27, 0.10), 0.95)
    c.vignette(0.30)
    c.grain(0.008)
    return c

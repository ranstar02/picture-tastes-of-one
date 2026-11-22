"""Golden Pancake Stack — the scene.

A stack of three golden pancakes on a white plate, warm morning light
from the left, maple syrup dripping down the sides, melting butter on
top, fresh berries beside the stack, a little steam, and a small cup of
black coffee blurred in the background.  No text anywhere.
"""

import math
import random

from draw import Canvas, clamp, mix

W = H = 1024

# -- palette (float RGB, 0..1) ---------------------------------------------
WOOD_TOP = (0.23, 0.15, 0.10)
WOOD_BOT = (0.10, 0.065, 0.045)
GLOW = (1.0, 0.72, 0.38)
PLATE = (0.96, 0.95, 0.92)
PLATE_SHADE = (0.78, 0.76, 0.72)
PLATE_RIM = (0.88, 0.86, 0.82)
CAKE_LIGHT = (0.98, 0.78, 0.42)
CAKE_MID = (0.88, 0.60, 0.26)
CAKE_DARK = (0.62, 0.36, 0.12)
CAKE_EDGE = (0.55, 0.30, 0.09)
SYRUP = (0.72, 0.38, 0.05)
SYRUP_DARK = (0.45, 0.20, 0.02)
SYRUP_HI = (1.0, 0.72, 0.28)
BUTTER = (1.0, 0.88, 0.45)
BUTTER_DARK = (0.94, 0.72, 0.25)
BLUEBERRY = (0.16, 0.18, 0.42)
BLUEBERRY_HI = (0.45, 0.50, 0.85)
STRAWBERRY = (0.85, 0.16, 0.16)
STRAWBERRY_DARK = (0.55, 0.06, 0.08)
LEAF = (0.20, 0.45, 0.18)
SUGAR = (1.0, 1.0, 1.0)
COFFEE = (0.12, 0.08, 0.06)
CUP = (0.16, 0.14, 0.13)
STEAM = (1.0, 1.0, 1.0)


def _pancake(cv, cx, cy, rx, ry, top_hi=True):
    """One pancake: golden body, toasted top, darker crisp rim."""
    cv.ellipse(cx, cy, rx, ry, CAKE_EDGE, alpha=1.0, feather=2.0)
    cv.ellipse(cx, cy - 2, rx - 6, ry - 5, CAKE_MID, alpha=1.0, feather=3.0)
    # toasted top, lighter toward the upper-left where the light hits
    cv.ellipse_gradient(cx - rx * 0.08, cy - ry * 0.22, rx - 14, ry - 10,
                        CAKE_LIGHT, CAKE_MID, feather=3.0)
    # speckles of toast
    rng = random.Random(int(cx + cy))
    for _ in range(46):
        a = rng.uniform(0, 6.283)
        rr = rng.uniform(0.15, 0.92)
        px = cx + math.cos(a) * rx * rr * 0.92
        py = cy - ry * 0.18 + math.sin(a) * ry * rr * 0.8
        r = rng.uniform(1.5, 4.5)
        tone = rng.choice([CAKE_DARK, CAKE_LIGHT])
        cv.circle(px, py, r, tone, alpha=rng.uniform(0.12, 0.30), feather=1.0)


def _syrup_drip(cv, x, y_top, length, width):
    """One thick syrup drip running down the side of the stack."""
    cv.rounded_rect(x - width / 2, y_top, x + width / 2, y_top + length,
                    width / 2, SYRUP, alpha=0.95)
    cv.circle(x, y_top + length, width / 2 + 1, SYRUP, alpha=0.95, feather=1.5)
    # glossy streak on the drip
    cv.rounded_rect(x - width / 2 + 2, y_top + 4, x - width / 2 + 5,
                    y_top + length - 4, 1.5, SYRUP_HI, alpha=0.55)


def _blueberry(cv, cx, cy, r):
    cv.ellipse_gradient(cx - r * 0.15, cy - r * 0.2, r, r,
                        BLUEBERRY_HI, BLUEBERRY, feather=1.5)
    cv.circle(cx - r * 0.35, cy - r * 0.4, r * 0.28, (0.9, 0.9, 1.0),
              alpha=0.85, feather=1.5)
    cv.circle(cx, cy - r * 0.1, r * 0.22, (0.08, 0.09, 0.25),
              alpha=0.8, feather=1.0)


def _strawberry(cv, cx, cy, r, tilt=0.0):
    # plump red body: two overlapping ellipses make the heart shape
    cv.ellipse(cx, cy, r * 0.95, r * 1.05, STRAWBERRY_DARK, alpha=1.0, feather=2.0)
    cv.ellipse_gradient(cx - r * 0.1, cy - r * 0.25, r * 0.8, r * 0.85,
                        (0.98, 0.35, 0.28), STRAWBERRY, feather=2.0)
    cv.circle(cx - r * 0.4, cy - r * 0.45, r * 0.25, (1.0, 0.65, 0.55),
              alpha=0.7, feather=2.0)
    # seeds
    rng = random.Random(int(cx * 3 + cy))
    for _ in range(14):
        a = rng.uniform(0, 6.283)
        rr = rng.uniform(0.2, 0.75)
        sx = cx + math.cos(a) * r * rr
        sy = cy + math.sin(a) * r * rr * 0.9
        cv.circle(sx, sy, 1.8, (1.0, 0.9, 0.6), alpha=0.85, feather=0.8)
    # leafy top
    for k, ang in enumerate((-0.6, 0.0, 0.6)):
        lx = cx + math.sin(ang) * r * 0.45
        ly = cy - r * 0.95 + abs(math.cos(ang)) * r * 0.1
        cv.ellipse(lx, ly, r * 0.22, r * 0.38, LEAF, alpha=0.95, feather=1.0)


def _butter(cv, cx, cy):
    """A pat of butter, half-melted, sliding on the top pancake."""
    cv.rounded_rect(cx - 52, cy - 26, cx + 52, cy + 20, 10, BUTTER_DARK, alpha=1.0)
    cv.rounded_rect(cx - 50, cy - 28, cx + 50, cy + 12, 10, BUTTER, alpha=1.0)
    cv.rounded_rect(cx - 44, cy - 26, cx + 44, cy - 12, 8, (1.0, 0.96, 0.75),
                    alpha=0.9)
    # melt pool spreading from the butter
    cv.blob(cx + 10, cy + 22, 62, 12, BUTTER, alpha=0.85, seed=11)


def _coffee_cup(cv):
    """Small black coffee in the background, top right (will be blurred)."""
    cx, cy = 815, 235
    cv.ellipse(cx, cy, 105, 34, (0.05, 0.04, 0.03), alpha=1.0, feather=4.0)
    cv.ellipse(cx, cy - 6, 92, 30, CUP, alpha=1.0, feather=4.0)
    cv.ellipse(cx, cy - 8, 78, 24, (0.03, 0.02, 0.015), alpha=1.0, feather=3.0)
    cv.ellipse(cx, cy - 8, 78, 24, (0.10, 0.06, 0.03), alpha=0.5, feather=3.0)
    cv.ring(cx + 108, cy - 2, 30, 34, 9, CUP, alpha=1.0, feather=3.0)
    # saucer
    cv.ellipse(cx, cy + 42, 125, 22, (0.20, 0.18, 0.16), alpha=1.0, feather=4.0)


def _steam(cv):
    """Thin warm steam ribbons rising above the stack."""
    for k, (x0, phase, amp) in enumerate([(470, 0.0, 14), (512, 1.8, 18),
                                          (556, 3.4, 13)]):
        for j in range(3):
            yb = 500 - j * 14
            cv.wavy_band(x0 - 26, x0 + 26, yb, amp, 110, 3,
                         STEAM, alpha=0.07 - j * 0.015, phase=phase + j * 0.7)


def _sugar(cv):
    """A dusting of powdered sugar over the stack and plate."""
    rng = random.Random(99)
    for _ in range(240):
        a = rng.uniform(0, 6.283)
        rr = rng.uniform(0.1, 1.0)
        x = 512 + math.cos(a) * 300 * rr
        y = 600 + math.sin(a) * 95 * rr
        if 500 < y < 720:
            cv.circle(x, y, rng.uniform(0.8, 2.2), SUGAR,
                      alpha=rng.uniform(0.35, 0.8), feather=0.8)


def render() -> Canvas:
    cv = Canvas(W, H)

    # 1. dark wooden table + warm morning glow from the left
    cv.vertical_gradient(WOOD_TOP, WOOD_BOT)
    cv.radial_glow(120, 180, 620, GLOW, 0.34)
    cv.radial_glow(512, 620, 700, (0.55, 0.32, 0.14), 0.16)

    # 2. coffee cup, blurred into the background (whole-canvas blur so
    #    there is no hard rectangle edge around the blurred region)
    _coffee_cup(cv)
    cv.box_blur(3)

    # 3. plate: soft shadow, then the white dish with a rim
    cv.ellipse(512, 700, 345, 108, (0.0, 0.0, 0.0), alpha=0.45, feather=14.0)
    cv.ellipse(512, 688, 330, 104, PLATE_SHADE, alpha=1.0, feather=2.0)
    cv.ellipse(512, 682, 322, 98, PLATE, alpha=1.0, feather=2.0)
    cv.ring(512, 682, 296, 88, 3, PLATE_RIM, alpha=0.9, feather=2.0)

    # 4. the stack: three pancakes, each a little smaller and higher
    _pancake(cv, 512, 668, 292, 56)
    _pancake(cv, 512, 618, 272, 54)
    _pancake(cv, 510, 570, 246, 52)

    # 5. syrup: a glossy pool on top, drips down the sides, a puddle
    cv.blob(510, 556, 200, 30, SYRUP, alpha=0.96, seed=5)
    cv.blob(510, 556, 170, 22, SYRUP_DARK, alpha=0.32, seed=6)
    cv.ellipse(470, 548, 70, 10, SYRUP_HI, alpha=0.5, feather=3.0)
    _syrup_drip(cv, 300, 585, 78, 16)
    _syrup_drip(cv, 700, 600, 62, 14)
    _syrup_drip(cv, 620, 612, 44, 12)
    _syrup_drip(cv, 380, 620, 52, 13)
    cv.blob(640, 700, 130, 16, SYRUP, alpha=0.9, seed=21)
    cv.blob(300, 706, 90, 12, SYRUP, alpha=0.85, seed=22)

    # 6. butter melting on top
    _butter(cv, 512, 532)

    # 7. berries on the plate beside the stack
    _blueberry(cv, 236, 706, 26)
    _blueberry(cv, 288, 726, 22)
    _blueberry(cv, 262, 736, 18)
    _blueberry(cv, 792, 716, 24)
    _strawberry(cv, 772, 676, 34)
    _strawberry(cv, 226, 668, 28)

    # 8. powdered sugar, steam, then finishing polish
    _sugar(cv)
    _steam(cv)
    cv.grain(0.0, seed=1234)
    cv.vignette(0.16)
    return cv

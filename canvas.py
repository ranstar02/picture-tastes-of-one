"""A tiny software rasterizer on a float RGB buffer.

Everything is drawn with soft edges on purpose: real food has no hard
pixel staircases, and soft alpha falloffs compress well in PNG. Only the
standard library is used (math, random).
"""

import math
import random


def clamp01(v):
    return 0.0 if v < 0.0 else 1.0 if v > 1.0 else v


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


class Canvas:
    def __init__(self, width, height, bg=(0.0, 0.0, 0.0)):
        self.w = width
        self.h = height
        self.px = [bg] * (width * height)

    def _idx(self, x, y):
        return y * self.w + x

    def blend(self, x, y, color, alpha):
        """Blend one pixel; alpha in [0, 1]; silently ignores out-of-range."""
        if alpha <= 0.0 or x < 0 or y < 0 or x >= self.w or y >= self.h:
            return
        i = self._idx(x, y)
        r, g, b = self.px[i]
        a = clamp01(alpha)
        self.px[i] = (lerp(r, color[0], a), lerp(g, color[1], a),
                      lerp(b, color[2], a))

    def fill(self, color):
        self.px = [color] * (self.w * self.h)

    def vertical_gradient(self, top, bottom):
        for y in range(self.h):
            t = y / max(1, self.h - 1)
            c = mix(top, bottom, t)
            base = y * self.w
            for x in range(self.w):
                self.px[base + x] = c

    def radial_glow(self, cx, cy, radius, color, strength):
        """Warm glow fading with distance; strength is peak alpha."""
        r0 = int(max(0, cx - radius))
        r1 = int(min(self.w - 1, cx + radius))
        y0 = int(max(0, cy - radius))
        y1 = int(min(self.h - 1, cy + radius))
        for y in range(y0, y1 + 1):
            for x in range(r0, r1 + 1):
                d = math.hypot(x - cx, y - cy) / radius
                if d >= 1.0:
                    continue
                fall = (1.0 - d) * (1.0 - d)
                self.blend(x, y, color, strength * fall)

    def ellipse(self, cx, cy, rx, ry, color, alpha=1.0, soft=2.0,
                rot=0.0):
        """Filled ellipse with a soft antialiased rim.

        soft: rim width in pixels over which alpha fades to zero.
        rot: rotation in radians (counter-clockwise).
        """
        cosr = math.cos(rot)
        sinr = math.sin(rot)
        x0 = int(max(0, cx - rx - soft - 2))
        x1 = int(min(self.w - 1, cx + rx + soft + 2))
        y0 = int(max(0, cy - ry - soft - 2))
        y1 = int(min(self.h - 1, cy + ry + soft + 2))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                dx = x - cx
                dy = y - cy
                # rotate point back into ellipse space
                lx = dx * cosr + dy * sinr
                ly = -dx * sinr + dy * cosr
                q = (lx / rx) ** 2 + (ly / ry) ** 2
                if q >= 1.0 + soft / max(rx, ry):
                    continue
                edge = 1.0 - clamp01((math.sqrt(max(q, 0.0)) - 1.0)
                                     * max(rx, ry) / max(soft, 0.5))
                self.blend(x, y, color, alpha * edge)

    def ellipse_gradient(self, cx, cy, rx, ry, inner, outer, soft=3.0,
                         rot=0.0):
        """Ellipse shaded from a bright centre to a darker rim."""
        cosr = math.cos(rot)
        sinr = math.sin(rot)
        x0 = int(max(0, cx - rx - soft - 2))
        x1 = int(min(self.w - 1, cx + rx + soft + 2))
        y0 = int(max(0, cy - ry - soft - 2))
        y1 = int(min(self.h - 1, cy + ry + soft + 2))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                dx = x - cx
                dy = y - cy
                lx = dx * cosr + dy * sinr
                ly = -dx * sinr + dy * cosr
                q = (lx / rx) ** 2 + (ly / ry) ** 2
                if q >= 1.05:
                    continue
                t = clamp01(math.sqrt(max(q, 0.0)))
                # ease the falloff so the centre stays bright longer
                t = t * t * (3.0 - 2.0 * t)
                col = mix(inner, outer, t)
                edge = 1.0 - clamp01((math.sqrt(max(q, 0.0)) - 1.0)
                                     * max(rx, ry) / max(soft, 0.5))
                self.blend(x, y, col, edge)

    def thick_line(self, x0, y0, x1, y1, width, color, alpha=1.0):
        """A capsule stroke between two points, soft rim."""
        steps = int(math.hypot(x1 - x0, y1 - y0)) + 1
        r = width / 2.0
        for s in range(steps + 1):
            t = s / max(1, steps)
            self.ellipse(lerp(x0, x1, t), lerp(y0, y1, t), r, r,
                         color, alpha, soft=1.5)

    def wavy_band(self, x0, x1, y_base, amp, wavelength, phase, width,
                  color, alpha=1.0):
        """A sine-wave band, like a noodle strand or a wisp of steam."""
        step = 3
        prev = None
        x = x0
        while x <= x1:
            y = y_base + amp * math.sin(2.0 * math.pi * (x / wavelength)
                                        + phase)
            if prev is not None:
                self.thick_line(prev[0], prev[1], x, y, width, color,
                                alpha)
            prev = (x, y)
            x += step

    def box_blur(self, passes=1, radius=2):
        """Separable box blur, in place, a few passes for a soft glow."""
        w, h = self.w, self.h
        for _ in range(passes):
            # horizontal
            tmp = [None] * (w * h)
            for y in range(h):
                base = y * w
                for x in range(w):
                    sr = sg = sb = 0.0
                    cnt = 0
                    for k in range(-radius, radius + 1):
                        xx = x + k
                        if 0 <= xx < w:
                            r, g, b = self.px[base + xx]
                            sr += r
                            sg += g
                            sb += b
                            cnt += 1
                    tmp[base + x] = (sr / cnt, sg / cnt, sb / cnt)
            # vertical
            for y in range(h):
                for x in range(w):
                    sr = sg = sb = 0.0
                    cnt = 0
                    for k in range(-radius, radius + 1):
                        yy = y + k
                        if 0 <= yy < h:
                            r, g, b = tmp[yy * w + x]
                            sr += r
                            sg += g
                            sb += b
                            cnt += 1
                    self.px[y * w + x] = (sr / cnt, sg / cnt, sb / cnt)

    def grain(self, amount, seed=7):
        """Fine luminance grain so flat areas do not band in PNG."""
        rnd = random.Random(seed)
        for i in range(len(self.px)):
            n = (rnd.random() - 0.5) * amount
            r, g, b = self.px[i]
            self.px[i] = (clamp01(r + n), clamp01(g + n), clamp01(b + n))

    def vignette(self, strength=0.35):
        cx, cy = self.w / 2.0, self.h / 2.0
        maxd = math.hypot(cx, cy)
        for y in range(self.h):
            for x in range(self.w):
                d = math.hypot(x - cx, y - cy) / maxd
                f = 1.0 - strength * (d * d)
                r, g, b = self.px[y * self.w + x]
                self.px[y * self.w + x] = (r * f, g * f, b * f)

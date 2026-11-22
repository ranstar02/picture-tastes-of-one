"""A tiny software rasterizer on a float RGB buffer.

Everything here is written from scratch for this picture: soft-edged
ellipses and circles, linear and radial gradients, a cheap box blur, a
grain pass and alpha-blended shapes.  No third-party libraries.
"""

import math
import random


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def mix(a, b, t):
    return a + (b - a) * t


class Canvas:
    def __init__(self, width, height):
        self.w = width
        self.h = height
        # flat float buffer, three channels per pixel, values 0..1
        self.px = [0.0] * (width * height * 3)

    # -- basic pixel access -------------------------------------------------
    def set_px(self, x, y, rgb):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = rgb[0]
            self.px[i + 1] = rgb[1]
            self.px[i + 2] = rgb[2]

    def get_px(self, x, y):
        i = (y * self.w + x) * 3
        return (self.px[i], self.px[i + 1], self.px[i + 2])

    def blend_px(self, x, y, rgb, alpha):
        """Blend *rgb* over the pixel at (x, y) with opacity *alpha*."""
        if alpha <= 0.0 or not (0 <= x < self.w and 0 <= y < self.h):
            return
        if alpha >= 1.0:
            self.set_px(x, y, rgb)
            return
        i = (y * self.w + x) * 3
        self.px[i] = mix(self.px[i], rgb[0], alpha)
        self.px[i + 1] = mix(self.px[i + 1], rgb[1], alpha)
        self.px[i + 2] = mix(self.px[i + 2], rgb[2], alpha)

    # -- fills --------------------------------------------------------------
    def fill(self, rgb):
        for i in range(0, len(self.px), 3):
            self.px[i] = rgb[0]
            self.px[i + 1] = rgb[1]
            self.px[i + 2] = rgb[2]

    def vertical_gradient(self, top, bottom):
        for y in range(self.h):
            t = y / max(1, self.h - 1)
            c = (mix(top[0], bottom[0], t),
                 mix(top[1], bottom[1], t),
                 mix(top[2], bottom[2], t))
            for x in range(self.w):
                self.set_px(x, y, c)

    def radial_glow(self, cx, cy, radius, rgb, strength):
        """Add a soft warm glow centred at (cx, cy)."""
        r2 = radius * radius
        x0 = max(0, int(cx - radius))
        x1 = min(self.w - 1, int(cx + radius))
        y0 = max(0, int(cy - radius))
        y1 = min(self.h - 1, int(cy + radius))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if d2 >= r2:
                    continue
                t = 1.0 - math.sqrt(d2) / radius
                self.blend_px(x, y, rgb, strength * t * t)

    # -- shapes -------------------------------------------------------------
    def ellipse(self, cx, cy, rx, ry, rgb, alpha=1.0, feather=1.0):
        """Filled ellipse with a soft (feathered) edge."""
        x0 = max(0, int(cx - rx - feather))
        x1 = min(self.w - 1, int(cx + rx + feather))
        y0 = max(0, int(cy - ry - feather))
        y1 = min(self.h - 1, int(cy + ry + feather))
        for y in range(y0, y1 + 1):
            ny = (y - cy) / ry
            for x in range(x0, x1 + 1):
                nx = (x - cx) / rx
                d = nx * nx + ny * ny
                if d > 1.0 + feather / min(rx, ry):
                    continue
                if d <= 1.0:
                    a = alpha
                else:
                    a = alpha * clamp(1.0 - (math.sqrt(d) - 1.0) * min(rx, ry) / feather)
                self.blend_px(x, y, rgb, a)

    def circle(self, cx, cy, r, rgb, alpha=1.0, feather=1.0):
        self.ellipse(cx, cy, r, r, rgb, alpha, feather)

    def ellipse_gradient(self, cx, cy, rx, ry, inner, outer, feather=1.0):
        """Ellipse shading from *inner* colour at the centre to *outer*."""
        x0 = max(0, int(cx - rx - feather))
        x1 = min(self.w - 1, int(cx + rx + feather))
        y0 = max(0, int(cy - ry - feather))
        y1 = min(self.h - 1, int(cy + ry + feather))
        for y in range(y0, y1 + 1):
            ny = (y - cy) / ry
            for x in range(x0, x1 + 1):
                nx = (x - cx) / rx
                d = math.sqrt(nx * nx + ny * ny)
                if d > 1.0 + feather / min(rx, ry):
                    continue
                t = clamp(d)
                c = (mix(inner[0], outer[0], t),
                     mix(inner[1], outer[1], t),
                     mix(inner[2], outer[2], t))
                a = 1.0 if d <= 1.0 else clamp(1.0 - (d - 1.0) * min(rx, ry) / feather)
                self.blend_px(x, y, c, a)

    def ring(self, cx, cy, rx, ry, thickness, rgb, alpha=1.0, feather=1.5):
        """Soft-edged elliptical ring (outline of an ellipse)."""
        x0 = max(0, int(cx - rx - thickness - feather))
        x1 = min(self.w - 1, int(cx + rx + thickness + feather))
        y0 = max(0, int(cy - ry - thickness - feather))
        y1 = min(self.h - 1, int(cy + ry + thickness + feather))
        for y in range(y0, y1 + 1):
            ny = (y - cy) / ry
            for x in range(x0, x1 + 1):
                nx = (x - cx) / rx
                d = math.sqrt(nx * nx + ny * ny)
                dist = abs(d - 1.0) * min(rx, ry)
                if dist > thickness + feather:
                    continue
                if dist <= thickness:
                    a = alpha
                else:
                    a = alpha * clamp(1.0 - (dist - thickness) / feather)
                self.blend_px(x, y, rgb, a)

    def rounded_rect(self, x0, y0, x1, y1, radius, rgb, alpha=1.0):
        """Filled rectangle with rounded corners and a soft edge."""
        for y in range(max(0, int(y0)), min(self.h, int(y1) + 1)):
            for x in range(max(0, int(x0)), min(self.w, int(x1) + 1)):
                dx = max(x0 + radius - x, 0.0, x - (x1 - radius))
                dy = max(y0 + radius - y, 0.0, y - (y1 - radius))
                d = math.hypot(dx, dy)
                if d <= radius:
                    self.blend_px(x, y, rgb, alpha)

    def blob(self, cx, cy, rx, ry, rgb, alpha=1.0, seed=7, wobble=0.12):
        """Ellipse whose outline wobbles like a hand-poured syrup pool."""
        rng = random.Random(seed)
        phases = [rng.uniform(0, 6.283) for _ in range(5)]
        amps = [rng.uniform(0.4, 1.0) * wobble for _ in range(5)]
        x0 = max(0, int(cx - rx * 1.25))
        x1 = min(self.w - 1, int(cx + rx * 1.25))
        y0 = max(0, int(cy - ry * 1.25))
        y1 = min(self.h - 1, int(cy + ry * 1.25))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                ang = math.atan2((y - cy) / ry, (x - cx) / rx)
                w = 1.0
                for k in range(5):
                    w += amps[k] * math.sin((k + 2) * ang + phases[k])
                d = math.hypot((x - cx) / rx, (y - cy) / ry) / w
                if d >= 1.0:
                    continue
                a = alpha * clamp((1.0 - d) * 6.0, 0.0, 1.0)
                self.blend_px(x, y, rgb, a)

    def wavy_band(self, x0, x1, y_base, amp, wavelength, thickness,
                  rgb, alpha=1.0, phase=0.0, y_step=1):
        """A horizontal wavy ribbon (used for syrup drips and steam)."""
        for x in range(max(0, int(x0)), min(self.w, int(x1) + 1)):
            yc = y_base + amp * math.sin(6.28318 * (x - x0) / wavelength + phase)
            for y in range(int(yc - thickness), int(yc + thickness) + 1):
                if 0 <= y < self.h:
                    edge = 1.0 - abs(y - yc) / (thickness + 0.5)
                    self.blend_px(x, y, rgb, alpha * clamp(edge))

    # -- post-processing ----------------------------------------------------
    def box_blur(self, radius, x0=0, y0=0, x1=None, y1=None):
        """Cheap separable box blur over a region of the buffer."""
        if radius < 1:
            return
        if x1 is None:
            x1 = self.w
        if y1 is None:
            y1 = self.h
        src = self.px[:]
        w, h = self.w, self.h
        tmp = [0.0] * len(src)
        span = 2 * radius + 1
        for y in range(y0, y1):
            for x in range(x0, x1):
                acc = [0.0, 0.0, 0.0]
                for dx in range(-radius, radius + 1):
                    xx = min(max(x + dx, 0), w - 1)
                    i = (y * w + xx) * 3
                    acc[0] += src[i]
                    acc[1] += src[i + 1]
                    acc[2] += src[i + 2]
                i = (y * w + x) * 3
                tmp[i] = acc[0] / span
                tmp[i + 1] = acc[1] / span
                tmp[i + 2] = acc[2] / span
        for y in range(y0, y1):
            for x in range(x0, x1):
                acc = [0.0, 0.0, 0.0]
                for dy in range(-radius, radius + 1):
                    yy = min(max(y + dy, 0), h - 1)
                    i = (yy * w + x) * 3
                    acc[0] += tmp[i]
                    acc[1] += tmp[i + 1]
                    acc[2] += tmp[i + 2]
                i = (y * w + x) * 3
                self.px[i] = acc[0] / span
                self.px[i + 1] = acc[1] / span
                self.px[i + 2] = acc[2] / span

    def grain(self, amount=0.02, seed=42):
        rng = random.Random(seed)
        for i in range(len(self.px)):
            self.px[i] = clamp(self.px[i] + rng.uniform(-amount, amount))

    def vignette(self, strength=0.18):
        cx, cy = self.w / 2.0, self.h / 2.0
        maxd = math.hypot(cx, cy)
        for y in range(self.h):
            for x in range(self.w):
                d = math.hypot(x - cx, y - cy) / maxd
                f = 1.0 - strength * d * d
                i = (y * self.w + x) * 3
                self.px[i] *= f
                self.px[i + 1] *= f
                self.px[i + 2] *= f

    def to_pixels(self):
        out = []
        for i in range(0, len(self.px), 3):
            out.append((int(clamp(self.px[i]) * 255 + 0.5),
                        int(clamp(self.px[i + 1]) * 255 + 0.5),
                        int(clamp(self.px[i + 2]) * 255 + 0.5)))
        return out

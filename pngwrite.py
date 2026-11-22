"""PNG encoder, pure Python standard library.

Takes a flat list of RGB float triples in [0, 1] plus width/height and
writes a valid 8-bit RGB PNG. Uses zlib for compression and picks, per
scanline, the filter (None / Sub / Up) with the smallest sum of absolute
signed-byte residuals, which keeps photographic-style gradients compact.
"""

import struct
import zlib


def _chunk(kind, data):
    body = kind + data
    crc = zlib.crc32(body) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + body + struct.pack(">I", crc)


def _filter_line(filter_type, line, prev):
    """Return one filtered scanline (filter byte + filtered bytes)."""
    out = bytearray()
    out.append(filter_type)
    n = len(line)
    if filter_type == 0:
        out += line
    elif filter_type == 1:  # Sub: left neighbour, 3 bytes back
        for i in range(n):
            left = line[i - 3] if i >= 3 else 0
            out.append((line[i] - left) & 0xFF)
    elif filter_type == 2:  # Up: pixel above
        for i in range(n):
            up = prev[i] if prev else 0
            out.append((line[i] - up) & 0xFF)
    else:
        raise ValueError("unsupported filter %d" % filter_type)
    return bytes(out)


def _score_filtered(filtered):
    """Cheap proxy for compressibility: sum of |signed byte| values."""
    total = 0
    for b in filtered[1:]:
        total += b if b < 128 else 256 - b
    return total


def encode_png(pixels, width, height):
    """pixels: sequence of (r, g, b) floats in [0, 1], row-major, len w*h."""
    raw = bytearray()
    prev = None
    for y in range(height):
        base = y * width
        line = bytearray(width * 3)
        for x in range(width):
            r, g, b = pixels[base + x]
            line[3 * x] = max(0, min(255, int(r * 255 + 0.5)))
            line[3 * x + 1] = max(0, min(255, int(g * 255 + 0.5)))
            line[3 * x + 2] = max(0, min(255, int(b * 255 + 0.5)))
        best = None
        best_score = None
        for ftype in (0, 1, 2):
            cand = _filter_line(ftype, bytes(line), prev)
            score = _score_filtered(cand)
            if best_score is None or score < best_score:
                best, best_score = cand, score
        raw += best
        prev = bytes(line)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


def write_png(path, pixels, width, height):
    data = encode_png(pixels, width, height)
    with open(path, "wb") as f:
        f.write(data)
    return len(data)

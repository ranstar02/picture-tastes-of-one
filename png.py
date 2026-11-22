"""Minimal PNG encoder, pure Python standard library.

Takes a width, a height and a flat list of (r, g, b) byte triples in
row-major order and returns the bytes of a truecolour PNG.  Each scanline
is written with filter type 0 (None) and compressed with zlib at level 6,
which keeps the output small enough for the 1 MiB cap without any
third-party library.
"""

import struct
import zlib


def _chunk(kind: bytes, payload: bytes) -> bytes:
    """One PNG chunk: length, type, data, CRC32 over type + data."""
    crc = zlib.crc32(kind)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def encode_png(width: int, height: int, pixels) -> bytes:
    """Encode *pixels* (row-major iterable of (r, g, b) ints 0..255).

    Every row after the first uses the Up filter (each byte minus the
    byte above it), which makes smooth gradients compress far better
    than raw scanlines; zlib level 9 keeps the file under the 1 MiB cap.
    """
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = bytearray()
    row_bytes = width * 3
    flat = list(pixels)
    prev = bytearray(row_bytes)
    for y in range(height):
        row = bytearray(row_bytes)
        base = y * width
        for x in range(width):
            r, g, b = flat[base + x]
            j = x * 3
            row[j] = r & 0xFF
            row[j + 1] = g & 0xFF
            row[j + 2] = b & 0xFF
        if y == 0:
            raw.append(0)  # filter: None
            raw += row
        else:
            raw.append(2)  # filter: Up
            raw += bytes((v - p) & 0xFF for v, p in zip(row, prev))
        prev = row
    out = bytearray(b"\x89PNG\r\n\x1a\n")
    out += _chunk(b"IHDR", header)
    out += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    out += _chunk(b"IEND", b"")
    return bytes(out)

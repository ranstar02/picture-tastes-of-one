"""Golden Pancake Stack — entrypoint.

Renders the pancake scene with the pure-stdlib rasterizer in cakes.py
and writes one PNG to $MAKEFUN_OUTPUT_DIR/entry.png (default
/output/entry.png).  No network, no third-party packages, runs in a few
seconds.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cakes import render  # noqa: E402
from png import encode_png  # noqa: E402


def main():
    started = time.time()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")

    canvas = render()
    data = encode_png(canvas.w, canvas.h, canvas.to_pixels())
    with open(out_path, "wb") as fh:
        fh.write(data)

    print(f"wrote {out_path} ({len(data)} bytes, "
          f"{canvas.w}x{canvas.h}) in {time.time() - started:.1f}s")


if __name__ == "__main__":
    main()

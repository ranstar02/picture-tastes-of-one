"""Golden Hour Ramen — make.fun entry.

Renders one 1024x1024 picture of a bowl of ramen whose star ingredient
is the halved ajitama egg, using only the Python standard library, and
writes it to /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png when
that variable is set, or the path given as the first argument).

    python3 main.py [output-path]
"""

import os
import sys

from pngwrite import write_png
from ramen import W, H, draw


def default_output_path():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    return os.path.join(out_dir, "entry.png")


def main(argv):
    path = argv[1] if len(argv) > 1 else default_output_path()
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    canvas = draw()
    size = write_png(path, canvas.px, W, H)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

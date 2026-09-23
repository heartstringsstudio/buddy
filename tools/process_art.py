"""Turn the ChatGPT PNGs in art/ into game sprites in sprites/.

- Removes scraps of neighbouring figures that ChatGPT leaves sliced off at the
  edge of each figure's box.
- Crops every pose of a stage to one shared box, so the dragon stays the same
  size when he changes pose.
- The bone is cropped tight on its own.

Run from the repo root:  python3 tools/process_art.py   (needs pillow, numpy, scipy)
"""
import glob
import os

import numpy as np
from PIL import Image
from scipy import ndimage

SIZE = 640


def clean(path):
    a = np.array(Image.open(path).convert("RGBA"))
    m = a[..., 3] > 12
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    main = int(np.argmax(sizes)) + 1
    for i in range(1, n + 1):
        if i == main:
            continue
        c = lab == i
        # A piece with a long flat edge on the figure's box was sliced from a neighbour.
        cut = max(c[:, x0].sum(), c[:, x1].sum(), c[y0, :].sum(), c[y1, :].sum())
        if cut >= 12 or sizes[i - 1] < 30:
            a[c] = 0
    return a


def bbox(a, pad):
    ys, xs = np.nonzero(a[..., 3] > 12)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    p = int(pad * max(x1 - x0, y1 - y0))
    h, w = a.shape[:2]
    return max(0, x0 - p), max(0, y0 - p), min(w - 1, x1 + p), min(h - 1, y1 + p)


def save(a, box, name):
    im = Image.fromarray(a).crop((box[0], box[1], box[2] + 1, box[3] + 1))
    sc = SIZE / max(im.size)
    im = im.resize((round(im.size[0] * sc), round(im.size[1] * sc)), Image.LANCZOS)
    im.save(f"sprites/{name}.webp", "WEBP", quality=86, method=6)


def main():
    os.makedirs("sprites", exist_ok=True)
    art = {os.path.basename(f)[:-4]: clean(f) for f in sorted(glob.glob("art/*.png"))}
    for stage in ["egg", "baby", "teen", "adult"]:
        names = [k for k in art if k.startswith(stage + "-")]
        if not names:
            continue
        boxes = [bbox(art[k], 0) for k in names]
        x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
        p = int(0.03 * max(x1 - x0, y1 - y0))
        box = (max(0, x0 - p), max(0, y0 - p), min(1023, x1 + p), min(1023, y1 + p))
        for k in names:
            save(art[k], box, k)
        print(stage, ", ".join(sorted(names)))
    if "bone" in art:
        save(art["bone"], bbox(art["bone"], 0.04), "bone")
        print("bone")


if __name__ == "__main__":
    main()

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


def clean(im):
    a = np.array(im.convert("RGBA"))
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


EXTRAS = ("run", "fetch")  # action poses fitted into the stage's standing box


def fit_into(a, box):
    """Place a pose on a canvas the size of the stage box, feet on the same floor line,
    shrinking it only if it would not fit."""
    bw, bh = box[2] - box[0] + 1, box[3] - box[1] + 1
    x0, y0, x1, y1 = bbox(a, 0)
    fig = Image.fromarray(a).crop((x0, y0, x1 + 1, y1 + 1))
    f = min(1.0, (bw * 0.98) / fig.size[0], (bh * 0.98) / fig.size[1])
    if f < 1:
        fig = fig.resize((round(fig.size[0] * f), round(fig.size[1] * f)), Image.LANCZOS)
    canvas = Image.new("RGBA", (bw, bh))
    floor = bh - int(0.03 * bh)
    canvas.paste(fig, ((bw - fig.size[0]) // 2, floor - fig.size[1]), fig)
    return np.array(canvas), (0, 0, bw - 1, bh - 1)


def load(path):
    im = Image.open(path).convert("RGBA")
    if im.size != (1024, 1024):  # later uploads came out at 1254px; match the original framing
        im = im.resize((1024, 1024), Image.LANCZOS)
    return clean(im)


def main():
    os.makedirs("sprites", exist_ok=True)
    art = {os.path.basename(f)[:-4]: load(f) for f in sorted(glob.glob("art/*.png"))}
    for stage in ["egg", "baby", "teen", "adult"]:
        names = [k for k in art if k.startswith(stage + "-")]
        core = [k for k in names if k.split("-")[1] not in EXTRAS]
        if not core:
            continue
        boxes = [bbox(art[k], 0) for k in core]
        x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
        p = int(0.03 * max(x1 - x0, y1 - y0))
        box = (max(0, x0 - p), max(0, y0 - p), min(1023, x1 + p), min(1023, y1 + p))
        for k in core:
            save(art[k], box, k)
        for k in names:
            if k not in core:
                save(*fit_into(art[k], box), k)
        print(stage, ", ".join(sorted(names)))
    if "bone" in art:
        save(art["bone"], bbox(art["bone"], 0.04), "bone")
        print("bone")


if __name__ == "__main__":
    main()

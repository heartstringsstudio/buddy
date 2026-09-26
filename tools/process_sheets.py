"""Cut the ChatGPT art sheets in art/sheet-*.png into game images in sprites/.

Each sheet is a grid; items are listed left to right, top to bottom. Transparent sheets
are cropped to each item's visible pixels; the tile sheet (white gaps, no transparency)
is cropped to each tile's non-white square.

Also writes gear-wvcap-flip.webp: the cap with its "WV" letters mirrored in place. The
game shows it while he faces left (his whole picture is mirrored then), so the letters
read the right way round.

Run from the repo root:  python3 tools/process_sheets.py   (needs pillow, numpy, scipy)
"""
import numpy as np
from PIL import Image
from scipy import ndimage

# sheet: (columns, rows, [(name, max size px) ...])
SHEETS = {
    "sheet-1-hats": (3, 2, [("gear-sunhat", 400), ("gear-beanie", 400), ("gear-cowboy", 400),
                            ("gear-crown", 400), ("gear-party", 400), ("gear-bow", 400)]),
    "sheet-2-headwear-eyewear": (3, 2, [("gear-bandana", 400), ("gear-phones", 400), ("gear-wvcap", 400),
                                        ("gear-shades", 400), ("gear-hearts", 400), ("gear-specs", 400)]),
    "sheet-3-icons": (3, 2, [("icon-jam", 160), ("icon-riff", 160), ("icon-mine", 160),
                             ("icon-match", 160), ("icon-whack", 160)]),
    "sheet-4-cards": (3, 2, [("card-guitar", 200), ("card-drum", 200), ("card-mic", 200),
                             ("card-phones", 200), ("card-flame", 200), ("card-bolt", 200)]),
    "sheet-5-crowd": (2, 1, [("whack-heckler", 240), ("whack-fan", 240)]),
    "sheet-7-gems": (3, 1, [("gem-ruby", 160), ("gem-sapphire", 160), ("gem-emerald", 160)]),
}
TILES = ("sheet-6-tiles", 3, 2, [("card-back", 240), ("whack-amp", 240), ("mine-rock", 200),
                                 ("mine-dug", 200), ("mine-water", 200)])


def cells(w, h, cols, rows):
    for r in range(rows):
        for c in range(cols):
            yield (c * w // cols, r * h // rows, (c + 1) * w // cols, (r + 1) * h // rows)


def save(im, name, size):
    im.thumbnail((size, size), Image.LANCZOS)
    im.save(f"sprites/{name}.webp", "WEBP", quality=88, method=6)
    print(name, im.size)
    return im


def cut_transparent(sheet, cols, rows, names):
    im = Image.open(f"art/{sheet}.png").convert("RGBA")
    for (name, size), box in zip(names, cells(*im.size, cols, rows)):
        part = im.crop(box)
        px = np.asarray(part).copy()
        # Drop scraps of neighbouring items: separate pieces that touch the cell's edge.
        m = px[..., 3] > 40
        lab, n = ndimage.label(m, structure=np.ones((3, 3)))
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        biggest = int(np.argmax(sizes)) + 1
        edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
        for i in range(1, n + 1):
            if i != biggest and (i in edge or sizes[i - 1] < 40):
                px[lab == i, 3] = 0
        part = Image.fromarray(px)
        a = px[..., 3]
        ys, xs = np.nonzero(a > 40)
        part = part.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        # Clear the colour hidden in fully transparent pixels (ChatGPT leaves a glow there),
        # so it can't bleed into the edges when the picture is scaled.
        px = np.asarray(part).copy()
        px[px[..., 3] == 0, :3] = 0
        if name == "icon-riff":  # the same drum pads, large, as the Riff Recall game board
            save(Image.fromarray(px).copy(), "riff-board", 480)
        part = save(Image.fromarray(px), name, size)
        if name == "gear-bandana":
            save(cut_bandana_back(Image.open(f"sprites/{name}.webp").convert("RGBA")), name, size)
        if name == "gear-wvcap":
            save(flip_letters(Image.open(f"sprites/{name}.webp").convert("RGBA")), "gear-wvcap-flip", size)


def cut_bandana_back(band):
    """Remove the back of the headband loop (the narrower, shadowed band seen through the
    opening), so only the front band and the knot sit on his head. The opening between the two
    bands is measured where it's clear (the middle of the band), a smooth curve is fitted
    through it, and everything below the curve is faded out, from just right of the knot to a
    short curl where the bands join on the right. The knot and tails on the left stay."""
    px = np.asarray(band).copy()
    a = px[..., 3] > 60
    h, w = a.shape
    pts = []
    for x in range(int(w * .4), int(w * .82)):
        col = a[:, x]
        ys = np.nonzero(col)[0]
        if not len(ys):
            continue
        y = ys[0]
        while y < h and col[y]:
            y += 1
        gap_top = y
        while y < h and not col[y]:
            y += 1
        if gap_top < h and y < h:
            pts.append((x, (gap_top + y) / 2))
    fx, fy = np.array(pts).T
    curve = np.poly1d(np.polyfit(fx, fy, 2))
    x0, x1 = int(w * .29), int(fx.max())
    yy = np.arange(h)[:, None]
    for x in range(x0, w):
        c = curve(x) if x <= x1 else curve(x1) + (x - x1) * .9  # past the join: a short curl
        fade = np.clip((yy[:, 0] - c) / 3 + .5, 0, 1)  # soft 3px edge
        px[:, x, 3] = (px[:, x, 3] * (1 - fade)).astype(np.uint8)
    return Image.fromarray(px)


def flip_letters(cap):
    """Mirror the gold WV lettering in place (the rest of the cap untouched)."""
    px = np.asarray(cap).astype(int)
    r, g, b, a = px[..., 0], px[..., 1], px[..., 2], px[..., 3]
    h, w = a.shape
    gold = (r > 150) & (g > 110) & (b < 90) & (a > 200)
    gold[int(h * .55):, :] = False  # ignore the gold brim at the bottom
    ys, xs = np.nonzero(gold)
    pad = 4
    box = (max(0, xs.min() - pad), max(0, ys.min() - pad), min(w, xs.max() + 1 + pad), min(h, ys.max() + 1 + pad))
    out = cap.copy()
    out.paste(cap.crop(box).transpose(Image.FLIP_LEFT_RIGHT), box[:2])
    return out


def cut_tiles(sheet, cols, rows, names):
    im = Image.open(f"art/{sheet}.png").convert("RGB")
    for (name, size), box in zip(names, cells(*im.size, cols, rows)):
        part = im.crop(box)
        px = np.asarray(part).astype(int)
        ink = (px < 235).any(-1)
        ys, xs = np.nonzero(ink)
        inset = 4  # trim the anti-aliased edge against the white gap
        part = part.crop((xs.min() + inset, ys.min() + inset, xs.max() + 1 - inset, ys.max() + 1 - inset))
        s = min(part.size)  # make it square
        part = part.crop(((part.width - s) // 2, (part.height - s) // 2, (part.width + s) // 2, (part.height + s) // 2))
        save(part, name, size)


if __name__ == "__main__":
    for sheet, (cols, rows, names) in SHEETS.items():
        cut_transparent(sheet, cols, rows, names)
    cut_tiles(*TILES)

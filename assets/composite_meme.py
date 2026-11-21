#!/usr/bin/env python3
"""Composite the GTA 6 meme: real make.fun ghost (extracted from the press-kit
mark, magenta disc removed) standing in the generated Vice City street,
plus two burned-in meme captions. Output: meme-final.png (1600x1600).

Ghost extraction: the mark is a white ghost (black outline, magenta star coin)
on a magenta disc. We keep white body + black outline adjacent to it + the
magenta coin around the white star, and drop the disc/outer ring.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ASSETS = "/home/hatch/workspace/makefun/gta6-meme-x/assets"
SCENE = f"{ASSETS}/media-generation-gta6-street-scene-0-8a9eae58-63a3-4cfc-a4d7-ead47bd8633e.png"
MARK = f"{ASSETS}/mark-1024.png"
OUT = "/home/hatch/workspace/makefun/gta6-meme-x/meme-final.png"


def extract_ghost(mark_path: str) -> Image.Image:
    im = np.array(Image.open(mark_path).convert("RGB")).astype(np.int16)
    h, w, _ = im.shape
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    white = (r > 225) & (g > 225) & (b > 225)
    black = (r < 80) & (g < 80) & (b < 80)
    # black outline: black pixels near the white body (dilate white ~14 px).
    # The outer black ring is far from any white, so it is excluded; the
    # coin's ring touches the white star/hand/body, so it is included.
    near_white = white.copy()
    for dy, dx in ((14, 0), (-14, 0), (0, 14), (0, -14),
                   (10, 10), (10, -10), (-10, 10), (-10, -10),
                   (7, 0), (-7, 0), (0, 7), (0, -7)):
        near_white |= np.roll(np.roll(white, dy, axis=0), dx, axis=1)
    mask = white | (black & near_white)
    # fill holes: the magenta coin is enclosed by its black ring (the coin's
    # magenta equals the disc's, so it cannot be keyed by colour)
    inv = Image.fromarray(((~mask) * 255).astype(np.uint8))
    ImageDraw.floodfill(inv, (0, 0), 128)
    inv_np = np.array(inv)
    holes = (inv_np == 0) & (~mask)
    mask = mask | holes
    # The coin itself did not survive extraction (its ring is not a closed
    # loop in the mask), so its white star now floats beside the ghost.
    # Remove ONLY the star: it is the small white component at upper right
    # (bbox x 726-825, y 394-495). The ghost alone (white body, sparkle
    # eyes, round hand) is still recognisably the make.fun mascot.
    from scipy import ndimage
    lab, _n = ndimage.label(white)
    star = np.zeros_like(white)
    for i in range(1, _n + 1):
        ys, xs = np.where(lab == i)
        if len(xs) < 20000 and 700 <= xs.mean() <= 850 and 380 <= ys.mean() <= 520:
            star |= lab == i
    mask = mask & (~star)
    # Fill the notch the coin left: a white disc over the old coin's spot
    # (centred on the star), so the ghost reads as one clean blob, with a
    # fresh black border only around the newly added part.
    yy, xx = np.mgrid[0:h, 0:w]
    disc = (xx - 760) ** 2 + (yy - 450) ** 2 < 105 ** 2
    added = disc & (~mask)
    mask = mask | disc
    add_img = Image.fromarray((added * 255).astype(np.uint8))
    border = np.array(add_img.filter(ImageFilter.MaxFilter(17))) > 0
    border = border & (~mask)
    # feather the edge slightly
    alpha = Image.fromarray((mask * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(1.2)
    )
    rgba = np.dstack([im.astype(np.uint8), np.array(alpha)])
    rgba[border] = [0, 0, 0, 255]
    return Image.fromarray(rgba, "RGBA")


def fit_font(text: str, max_width: int, start: int, path: str) -> ImageFont.FreeTypeFont:
    size = start
    while size > 20:
        f = ImageFont.truetype(path, size)
        if f.getbbox(text)[2] <= max_width:
            return f
        size -= 4
    return ImageFont.truetype(path, 20)


def caption(draw: ImageDraw.ImageDraw, text: str, y: int, canvas_w: int, font_path: str):
    font = fit_font(text, canvas_w - 100, 132, font_path)
    x = (canvas_w - font.getbbox(text)[2]) // 2
    draw.text((x, y), text, font=font, fill="white",
              stroke_width=10, stroke_fill="black")


def main() -> None:
    scene = Image.open(SCENE).convert("RGB")
    W, H = scene.size  # 1600x1600
    ghost = extract_ghost(MARK)
    # ghost ~40% of canvas height, standing foreground-centre
    gh = int(H * 0.40)
    gw = int(ghost.width * gh / ghost.height)
    ghost = ghost.resize((gw, gh), Image.LANCZOS)
    gx = (W - gw) // 2
    gy = int(H * 0.80) - gh  # feet at ~80% height
    # soft contact shadow on the wet street
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sw, sh = int(gw * 0.66), int(gh * 0.05)
    sd.ellipse([gx + (gw - sw) // 2, gy + gh - sh // 2,
                gx + (gw + sw) // 2, gy + gh + sh // 2], fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    scene = Image.alpha_composite(scene.convert("RGBA"), shadow)
    scene.alpha_composite(ghost, (gx, gy))
    out = scene.convert("RGB")
    draw = ImageDraw.Draw(out)
    font_path = "/home/hatch/.local/share/fonts/Anton.ttf"
    caption(draw, "SPENT $80 ON GTA 6", 48, W, font_path)
    caption(draw, "MY AI AGENT EARNED IT BACK", H - 178, W, font_path)
    out.save(OUT, "PNG")
    print(f"saved {OUT} {out.size}")


if __name__ == "__main__":
    main()

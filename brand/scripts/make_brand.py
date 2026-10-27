"""Write the dotTide icon, badge and mark SVGs into <repo>/brand.

The mark is called Undertow: a wave that runs right across its frame, with one dot
under the surface. The wave always runs past the edge, so the mark only exists inside
a rounded tile, never as a loose stroke. There is no round badge: in a circle, the
wave and dot read as a yin-yang.
Usage: python3 brand/scripts/make_brand.py brand
"""

import os
import sys

out = sys.argv[1]
for sub in ("mark", "icon"):
    os.makedirs(os.path.join(out, sub), exist_ok=True)

GREEN, FOREST, LIME, INK, WHITE = "#008450", "#003820", "#bef050", "#0f1f17", "#ffffff"
WAVE = "M-6 46 C15 21 34 21 50 46 C66 71 85 71 106 46"
STROKE = 11
DOT = (24, 77, 9)
TILE = '<rect width="100" height="100" rx="23"/>'


def wave_and_dot(color, scale=1):
    cx, cy, r = DOT
    body = (
        f'<path d="{WAVE}" fill="none" stroke="{color}" stroke-width="{STROKE}" '
        f'stroke-linecap="round"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>'
    )
    if scale == 1:
        return body
    return f'<g transform="translate(50 50) scale({scale}) translate(-50 -50)">{body}</g>'


def svg(body, title, size=1024):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="{size}" '
        f'height="{size}"><title>{title}</title>{body}</svg>'
    )


def filled(frame, bg, fg, title, scale=1):
    """A colored frame with the mark drawn on top, clipped so the wave runs off the edge."""
    return svg(
        f'<defs><clipPath id="f">{frame}</clipPath></defs><g clip-path="url(#f)">'
        f'<rect width="100" height="100" fill="{bg}"/>{wave_and_dot(fg, scale)}</g>',
        title,
    )


def knockout(frame, color, title, scale=1):
    """A one-color frame with the mark cut out of it, for single-color use."""
    return svg(
        f'<defs><mask id="k"><rect width="100" height="100" fill="#fff"/>'
        f'{wave_and_dot("#000", scale)}</mask><clipPath id="f">{frame}</clipPath></defs>'
        f'<g clip-path="url(#f)"><rect width="100" height="100" fill="{color}" '
        f'mask="url(#k)"/></g>',
        title,
    )


def write(path, text):
    with open(os.path.join(out, path), "w") as f:
        f.write(text + "\n")


write("icon/dottide-icon-green.svg", filled(TILE, GREEN, WHITE, "dotTide icon, green"))
write("icon/dottide-icon-forest.svg", filled(TILE, FOREST, LIME, "dotTide icon, forest"))
write("icon/dottide-icon-ink.svg", filled(TILE, INK, WHITE, "dotTide icon, ink"))
for name, color in (("green", GREEN), ("ink", INK), ("white", WHITE), ("lime", LIME)):
    write(f"mark/dottide-mark-{name}.svg", knockout(TILE, color, f"dotTide mark, {name}"))

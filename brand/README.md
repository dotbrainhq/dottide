# dotTide brand assets

The dotTide mark is called Undertow: a wave that runs right across the tile, with one dot under the surface. Your numbers are already there, spread across Google accounts and store pages, and dotTide brings them up. The wave always runs past the edge, because the tide is bigger than any one site. The dot is also the Dot in Dotbrain.

## Files

| Path | What it is |
|---|---|
| `icon/` | The icon on the green, forest and ink tiles. |
| `mark/` | One-color versions with the wave and dot cut out of the tile, in green, ink, white and lime. |
| `png/` | 1024 px renders of each icon. |
| `png/sizes/` | The green icon at 16, 32, 48, 128, 256, 512 and 1024 px. |
| `scripts/make_brand.py` | Writes every SVG. |

## Colors

- **Brand green:** `#008450`, the main tile.
- **Forest:** `#003820`, the dark tile.
- **Lime:** `#bef050`, the mark on forest.
- **Ink:** `#0f1f17`, the neutral tile and the one-color dark mark.

## Rebuild

Run the script, render each icon with Chrome, then scale the size set from the 1024 px green render:

```
python3 brand/scripts/make_brand.py brand
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars --default-background-color=00000000 --window-size=1024,1024 --screenshot="$PWD/brand/png/dottide-icon-green-1024.png" "file://$PWD/brand/icon/dottide-icon-green.svg"
for s in 16 32 48 128 256 512 1024; do sips -s format png -z $s $s brand/png/dottide-icon-green-1024.png --out brand/png/sizes/dottide-icon-$s.png; done
```

Repeat the Chrome line for `forest` and `ink`.

## Usage

- Use the green icon almost everywhere, and the forest icon on dark pages.
- The mark only lives inside its tile. Don't draw the wave as a loose stroke: on its own it turns into dotPen's mark.
- Don't put the mark in a circle. In a round frame, the wave and dot read as a yin-yang.
- Keep clear space around the icon equal to the dot's diameter.

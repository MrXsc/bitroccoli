# BitVibe

**Bit-style mosaic image generator.**

Turn any image into a bit-style pixel-art mosaic — rendered in the terminal with colored ANSI symbols, and optionally saved as a high-resolution PNG.

## Features

- **Terminal render** — ANSI TrueColor output with configurable symbol sets
- **PNG export** — save mosaics as high-resolution images
- **Posterize** — reduce to flat color regions for a clean, cartoon-like look
- **Edge detection** — emphasize contours with contrast symbols
- **Presets** — one-flag convenience for optimized settings
- **5 symbol sets** — `default`, `blocks`, `dots`, `cross`, `simple`
- **EXIF auto-rotation** — photos from cameras/phones render right-side up

## Requirements

- Python 3.9+
- [Pillow](https://python-pillow.org) (`pip install Pillow`)

## Quick Start

```bash
# See available flags
python3 bitvibe.py --help

# Basic — 80-wide mosaic in terminal
python3 bitvibe.py -i path/to/photo.JPG

# Sharp preset — flat colors, blocks, 120-wide, PNG save
python3 bitvibe.py --preset sharp -i path/to/photo.JPG -o output/sharp.png

# Posterize + custom width
python3 bitvibe.py -i path/to/photo.JPG -w 100 --posterize 8 -s blocks

# Edge emphasis
python3 bitvibe.py -i path/to/photo.JPG -w 80 --posterize 16 --edge
```

## Options

| Flag | Description |
|---|---|
| `-i`, `--input` | Input image path **(required)** |
| `-w`, `--width` | Mosaic width in tiles (default: `80`) |
| `-s`, `--symbols` | Symbol set to use |
| `-o`, `--output` | Save mosaic as PNG |
| `--preset` | Predefined settings shortcut |
| `--posterize N` | Reduce to N flat colors before mosaicing (default: `0` = off) |
| `--edge` | Emphasize contours via edge detection |
| `--edge-symbol` | Character used for edge cells (default: `+`) |
| `--invert` | Invert brightness-symbol mapping (for light terminal backgrounds) |
| `--cell-size` | Pixel size of each tile in output PNG (default: `16`) |
| `--grid` | Draw grid lines in the output PNG |
| `--list-symbols` | List available symbol sets and exit |

## Presets

| Preset | Equivalent | Best For |
|---|---|---|
| `sharp` | `-w 120 -s blocks --posterize 12` | Pixel-art style with clean, flat color regions and sharp edges |

Use `--preset sharp` and individual flags still override it:

```bash
# sharp, but narrower for terminal viewing
python3 bitvibe.py --preset sharp -w 60 -i photo.JPG
```

## Symbol Sets

| Set | Characters | Vibe |
|---|---|---|
| `default` | `█ ▓ ▒ ░ ● + # @ % * · ` | Balanced, good for photos |
| `blocks` | `█ ▓ ▒ ░ ` | Solid fill, clean pixel art feel |
| `dots` | `█ ▓ ▒ ░ ● · ` | Softer, dither-like |
| `cross` | `+ × * # ` | Geometric, technical |
| `simple` | `@ % # * + · ` | High contrast, ASCII art style |

## Examples

Generated outputs live in `output/`:

```
output/
├── output_cat.png             # Basic render, w=80
├── output_cat_fixed.png       # With EXIF correction
├── output_cat_sharp.png       # --preset sharp (w=120, blocks, posterize 12)
├── output_cat_sharp_w60.png   # Same but w=60
├── output_cat_v2.png          # v2 with EXIF fix
├── output_toys.png            # Basic render
├── output_toys_fixed.png      # With EXIF correction
└── output.png                 # First test run
```

## How It Works

1. **Load** — image is loaded and EXIF orientation is auto-corrected
2. **Posterize** *(optional)* — colors are reduced to N for flat regions
3. **Grid** — image is downsampled to an N×M grid of average RGB values
4. **Render** — each cell is mapped to a brightness symbol and rendered with ANSI TrueColor
5. **Save** *(optional)* — the grid is drawn as colored rectangles and saved as PNG

Terminal character aspect (~2:1 tall) is compensated so the mosaic appears correct on screen; PNG export compensates in the opposite direction for the same reason.

## Development

```
src/
├── main.py      # CLI, argument parsing, orchestration
├── mosaic.py    # load_image, posterize, compute_grid
└── render.py    # render_terminal, save_output_image, detect_edges
```

## License

MIT

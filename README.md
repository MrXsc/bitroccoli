# BitVibe

**Bit-style mosaic image generator.**

Converts images into bit-style pixel-art mosaics, rendered with colored ANSI symbols in the terminal and optionally saved as PNG.

## Requirements

- Python 3.9+
- [Pillow](https://python-pillow.org) (`pip install Pillow`)

## Quick Start

```bash
# Basic usage — render a mosaic in the terminal
python3 bitvibe.py -i path/to/image.JPG

# Sharp mode — flat color regions, blocks, high resolution
python3 bitvibe.py --preset sharp -i path/to/image.JPG

# Save as PNG
python3 bitvibe.py --preset sharp -i path/to/image.JPG -o output.png
```

## Options

| Flag | Description |
|---|---|
| `-i`, `--input` | Input image path (required) |
| `-w`, `--width` | Mosaic width in tiles (default: 80) |
| `-s`, `--symbols` | Symbol set: `default`, `blocks`, `dots`, `cross`, `simple` |
| `-o`, `--output` | Save mosaic as PNG |
| `--posterize N` | Reduce to N flat colors before mosaicing |
| `--edge` | Emphasize contours via edge detection |
| `--grid` | Draw grid lines in the output PNG |
| `--preset` | Apply predefined option sets: `sharp` (= `-w 120 -s blocks --posterize 12`) |

## License

MIT

"""
BitVibe - Bit-style mosaic image generator.

Converts an input image into a mosaic rendered with coloured symbols
in the terminal.  Optionally saves the mosaic as a PNG.
"""

import argparse
import os
import sys
from typing import Optional

from .mosaic import compute_grid, load_image, posterize
from .render import SYMBOL_SETS, render_terminal, save_output_image, detect_edges

# Estimated terminal character aspect ratio (height / width).
# A terminal cell is roughly 2:1 tall.  We use 0.5 so that the
# mosaic appears visually square when printed.
CHAR_ASPECT = 0.5


def _resolve_height(img_w: int, img_h: int, grid_w: int) -> int:
    """Compute mosaic height that preserves the image aspect ratio."""
    h = int(grid_w * (img_h / img_w) * CHAR_ASPECT)
    return max(h, 1)


def _list_symbols() -> None:
    """Print available symbol sets and exit."""
    print("Available symbol sets:")
    for name, syms in SYMBOL_SETS.items():
        print(f"  {name:12s}  {''.join(sym for sym in syms)}")
    sys.exit(0)


# Predefined presets
PRESETS: dict[str, dict[str, object]] = {
    "sharp": {
        "width": 120,
        "symbols": "blocks",
        "posterize": 12,
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bitvibe",
        description="Generate a bit-style mosaic from an image.",
    )
    parser.add_argument(
        "--preset",
        choices=list(PRESETS),
        help="Apply a predefined set of options.  Individual flags override the preset.",
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to input image",
    )
    parser.add_argument(
        "-w", "--width",
        type=int,
        default=80,
        help="Mosaic width in tiles (default: 80)",
    )
    parser.add_argument(
        "-s", "--symbols",
        choices=list(SYMBOL_SETS),
        default="default",
        help="Symbol set to use (default: default)",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert brightness-symbol mapping (useful on light backgrounds)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Save mosaic as PNG (provides path)",
    )
    parser.add_argument(
        "--cell-size",
        type=int,
        default=16,
        help="Pixel width of each tile in the output PNG; height = width × 2 (default: 16)",
    )
    parser.add_argument(
        "--grid",
        action="store_true",
        help="Draw grid lines in the output PNG (only with -o)",
    )
    parser.add_argument(
        "--posterize",
        type=int,
        default=0,
        help="Reduce to N colours before mosaicing for flat, cartoon-like look "
             "(default: 0 = off)",
    )
    parser.add_argument(
        "--edge",
        type=float,
        nargs="?",
        const=40.0,
        default=0.0,
        help="Emphasise contours by detecting edges.  Optional threshold value "
             "(default threshold: 40, pass 0 to disable, pass --edge without value for default)",
    )
    parser.add_argument(
        "--edge-symbol",
        default="+",
        help="Symbol used for edge cells in terminal render (default: +)",
    )
    parser.add_argument(
        "--list-symbols",
        action="store_true",
        help="List available symbol sets and exit",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    # First pass: detect --preset before applying defaults
    args, _ = parser.parse_known_args(argv)

    if args.preset:
        # Apply preset defaults, then re-parse so explicit flags can override
        parser.set_defaults(**PRESETS[args.preset])
        args = parser.parse_args(argv)
    else:
        args = parser.parse_args(argv)

    if args.list_symbols:
        _list_symbols()
        return

    # Load image
    if not os.path.isfile(args.input):
        print(f"Error: file not found — {args.input}", file=sys.stderr)
        sys.exit(1)

    img = load_image(args.input)
    img_w, img_h = img.size
    grid_h = _resolve_height(img_w, img_h, args.width)
    print(f"Image: {img_w}×{img_h}  →  Mosaic: {args.width}×{grid_h}", file=sys.stderr)

    # Optional: posterize → flat colour regions
    if args.posterize > 1:
        img = posterize(img, args.posterize)

    # Build colour grid
    colors = compute_grid(img, args.width, grid_h)

    # Optional: edge mask
    edge_mask = None
    if args.edge > 0:
        edge_mask = detect_edges(colors, threshold=args.edge)

    # Render to terminal
    render_terminal(
        colors,
        symbol_set=args.symbols,
        invert=args.invert,
        edge_mask=edge_mask,
        edge_symbol=args.edge_symbol,
    )

    # Optionally save as PNG
    if args.output:
        save_output_image(
            colors, args.output,
            cell_size=args.cell_size,
            show_grid=args.grid,
            cell_aspect=1.0 / CHAR_ASPECT,
            edge_mask=edge_mask,
        )
        print(f"\nSaved: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()

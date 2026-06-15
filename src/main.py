"""
BitVibe - Bit-style pixel-art mosaic generator.

Renders an image as a pixel-art mosaic in the terminal (half-block ▄
mode by default) and optionally saves a PNG.

Modes
-----
- **Half-block** (default):  uses ``▄`` to pack 2 pixel rows per terminal
  line → 2× vertical resolution, no aspect distortion.
- **Symbol**:  each cell → one colour-mapped symbol (original mode).
"""

import argparse
import os
import shutil
import sys
from typing import Optional, List, Tuple

from .mosaic import (
    ColorGrid,
    compute_grid,
    load_image,
    posterize,
    map_to_palette,
    floyd_steinberg_dither,
    PALETTES,
)
from .render import (
    SYMBOL_SETS,
    render_terminal,
    render_terminal_halfblock,
    save_output_image,
    detect_edges,
    perceived_brightness,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _detect_terminal_width() -> int:
    """Return usable column count, falling back to 80."""
    try:
        w = shutil.get_terminal_size().columns
    except Exception:
        w = 80
    return max(w, 40)


def _resolve_height(img_w: int, img_h: int, grid_w: int, halfblock: bool) -> int:
    """Compute mosaic height that preserves the image aspect ratio.

    In half-block mode the grid height is the **natural** pixel-height of
    the mosaic; the terminal will render ceil(height / 2) rows.
    """
    h = int(grid_w * (img_h / img_w))
    return max(h, 2 if halfblock else 1)


def _list_symbols() -> None:
    """Print available symbol sets and exit."""
    print("Available symbol sets:")
    for name, syms in SYMBOL_SETS.items():
        print(f"  {name:12s}  {''.join(sym for sym in syms)}")
    sys.exit(0)


def _list_palettes() -> None:
    """Print available palettes and exit."""
    print("Available palettes:")
    for name, colors in PALETTES.items():
        descs = {
            "retro": "CGA-inspired 16-colour",
            "gameboy": "Game Boy 4-shade green",
            "mono": "Grayscale 8-stop",
            "pico8": "PICO-8 inspired 16-colour",
            "warm": "Browns/reds/oranges 8-colour",
            "cool": "Blues/teals/purples 8-colour",
        }
        desc = descs.get(name, f"{len(colors)} colours")
        print(f"  {name:12s}  {desc}")
    sys.exit(0)


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

PRESETS: dict[str, dict[str, object]] = {
    "sharp": {
        "width": 120,
        "symbols": "blocks",
        "posterize": 12,
    },
    "retro": {
        "width": 80,
        "palette": "retro",
        "dither": True,
        "posterize": 16,
    },
}

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bitvibe",
        description="Generate a bit-style mosaic from an image.",
    )
    parser.add_argument(
        "--preset",
        choices=list(PRESETS),
        help="Apply a predefined set of options.  Individual flags override.",
    )
    parser.add_argument(
        "-i", "--input",
        default=None,
        help="Path to input image",
    )
    parser.add_argument(
        "-w", "--width",
        type=int,
        default=0,
        help="Mosaic width in tiles (default: auto = terminal width)",
    )
    parser.add_argument(
        "--halfblock",
        action="store_true",
        default=True,
        help="Use half-block ▄ rendering (default: on). "
             "Pass --no-halfblock to use legacy symbol mode.",
    )
    parser.add_argument(
        "--no-halfblock",
        action="store_false",
        dest="halfblock",
        help="Fall back to one-symbol-per-cell rendering.",
    )
    parser.add_argument(
        "-s", "--symbols",
        choices=list(SYMBOL_SETS),
        default="default",
        help="Symbol set (only used in legacy symbol mode; default: default)",
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
        default=12,
        help="Pixel size of each grid cell in the output PNG (default: 12; cell is 1:1 square now)",
    )
    parser.add_argument(
        "--grid",
        action="store_true",
        help="Draw grid lines in the output PNG (only with -o)",
    )
    # --- colour reduction ---
    parser.add_argument(
        "--posterize",
        type=int,
        default=0,
        help="Reduce to N flat colours (applied **after** downsampling "
             "for speed; default: 0 = off)",
    )
    parser.add_argument(
        "--palette",
        nargs="?",
        const="retro",
        default=None,
        choices=list(PALETTES),
        help="Map colours to a fixed palette for a cleaner bit look "
             "(default palette: retro).  Use --list-palettes to see all.",
    )
    parser.add_argument(
        "--list-palettes",
        action="store_true",
        help="List available palettes and exit",
    )
    parser.add_argument(
        "--dither",
        action="store_true",
        help="Apply Floyd-Steinberg dithering when reducing colours",
    )
    # --- gamma ---
    parser.add_argument(
        "--gamma",
        type=float,
        default=1.0,
        help="Gamma correction for brightness-symbol mapping "
             "(1.0 = linear; ~2.2 = perceptual; default: 1.0)",
    )
    # --- edge ---
    parser.add_argument(
        "--edge",
        type=float,
        nargs="?",
        const=40.0,
        default=0.0,
        help="Emphasise contours via edge detection "
             "(optional threshold; default: 40)",
    )
    parser.add_argument(
        "--edge-symbol",
        default="+",
        help="Symbol used for edge cells in symbol mode (default: +)",
    )
    parser.add_argument(
        "--list-symbols",
        action="store_true",
        help="List available symbol sets and exit",
    )
    return parser


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args, _ = parser.parse_known_args(argv)

    if args.list_symbols:
        _list_symbols()
    if args.list_palettes:
        _list_palettes()

    if args.preset:
        parser.set_defaults(**PRESETS[args.preset])
        args = parser.parse_args(argv)
    else:
        args = parser.parse_args(argv)

    # ── 1. Input ────────────────────────────────────────────────────────
    if not args.input or not os.path.isfile(args.input):
        print(f"Error: file not found — {args.input}", file=sys.stderr)
        sys.exit(1)

    img = load_image(args.input)
    img_w, img_h = img.size

    # ── 2. Grid dimensions ──────────────────────────────────────────────
    grid_w = args.width if args.width > 0 else _detect_terminal_width()
    grid_h = _resolve_height(img_w, img_h, grid_w, args.halfblock)

    term_rows = (grid_h + 1) // 2 if args.halfblock else grid_h
    print(f"Image: {img_w}×{img_h}  →  Mosaic: {grid_w}×{grid_h}"
          f"  →  Terminal: {grid_w}×{term_rows}  (halfblock={args.halfblock})",
          file=sys.stderr)

    # ── 3. Downsample → COLOR GRID (fast: resize only) ─────────────────
    colors = compute_grid(img, grid_w, grid_h)

    # ── 4. Posterize (on the small grid → way faster) ───────────────────
    if args.posterize > 1:
        colors = posterize(colors, args.posterize, dither=args.dither)

    # ── 5. Fixed palette mapping ────────────────────────────────────────
    if args.palette:
        colors = map_to_palette(colors, palette=PALETTES[args.palette])

    # ── 6. Edge mask ───────────────────────────────────────────────────
    edge_mask = None
    if args.edge > 0:
        edge_mask = detect_edges(colors, threshold=args.edge)

    # ── 7. Terminal render ─────────────────────────────────────────────
    if args.halfblock:
        render_terminal_halfblock(colors, out=sys.stdout)
    else:
        render_terminal(
            colors,
            symbol_set=args.symbols,
            invert=args.invert,
            gamma=args.gamma,
            edge_mask=edge_mask,
            edge_symbol=args.edge_symbol,
        )

    # ── 8. PNG output ──────────────────────────────────────────────────
    if args.output:
        save_output_image(
            colors,
            args.output,
            cell_size=args.cell_size,
            show_grid=args.grid,
            cell_aspect=1.0,  # grid is now 1:1 pixel aspect
            edge_mask=edge_mask,
        )
        print(f"Saved: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()

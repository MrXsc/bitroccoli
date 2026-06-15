"""
bitvibe.render - Terminal ANSI rendering and output image saving.

Supports multiple symbol sets. Each tile cell is rendered as a single
colored symbol in the terminal using ANSI TrueColor escape codes.
"""

import sys
import math
from typing import List, Optional, Tuple
from PIL import Image

from .mosaic import Color, ColorGrid

# ---------------------------------------------------------------------------
# Symbol sets: each is a list of characters sorted by increasing visual density
# (sparser → denser). Index is chosen by brightness level.
# ---------------------------------------------------------------------------
SYMBOL_SETS: dict[str, List[str]] = {
    "blocks": [" ", "░", "▒", "▓", "█"],
    "default": [" ", ".", "·", "*", "+", "%", "@", "#", "█"],
    "dots": [" ", "·", "•", "○", "◎", "◉", "●"],
    "cross": [" ", "·", "+", "╳", "✚", "█"],
    "simple": [" ", ".", "-", "+", "*", "%", "@"],
}

SYMBOL_SETS["all"] = sorted(set().union(*SYMBOL_SETS.values()))

# ANSI TrueColor control sequences
ANSI_RESET = "\033[0m"

# Edge detection threshold – larger = fewer edges detected
EDGE_THRESHOLD = 40.0


def _rgb_ansi_fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def _rgb_ansi_bg(r: int, g: int, b: int) -> str:
    return f"\033[48;2;{r};{g};{b}m"


def perceived_brightness(r: int, g: int, b: int) -> float:
    """Perceived luminance using Rec. 601 luma coefficients."""
    return 0.299 * r + 0.587 * g + 0.114 * b


# ---------------------------------------------------------------------------
# Edge detection
# ---------------------------------------------------------------------------


def _color_diff(a: Color, b: Color) -> float:
    """Simple RGB Euclidean distance for edge detection."""
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def detect_edges(
    colors: ColorGrid,
    threshold: float = EDGE_THRESHOLD,
) -> List[List[bool]]:
    """Return a boolean grid where True = edge cell.

    A cell is an edge if its colour difference with any 4-neighbour
    exceeds *threshold*.
    """
    rows = len(colors)
    cols = len(colors[0])
    edges: List[List[bool]] = [[False] * cols for _ in range(rows)]

    for y in range(rows):
        for x in range(cols):
            c = colors[y][x]
            # Check 4 neighbours
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < cols and 0 <= ny < rows:
                    if _color_diff(c, colors[ny][nx]) > threshold:
                        edges[y][x] = True
                        break
    return edges


# ---------------------------------------------------------------------------
# Terminal rendering
# ---------------------------------------------------------------------------


def render_terminal(
    colors: ColorGrid,
    symbol_set: str = "default",
    background: str = "dark",
    invert: bool = False,
    edge_mask: Optional[List[List[bool]]] = None,
    edge_symbol: str = "+",
    out=sys.stdout,
) -> None:
    """
    Write the mosaic to *out* (default stdout) using ANSI TrueColor.

    Parameters
    ----------
    colors : ColorGrid
        Grid of RGB tuples (rows × cols).
    symbol_set : str
        Key into SYMBOL_SETS.
    background : "dark" | "light"
        Whether the terminal background is dark or light.
    invert : bool
        Invert brightness-symbol mapping.
    edge_mask : list of lists of bool, optional
        True = edge cell → rendered with *edge_symbol* in inverted
        (light-on-dark / dark-on-light) colour for contrast.
    edge_symbol : str
        Character used for edge cells.
    out : text stream
    """
    symbols = SYMBOL_SETS.get(symbol_set, SYMBOL_SETS["default"])
    n_levels = len(symbols)
    bg_rgb = (0, 0, 0) if background == "dark" else (255, 255, 255)
    # Edge contrast colour (opposite of background)
    edge_fg = (255, 255, 255) if background == "dark" else (0, 0, 0)

    lines: List[str] = []
    for y, row in enumerate(colors):
        line_chars: List[str] = []
        for x, (r, g, b) in enumerate(row):
            is_edge = edge_mask is not None and edge_mask[y][x]

            if is_edge:
                # Edge cell: use contrasting symbol
                fg = _rgb_ansi_fg(*edge_fg)
                bg = _rgb_ansi_bg(r, g, b)
                line_chars.append(f"{fg}{bg}{edge_symbol}{ANSI_RESET}")
            else:
                brightness = perceived_brightness(r, g, b)
                idx = int(brightness / 256.0 * n_levels)
                idx = min(idx, n_levels - 1)
                if invert:
                    idx = n_levels - 1 - idx
                sym = symbols[idx]
                fg = _rgb_ansi_fg(r, g, b)
                bg = _rgb_ansi_bg(*bg_rgb)
                line_chars.append(f"{fg}{bg}{sym}{ANSI_RESET}")
        lines.append("".join(line_chars))

    out.write("\n".join(lines))
    out.write("\n")
    out.flush()


# ---------------------------------------------------------------------------
# Output image saving
# ---------------------------------------------------------------------------


def save_output_image(
    colors: ColorGrid,
    output_path: str,
    cell_size: int = 16,
    show_grid: bool = False,
    cell_aspect: float = 1.0,
    edge_mask: Optional[List[List[bool]]] = None,
) -> None:
    """
    Render the mosaic grid as a PNG image.

    Parameters
    ----------
    cell_aspect : float
        Height / width ratio of each cell.  Use >1.0 when the grid was
        computed with terminal char aspect compensation (e.g. 2.0 means
        each cell is twice as tall as wide).
    edge_mask : optional bool grid
        Edge cells are painted with a 50 % darker colour to emphasise
        contours.
    """
    if not colors or not colors[0]:
        return

    rows = len(colors)
    cols = len(colors[0])
    cell_h = int(cell_size * cell_aspect)

    if show_grid:
        img_w = cols * (cell_size + 1) + 1
        img_h = rows * (cell_h + 1) + 1
    else:
        img_w = cols * cell_size
        img_h = rows * cell_h

    img = Image.new("RGB", (img_w, img_h), (0, 0, 0))
    pixels = img.load()

    for y, row in enumerate(colors):
        for x, (r, g, b) in enumerate(row):
            is_edge = edge_mask is not None and edge_mask[y][x]
            cr, cg, cb = (r, g, b)
            if is_edge:
                # Darken edge cells to emphasise contours
                cr = int(r * 0.5)
                cg = int(g * 0.5)
                cb = int(b * 0.5)

            if show_grid:
                ox = x * (cell_size + 1) + 1
                oy = y * (cell_h + 1) + 1
            else:
                ox = x * cell_size
                oy = y * cell_h

            for dy in range(cell_h):
                for dx in range(cell_size):
                    px = ox + dx
                    py = oy + dy
                    if 0 <= px < img_w and 0 <= py < img_h:
                        pixels[px, py] = (cr, cg, cb)

    img.save(output_path)

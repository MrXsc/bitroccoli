"""
bitvibe.mosaic - Image loading, downsampling, colour reduction.
"""

from typing import List, Optional, Tuple
from PIL import Image, ImageOps

Color = Tuple[int, int, int]
ColorGrid = List[List[Color]]

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------


def _color_dist(a: Color, b: Color) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------

PALETTES: dict[str, List[Color]] = {
    # CGA-inspired 16-colour retro palette
    "retro": [
        (0, 0, 0),        # black
        (255, 255, 255),  # white
        (136, 0, 0),      # dark red
        (170, 136, 0),    # brown
        (0, 136, 0),      # dark green
        (0, 0, 170),      # dark blue
        (136, 0, 170),    # purple
        (0, 136, 170),    # teal
        (170, 170, 170),  # light grey
        (85, 85, 85),     # dark grey
        (255, 85, 85),    # light red
        (255, 255, 85),   # yellow
        (85, 255, 85),    # light green
        (85, 170, 255),   # light blue
        (255, 85, 255),   # magenta
        (85, 255, 255),   # cyan
    ],
    # Game Boy — 4 shades of olive green
    "gameboy": [
        (15, 56, 15),
        (48, 98, 48),
        (139, 172, 15),
        (155, 188, 15),
    ],
    # Grayscale — 8 stops
    "mono": [
        (i, i, i) for i in range(0, 256, 36)
    ],
    # PICO-8 inspired — vibrant, limited
    "pico8": [
        (0, 0, 0),
        (29, 43, 83),
        (126, 37, 83),
        (0, 135, 81),
        (171, 82, 54),
        (95, 87, 79),
        (194, 195, 199),
        (255, 241, 232),
        (255, 0, 77),
        (255, 163, 0),
        (255, 236, 39),
        (0, 228, 54),
        (41, 173, 255),
        (131, 118, 156),
        (255, 119, 168),
        (255, 204, 170),
    ],
    # Warm — browns / reds / oranges
    "warm": [
        (30, 20, 10),
        (80, 50, 30),
        (130, 70, 40),
        (180, 100, 50),
        (220, 140, 60),
        (240, 180, 90),
        (250, 210, 140),
        (255, 240, 200),
    ],
    # Cool — blues / teals / purples
    "cool": [
        (10, 10, 30),
        (20, 40, 80),
        (30, 80, 140),
        (50, 130, 190),
        (80, 170, 220),
        (130, 200, 240),
        (180, 220, 250),
        (220, 240, 255),
    ],
}


# ---------------------------------------------------------------------------
# Image I/O
# ---------------------------------------------------------------------------


def load_image(path: str) -> Image.Image:
    """Load an image from path, apply EXIF orientation, and convert to RGB."""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img) or img
    return img.convert("RGB")


# ---------------------------------------------------------------------------
# Downsampling → ColorGrid
# ---------------------------------------------------------------------------


def compute_grid(image: Image.Image, grid_w: int, grid_h: int) -> ColorGrid:
    """
    Downsample image to *grid_w* × *grid_h* and return the colour grid.

    Each cell holds the resampled (LANCZOS) colour for that region.
    """
    small = image.resize((grid_w, grid_h), Image.Resampling.LANCZOS)
    pixels = small.load()
    colors: ColorGrid = []
    for y in range(grid_h):
        row: List[Color] = []
        for x in range(grid_w):
            row.append(pixels[x, y])  # type: ignore[index]
        colors.append(row)
    return colors


# ---------------------------------------------------------------------------
# Posterize on a ColorGrid  (fast: works on the small grid)
# ---------------------------------------------------------------------------


def _colorgrid_to_image(colors: ColorGrid) -> Image.Image:
    h, w = len(colors), len(colors[0])
    img = Image.new("RGB", (w, h))
    for y in range(h):
        for x in range(w):
            img.putpixel((x, y), colors[y][x])
    return img


def _image_to_colorgrid(img: Image.Image) -> ColorGrid:
    w, h = img.size
    result: ColorGrid = []
    for y in range(h):
        row: List[Color] = []
        for x in range(w):
            row.append(img.getpixel((x, y)))
        result.append(row)
    return result


def posterize(
    colors: ColorGrid,
    num_colors: int,
    dither: bool = False,
) -> ColorGrid:
    """Reduce a :class:`ColorGrid` to *num_colors* via palette quantisation.

    This runs on the **already-downsampled** grid, which is orders of
    magnitude faster than posterizing the full-resolution image first.

    Parameters
    ----------
    dither : bool
        When True, apply Floyd-Steinberg error diffusion for smoother
        gradients with limited colours.
    """
    if num_colors < 2:
        return colors

    img = _colorgrid_to_image(colors)
    dither_method = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
    img = img.quantize(colors=num_colors, dither=dither_method).convert("RGB")
    return _image_to_colorgrid(img)


# ---------------------------------------------------------------------------
# Fixed-palette mapping
# ---------------------------------------------------------------------------


def map_to_palette(
    colors: ColorGrid,
    palette: Optional[List[Color]] = None,
) -> ColorGrid:
    """Map every cell to the nearest colour in a fixed palette.

    Produces a cleaner, more "retro" bit look.
    """
    pal = palette or PALETTES["retro"]
    result: ColorGrid = []
    for row in colors:
        new_row: List[Color] = []
        for c in row:
            # Nearest neighbour in palette
            best = min(pal, key=lambda pc: _color_dist(c, pc))
            new_row.append(best)
        result.append(new_row)
    return result


# ---------------------------------------------------------------------------
# Floyd-Steinberg dithering on a ColorGrid  (standalone, when not using PIL)
# ---------------------------------------------------------------------------


def floyd_steinberg_dither(
    colors: ColorGrid,
    palette: Optional[List[Color]] = None,
) -> ColorGrid:
    """Apply Floyd-Steinberg error diffusion against a fixed palette.

    Works cell-by-cell: quantises to the nearest palette colour and
    propagates the error to neighbours.
    """
    pal = palette or PALETTES["retro"]
    h, w = len(colors), len(colors[0])

    # Work on floats for error accumulation
    grid: List[List[Tuple[float, float, float]]] = [
        [(float(r), float(g), float(b)) for r, g, b in row]
        for row in colors
    ]

    for y in range(h):
        for x in range(w):
            r, g, b = grid[y][x]

            # Nearest palette colour
            best = min(pal, key=lambda pc: _color_dist(
                (int(r), int(g), int(b)), pc
            ))
            er, eg, eb = r - best[0], g - best[1], b - best[2]

            grid[y][x] = (float(best[0]), float(best[1]), float(best[2]))

            # Distribute error
            neighbours = [
                (x + 1, y, 7 / 16),
                (x - 1, y + 1, 3 / 16),
                (x, y + 1, 5 / 16),
                (x + 1, y + 1, 1 / 16),
            ]
            for nx, ny, factor in neighbours:
                if 0 <= nx < w and 0 <= ny < h:
                    cr, cg, cb = grid[ny][nx]
                    grid[ny][nx] = (
                        cr + er * factor,
                        cg + eg * factor,
                        cb + eb * factor,
                    )

    # Clamp & convert back
    result: ColorGrid = []
    for y in range(h):
        row: List[Color] = []
        for x in range(w):
            r = max(0, min(255, int(round(grid[y][x][0]))))
            g = max(0, min(255, int(round(grid[y][x][1]))))
            b = max(0, min(255, int(round(grid[y][x][2]))))
            row.append((r, g, b))
        result.append(row)
    return result

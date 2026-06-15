"""
bitvibe.mosaic - Image downsampling and color grid extraction.
"""

from typing import List, Tuple
from PIL import Image, ImageOps

Color = Tuple[int, int, int]
ColorGrid = List[List[Color]]


def load_image(path: str) -> Image.Image:
    """Load an image from path, apply EXIF orientation, and convert to RGB."""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img) or img
    return img.convert("RGB")


def posterize(image: Image.Image, num_colors: int) -> Image.Image:
    """Reduce to *num_colors* via palette quantization for flat color regions.

    Pass *num_colors* <= 1 to skip.
    """
    if num_colors < 2:
        return image
    return image.quantize(colors=num_colors).convert("RGB")


def compute_grid(image: Image.Image, grid_w: int, grid_h: int) -> ColorGrid:
    """
    Downsample image to grid_w × grid_h and return the color grid.

    Each cell in the returned grid holds the average (resampled) RGB color
    for that region of the original image.
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

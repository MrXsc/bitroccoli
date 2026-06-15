# README Redesign — Minimal + Comparison Image

## TL;DR
Redesign README.md with a clean, minimal layout featuring a side-by-side original-vs-mosaic comparison image. Remove old standalone preview images.

---

## Task

- [ ] 1. **Overwrite README.md with new design**

  **Content to write**:
```markdown
<p align="center">
  <img src="logo.svg" width="48">
</p>

<h1 align="center">BitVibe</h1>

<p align="center">
  Turn any image into a bit-style pixel-art mosaic,<br>
  rendered in the terminal with ANSI color and saveable as PNG.
</p>

<br>

<p align="center">
  <img src="preview_comparison.png" width="100%" alt="Original vs Mosaic comparison">
</p>

<br>

## Usage

```bash
pip install Pillow

# Terminal render
python3 bitvibe.py -i photo.JPG

# Sharp pixel-art style + PNG
python3 bitvibe.py --preset sharp -i photo.JPG -o mosaic.png
```

<br>

## Options

| Flag | Description |
|---|---|
| `-i`, `--input` | Input image path |
| `-w`, `--width` | Mosaic width in tiles (default: `80`) |
| `-s`, `--symbols` | `default` · `blocks` · `dots` · `cross` · `simple` |
| `-o`, `--output` | Save as PNG |
| `--preset` | `sharp` = `-w 120 -s blocks --posterize 12` |
| `--posterize N` | Reduce to N flat colours |
| `--edge` | Emphasize contours |

See `python3 bitvibe.py --help` for all flags.

<br>

## License

MIT
```

- [ ] 2. **Remove old standalone preview images**
  - Delete `preview_sharp.png`
  - Delete `preview_toys.png`

- [ ] 3. **Stage, amend author, commit, push**
  - `git add README.md`
  - `git rm preview_sharp.png preview_toys.png`
  - `git commit --author="MrXsc <MrXsc@users.noreply.github.com>"`
  - If committer is wrong, run filter-branch to fix
  - `git push`

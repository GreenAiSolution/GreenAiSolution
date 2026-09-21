# Field Guide 01 — Build an AI Empire

Cleaned-up version of the 7-layer frontend blueprint poster.

| file | what it is |
| --- | --- |
| `build-an-ai-empire.png` | 900 × 1125, lossless — the master |
| `build-an-ai-empire.webp` | same size, ~400 KB, for posting |
| `build-an-ai-empire@2x.webp` | 1800 × 2250, crisp type for large screens |
| `source/original.webp` | the render this was fixed up from |
| `build_poster.py` | regenerates everything from the source |

## What was wrong with the original

The background plate was fine; the UI chrome on top of it was not.

- **Every layer card was drawn twice.** An empty duplicate box sat above each
  card — about 12 px up on layers 07–03, and ~40 px up on 02 and 01, where it
  read as a large empty box floating over the artwork. Same duplication on the
  connector panels.
- **Titles ran past their boxes.** `SHIP THE SHELL`, `FIND THE WEDGE` and
  `REVENUE LOOP` all crossed the card's right border.
- **The third line of copy fell outside the card.** `Stream every AI state`,
  `Promise one measurable win`, `Trigger lifecycle journeys` and the rest sat
  below the bottom border instead of inside it.
- **Connector panels were inconsistent.** Tiles overflowed the panel edge, one
  tile per panel carried a stray coloured border, borders doubled up, and the
  `Perplexity` label was set smaller than its neighbours.

## What changed

The artwork is untouched. The chrome was thrown away and redrawn as HTML/CSS on
a grid: left cards all at x 56–296, connector panels all at x 646–872, and both
columns sharing one top/height per row so they line up. Type is sized to fit
inside the padding box — the longest title now stops 20 px short of the card
edge. Layers 02 and 01 use taller cards because that is what it takes to cover
the duplicate boxes the original left behind.

The 21 connector glyphs are lifted pixel-for-pixel out of the original render, so
the logos are exactly as they were drawn.

## Rebuilding

```sh
pip install pillow
python3 build_poster.py            # or --chromium /path/to/chrome
```

Needs Chromium and, on the first run, network access to fetch Inter and Archivo
into `fonts/`. Both `fonts/` and the intermediate `build/` directory are ignored.

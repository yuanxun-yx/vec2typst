# vec2typst

Extract text from SVG figures into editable Typst overlays while preserving the original vector graphics.
A Typst equivalent of Inkscape's PDF+LaTeX SVG export.

> [!NOTE]
> vec2typst is still in an early stage.
> Future versions may also support PDF-based workflows.

## Why not just use `image()`?

SVG figures can already be embedded directly in Typst with `image()`.
However, the text inside the SVG remains part of the original graphic and cannot participate 
in Typst's typesetting system.

vec2typst extracts SVG text into editable Typst overlays while preserving the original vector graphics.

The goal is to preserve the original SVG rendering as closely as possible while 
allowing figure texts to become native Typst content. This makes it possible to:

- use native Typst content inside figure texts, including math, styling
- adjust text styling with `set text(...)`

## Installation

```bash
uv tool install vec2typst
```

## Usage

```bash
vec2typst figure.svg
```

This generates: 
- `figure.typ`
- `figure_notext.svg`

To include the figure in your document:

```typst
#figure(
  {
    import "figure.typ": fig
    set text(size: .75em)   // adjustment
    fig(width: 50%)
  },
  caption: [Caption.],
) <fig>
```
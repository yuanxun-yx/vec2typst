# vec2typst

Extract text from SVG figures into editable Typst overlays while preserving the original vector graphics.
A Typst equivalent of Inkscape's PDF+LaTeX SVG export.

> [!NOTE]
> vec2typst is still in an early stage.
> Currently, SVG transforms are not yet supported.
> Future versions may also support PDF-based workflows.

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
- `figure_notext.svg`. 

To include the figure in your document:

```typst
#figure(
  {
    import "figure.typ": fig
    set text(size: .75em)
    fig(width: 50%)
  },
  caption: [Caption.],
) <fig>
```
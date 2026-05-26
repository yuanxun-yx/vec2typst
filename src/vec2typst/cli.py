import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from .affine import Affine2D, rotate, translate


@dataclass(frozen=True)
class Text:
    alignment: str
    dx: float
    dy: float
    text: str
    rotate: float
    font_size: float


TRANSFORM_RE = re.compile(r"([a-z]+)\s*\(([^)]*)\)")
SIZE_RE = re.compile(r"([-+]?\d*\.?\d+)([a-z%]*)")

SIZE_CONVERTION_PX: dict[str, float] = {
    "px": 1.0,
    "pt": 4 / 3,
    "pc": 16,
    "mm": 96 / 25.4,
    "cm": 96 / 2.54,
    "in": 96,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    args = parser.parse_args()

    file_path = args.file
    svg_path = file_path.parent / f"{file_path.stem}_notext.svg"
    typ_path = file_path.with_suffix(".typ")

    texts: list[Text] = []

    parser = etree.XMLParser()
    tree = etree.parse(file_path, parser)
    root = tree.getroot()
    view_box = root.get("viewBox")
    x_min, y_min, w, h = map(float, view_box.split(" "))
    for elem in root.xpath(
        ".//svg:text", namespaces={"svg": "http://www.w3.org/2000/svg"}
    ):
        t = elem.xpath("string()")
        x = float(elem.get("x", "0"))
        y = float(elem.get("y", "0"))

        style = elem.get("style")
        res = {}
        for field in style.split(";"):
            if not field:
                continue
            k, v = field.split(":")
            res[k.strip()] = v.strip()
        style = res

        if "font-size" in style:
            value, unit = SIZE_RE.match(style["font-size"]).groups()
            value = float(value)
            if unit in SIZE_CONVERTION_PX:
                value *= SIZE_CONVERTION_PX[unit]
            else:
                raise NotImplementedError(f"unknown unit: {unit}")
            # base size of svg: 16px
            font_size = value / 16
        else:
            font_size = 1

        transform = elem.get("transform")
        affine = Affine2D()
        if transform:
            for name, args in TRANSFORM_RE.findall(transform):
                values = map(float, re.split(r"[,\s]+", args.strip()))
                if name == "rotate":
                    affine @= rotate(*values)
                elif name == "translate":
                    affine @= translate(*values)
                else:
                    raise NotImplementedError(f"unknown transform: {name}")

        x, y = affine @ (x, y)

        dx = (x - x_min) / w
        text_anchor = style.get("text-anchor", "start")
        if text_anchor == "start":
            anchor = "left"
        elif text_anchor == "middle":
            anchor = "center"
            dx = dx - 0.5
        elif text_anchor == "end":
            anchor = "right"
            dx = dx - 1.0
        else:
            raise ValueError(f"unknown text anchor: {text_anchor}")

        # vertical text anchor for svg is text baseline
        # use approximation bottom here instead
        dy = (y - y_min) / h - 1.0

        texts.append(
            Text(
                alignment=anchor,
                dx=dx,
                dy=dy,
                text=t,
                rotate=affine.angle,
                font_size=font_size,
            )
        )

        elem.getparent().remove(elem)

    if not texts:
        raise ValueError("no text elements found")

    tree.write(svg_path, pretty_print=True, xml_declaration=True)
    with typ_path.open("w") as f:
        f.write(
            "#let p(alignment, ..args) = place(alignment + bottom, ..args)\n"
            "#let fig(..args) = box(..args)[\n"
            f'#image("{svg_path.name}", width: 100%)\n'
        )
        for t in texts:
            f.write(
                f"#p({t.alignment}, dx: {t.dx * 100:.2f}%, dy: {t.dy * 100:.2f}%)[\n"
            )
            depth = 1
            if t.font_size != 1:
                f.write(f"#set text(size: {t.font_size:.2f}em)\n")
            if t.rotate != 0:
                f.write(f"#rotate({t.rotate:.3f}deg, origin: {t.alignment} + bottom)[")
                depth += 1
            f.write(t.text)
            f.write("]" * depth)
            f.write("\n")
        f.write("]")


if __name__ == "__main__":
    main()

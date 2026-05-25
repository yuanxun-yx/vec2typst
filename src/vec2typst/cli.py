import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from lxml import etree


@dataclass(frozen=True)
class Text:
    alignment: str
    dx: float
    dy: float
    text: str
    rotate: float


TRANSFORM_RE = re.compile(r"([a-zA-Z]+)\s*\(([^)]*)\)")


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

        dx = (x - x_min) / w
        text_anchor = style["text-anchor"]
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

        transform = elem.get("transform")
        rotate = 0.0
        if transform:
            for name, args in TRANSFORM_RE.findall(transform):
                values = map(float, re.split(r"[,\s]+", args.strip()))
                if name == "rotate":
                    angle, cx, cy = values
                    if angle == 0:
                        continue
                    if cx != x:
                        raise NotImplementedError(
                            f"rotate cx {cx} does not match element x {x}"
                        )
                    if cy != y:
                        raise NotImplementedError(
                            f"rotate cy {cy} does not match element y {y}"
                        )
                    rotate += angle
                else:
                    raise NotImplementedError(f"unknown transform: {name}")

        texts.append(Text(alignment=anchor, dx=dx, dy=dy, text=t, rotate=rotate))

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
            f.write(f"#p({t.alignment}, dx: {t.dx * 100:.2f}%, dy: {t.dy * 100:.2f}%)[")
            depth = 1
            if t.rotate != 0:
                f.write(f"#rotate({t.rotate:.3f}deg, origin: {t.alignment} + bottom)[")
                depth += 1
            f.write(t.text)
            f.write("]" * depth)
            f.write("\n")
        f.write("]")


if __name__ == "__main__":
    main()

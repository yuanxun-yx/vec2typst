from lxml import etree
import argparse
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class Text:
    alignment: str
    dx: float
    dy: float
    text: str


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
        x = float(elem.get("x"))
        y = float(elem.get("y"))

        style = elem.get("style")
        res = {}
        for field in style.split(";"):
            k, v = field.split(":")
            res[k] = v
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

        texts.append(Text(alignment=anchor, dx=dx, dy=dy, text=t))

        elem.getparent().remove(elem)

    tree.write(svg_path, pretty_print=True, xml_declaration=True)
    with typ_path.open("w") as f:
        f.write(
            "#let p(alignment, ..args, body) = place(alignment + bottom, ..args, body)\n"
            "#let fig(width: auto) = box(width: width)[\n"
            f'#image("{svg_path.name}", width: 100%)\n'
        )
        for t in texts:
            f.write(
                f"  #p({t.alignment}, dx: {t.dx * 100:.2f}%, dy: {t.dy * 100:.2f}%)[{t.text}]\n"
            )
        f.write("]")


if __name__ == "__main__":
    main()

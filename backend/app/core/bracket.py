from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment

LAYERS = {
    "OUTLINE": {"color": 7, "lineweight": 50},
    "HOLE": {"color": 1, "lineweight": 25},
    "DIM": {"color": 3, "lineweight": 18},
    "TEXT": {"color": 7, "lineweight": 18},
    "FRAME": {"color": 8, "lineweight": 25},
    "CUT": {"color": 5, "lineweight": 25},
}


def build(spec: dict, out_dxf: str | Path) -> Path:
    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = 4  # mm
    doc.header["$DIMLFAC"] = 1.0
    for name, attr in LAYERS.items():
        doc.layers.add(name, color=attr["color"], lineweight=attr["lineweight"])

    msp = doc.modelspace()
    length = float(spec["length"])
    width = float(spec["width"])
    drawing_no = str(spec.get("drawing_no", "SW-0000-000"))
    material = str(spec.get("material", "304"))
    surface = str(spec.get("surface", "拉丝"))

    outline = spec.get("outline") or []
    radius = min(float(spec.get("corner_radius", 0) or 0), min(length, width) / 2)
    chamfer = min(float(spec.get("chamfer", 0) or 0), min(length, width) / 2)
    if outline:
        msp.add_lwpolyline(
            [(float(point["x"]), float(point["y"])) for point in outline],
            close=True,
            dxfattribs={"layer": "OUTLINE"},
        )
    elif radius <= 0 and chamfer > 0:
        c = chamfer
        msp.add_lwpolyline(
            [
                (c, 0), (length - c, 0), (length, c), (length, width - c),
                (length - c, width), (c, width), (0, width - c), (0, c),
            ],
            close=True,
            dxfattribs={"layer": "OUTLINE"},
        )
    elif radius > 0:
        b = 0.41421356237
        points = [
            (radius, 0, 0),
            (length - radius, 0, b),
            (length, radius, 0),
            (length, width - radius, b),
            (length - radius, width, 0),
            (radius, width, b),
            (0, width - radius, 0),
            (0, radius, b),
        ]
        msp.add_lwpolyline(
            points,
            format="xyb",
            close=True,
            dxfattribs={"layer": "OUTLINE"},
        )
    else:
        msp.add_lwpolyline(
            [(0, 0), (length, 0), (length, width), (0, width)],
            close=True,
            dxfattribs={"layer": "OUTLINE"},
        )

    for cutout in spec.get("cutouts", []) or []:
        cx, cy = float(cutout["x"]), float(cutout["y"])
        cw, ch = float(cutout["width"]), float(cutout["height"])
        msp.add_lwpolyline(
            [(cx, cy), (cx + cw, cy), (cx + cw, cy + ch), (cx, cy + ch)],
            close=True,
            dxfattribs={"layer": "CUT"},
        )

    for slot in spec.get("slots", []) or []:
        sx, sy = float(slot["x"]), float(slot["y"])
        sl, sw = float(slot["length"]), float(slot["width"])
        if sl < sw:
            raise ValueError("槽长不能小于槽宽")
        points = [
            (sx, sy - sw / 2, 0),
            (sx + sl - sw, sy - sw / 2, 1),
            (sx + sl - sw, sy + sw / 2, 0),
            (sx, sy + sw / 2, 1),
        ]
        msp.add_lwpolyline(points, format="xyb", close=True, dxfattribs={"layer": "HOLE"})

    for hole in spec.get("holes", []):
        x, y, d = float(hole["x"]), float(hole["y"]), float(hole["d"])
        msp.add_circle((x, y), d / 2, dxfattribs={"layer": "HOLE"})
        r = d / 2 + 3
        msp.add_line((x - r, y), (x + r, y), dxfattribs={"layer": "DIM"})
        msp.add_line((x, y - r), (x, y + r), dxfattribs={"layer": "DIM"})

    common = {"dimtxt": 3.5, "dimasz": 3.0, "dimlfac": 1.0}
    dim = msp.add_linear_dim(
        base=(0, -18), p1=(0, 0), p2=(length, 0),
        dimstyle="EZDXF", override=common, dxfattribs={"layer": "DIM"},
    )
    dim.render()
    dim = msp.add_linear_dim(
        base=(-18, 0), p1=(0, 0), p2=(0, width), angle=90,
        dimstyle="EZDXF", override=common, dxfattribs={"layer": "DIM"},
    )
    dim.render()

    msp.add_lwpolyline(
        [(0, width + 10), (length, width + 10), (length, width + 62), (0, width + 62)],
        close=True,
        dxfattribs={"layer": "FRAME"},
    )
    rows = [
        ("图号", drawing_no),
        ("名称", str(spec.get("title", "安装板"))),
        ("材料", material),
        ("表面", surface),
        ("比例", "1:1"),
        ("单位", "CAD Agent Demo"),
    ]
    for index, (key, value) in enumerate(rows):
        y = width + 56 - index * 8.4
        msp.add_text(key, height=3.0, dxfattribs={"layer": "TEXT"}).set_placement((4, y))
        msp.add_text(value, height=3.0, dxfattribs={"layer": "TEXT"}).set_placement(
            (22, y), align=TextEntityAlignment.LEFT
        )

    out = Path(out_dxf)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(out)
    return out

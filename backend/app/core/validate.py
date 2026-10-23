import ezdxf


def _inside(x: float, y: float, points: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(points) - 1
    for i, (xi, yi) in enumerate(points):
        xj, yj = points[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def validate(path: str, spec: dict | None = None) -> list[str]:
    issues: list[str] = []
    try:
        doc = ezdxf.readfile(path)
    except Exception as exc:  # noqa: BLE001
        return [f"DXF 无法读取: {exc}"]

    auditor = doc.audit()
    issues.extend(f"DXF 结构错误: {e.message}" for e in auditor.errors)

    layers = {layer.dxf.name for layer in doc.layers}
    for required in ("OUTLINE", "HOLE", "DIM", "TEXT", "FRAME"):
        if required not in layers:
            issues.append(f"缺少图层 {required}")

    msp = doc.modelspace()
    outlines = list(msp.query("LWPOLYLINE[layer=='OUTLINE']"))
    if not outlines:
        issues.append("缺少外形轮廓")
    elif not outlines[0].closed:
        issues.append("外形轮廓未闭合")

    circles = list(msp.query("CIRCLE[layer=='HOLE']"))
    if not circles:
        issues.append("缺少孔")

    if len(list(msp.query("DIMENSION"))) < 2:
        issues.append("尺寸标注不足")

    if spec:
        length = float(spec["length"])
        width = float(spec["width"])
        for hole in spec.get("holes", []):
            x, y = float(hole["x"]), float(hole["y"])
            if not (0 < x < length and 0 < y < width):
                issues.append(f"孔位超界: ({x},{y})")
        outline = spec.get("outline") or []
        polygon = [(float(point["x"]), float(point["y"])) for point in outline]
        for point in outline:
            x, y = float(point["x"]), float(point["y"])
            if not (0 <= x <= length and 0 <= y <= width):
                issues.append(f"轮廓点超界: ({x},{y})")
        if polygon:
            for hole in spec.get("holes", []):
                if not _inside(float(hole["x"]), float(hole["y"]), polygon):
                    issues.append(f"孔位不在轮廓内: ({hole['x']},{hole['y']})")
            for slot in spec.get("slots", []) or []:
                sx, sy = float(slot["x"]), float(slot["y"])
                sl, sw = float(slot["length"]), float(slot["width"])
                for px, py in ((sx + sw / 2, sy), (sx + sl - sw / 2, sy)):
                    if not _inside(px, py, polygon):
                        issues.append(f"槽位不在轮廓内: ({sx},{sy})")
                        break
            for cutout in spec.get("cutouts", []) or []:
                cx, cy = float(cutout["x"]), float(cutout["y"])
                cw, ch = float(cutout["width"]), float(cutout["height"])
                for px, py in ((cx, cy), (cx + cw, cy), (cx, cy + ch), (cx + cw, cy + ch)):
                    if not _inside(px, py, polygon):
                        issues.append(f"开口不在轮廓内: ({cx},{cy})")
                        break
        for cutout in spec.get("cutouts", []) or []:
            x, y = float(cutout["x"]), float(cutout["y"])
            cw, ch = float(cutout["width"]), float(cutout["height"])
            if x < 0 or y < 0 or x + cw > length or y + ch > width:
                issues.append(f"开口超界: ({x},{y})")
        for slot in spec.get("slots", []) or []:
            x, y = float(slot["x"]), float(slot["y"])
            sl, sw = float(slot["length"]), float(slot["width"])
            if x < 0 or y - sw / 2 < 0 or x + sl > length or y + sw / 2 > width:
                issues.append(f"槽位超界: ({x},{y})")

    return issues

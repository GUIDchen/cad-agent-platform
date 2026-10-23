import csv
import io
import json

from ..models import Drawing, Version


def build_bom_csv(drawing: Drawing, version: Version) -> str:
    spec = json.loads(version.params_json or "{}")
    holes = spec.get("holes", []) or []
    hole_positions = ";".join(f"{h['x']},{h['y']}" for h in holes)

    rows = [
        ["图号", "名称", "材料", "表面", "长度mm", "宽度mm", "厚度mm", "孔数", "孔位"],
        [
            drawing.drawing_no,
            drawing.title,
            spec.get("material", ""),
            spec.get("surface", ""),
            spec.get("length", ""),
            spec.get("width", ""),
            spec.get("thickness", ""),
            len(holes),
            hole_positions,
        ],
    ]
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    for row in rows:
        writer.writerow(row)
    return "\ufeff" + buffer.getvalue()

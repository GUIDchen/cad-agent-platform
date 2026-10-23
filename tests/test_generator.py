from pathlib import Path

import ezdxf

from app.core.bracket import build
from app.core.preview import render
from app.core.validate import validate

SPEC = {
    "drawing_no": "SW-2026-099",
    "title": "测试板",
    "length": 180,
    "width": 120,
    "material": "304",
    "surface": "拉丝",
    "holes": [{"x": 20, "y": 20, "d": 6.6}, {"x": 160, "y": 100, "d": 6.6}],
}


def test_build_and_validate(tmp_path: Path):
    dxf = build(SPEC, tmp_path / "out.dxf")
    assert dxf.exists()
    assert validate(str(dxf), SPEC) == []


def test_render(tmp_path: Path):
    dxf = build(SPEC, tmp_path / "out.dxf")
    png = render(dxf, tmp_path / "out.png")
    assert png.exists() and png.stat().st_size > 1000


def test_corner_radius(tmp_path: Path):
    spec = dict(SPEC)
    spec["corner_radius"] = 10
    dxf = build(spec, tmp_path / "rounded.dxf")
    doc = ezdxf.readfile(dxf)
    bulges = [point[2] for pline in doc.modelspace().query("LWPOLYLINE") for point in pline.get_points("xyb")]
    assert any(abs(bulge) > 0 for bulge in bulges)
    assert validate(str(dxf), spec) == []


def test_slot(tmp_path: Path):
    spec = dict(SPEC)
    spec["slots"] = [{"x": 60, "y": 60, "length": 40, "width": 10}]
    dxf = build(spec, tmp_path / "slot.dxf")
    doc = ezdxf.readfile(dxf)
    slot_lines = [
        pline for pline in doc.modelspace().query("LWPOLYLINE")
        if pline.dxf.layer == "HOLE" and any(abs(point[2]) > 0 for point in pline.get_points("xyb"))
    ]
    assert slot_lines
    assert validate(str(dxf), spec) == []


def test_cutout(tmp_path: Path):
    spec = dict(SPEC)
    spec["cutouts"] = [{"x": 70, "y": 50, "width": 40, "height": 20}]
    dxf = build(spec, tmp_path / "cutout.dxf")
    doc = ezdxf.readfile(dxf)
    cuts = [pline for pline in doc.modelspace().query("LWPOLYLINE") if pline.dxf.layer == "CUT"]
    assert cuts
    assert validate(str(dxf), spec) == []


def test_cutout_out_of_bounds(tmp_path: Path):
    spec = dict(SPEC)
    spec["cutouts"] = [{"x": 170, "y": 110, "width": 40, "height": 20}]
    dxf = build(spec, tmp_path / "cutout-bad.dxf")
    assert any("开口超界" in issue for issue in validate(str(dxf), spec))


def test_out_of_bounds(tmp_path: Path):
    bad = dict(SPEC)
    bad["holes"] = [{"x": 500, "y": 500, "d": 6.6}]
    dxf = build(bad, tmp_path / "bad.dxf")
    assert any("超界" in issue for issue in validate(str(dxf), bad))


def test_polygon_outline(tmp_path: Path):
    spec = dict(SPEC)
    spec["holes"] = [{"x": 20, "y": 20, "d": 6.6}, {"x": 80, "y": 40, "d": 6.6}]
    spec["outline"] = [
        {"x": 0, "y": 0},
        {"x": 100, "y": 0},
        {"x": 100, "y": 60},
        {"x": 60, "y": 60},
        {"x": 60, "y": 120},
        {"x": 0, "y": 120},
    ]
    dxf = build(spec, tmp_path / "polygon.dxf")
    doc = ezdxf.readfile(dxf)
    outlines = [pline for pline in doc.modelspace().query("LWPOLYLINE") if pline.dxf.layer == "OUTLINE"]
    assert outlines and len(list(outlines[0].get_points("xyb"))) >= 6
    assert validate(str(dxf), spec) == []


def test_hole_outside_outline(tmp_path: Path):
    spec = dict(SPEC)
    spec["holes"] = [{"x": 80, "y": 100, "d": 6.6}]
    spec["outline"] = [
        {"x": 0, "y": 0},
        {"x": 100, "y": 0},
        {"x": 100, "y": 60},
        {"x": 60, "y": 60},
        {"x": 60, "y": 120},
        {"x": 0, "y": 120},
    ]
    dxf = build(spec, tmp_path / "outside.dxf")
    issues = validate(str(dxf), spec)
    assert any("不在轮廓内" in issue for issue in issues)


def test_chamfer(tmp_path: Path):
    spec = dict(SPEC)
    spec["chamfer"] = 10
    dxf = build(spec, tmp_path / "chamfer.dxf")
    doc = ezdxf.readfile(dxf)
    outlines = [pline for pline in doc.modelspace().query("LWPOLYLINE") if pline.dxf.layer == "OUTLINE"]
    assert outlines and len(list(outlines[0].get_points("xyb"))) == 8
    assert validate(str(dxf), spec) == []

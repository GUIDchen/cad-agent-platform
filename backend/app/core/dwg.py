import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def convert(src: Path, dst: Path) -> Path:
    src = Path(src)
    dst = Path(dst)
    if not src.exists():
        raise FileNotFoundError(src)

    dwg2dxf_bin = os.getenv("DWG2DXF_BIN", "")
    oda = os.getenv("ODA_FILE_CONVERTER", "")

    if dwg2dxf_bin:
        subprocess.run([dwg2dxf_bin, str(src), str(dst)], check=True, capture_output=True, text=True, timeout=120)
    elif oda:
        with tempfile.TemporaryDirectory(prefix="dwg-convert-") as tmp:
            in_dir = Path(tmp) / "in"
            out_dir = Path(tmp) / "out"
            in_dir.mkdir()
            out_dir.mkdir()
            shutil.copy2(src, in_dir / src.name)
            subprocess.run(
                [oda, str(in_dir), str(out_dir), "ACAD2018", "DXF", "0", "1", src.name],
                check=True, capture_output=True, text=True, timeout=300,
            )
            produced = out_dir / (src.stem + ".dxf")
            if not produced.exists():
                raise RuntimeError("ODA 未生成 DXF")
            shutil.copy2(produced, dst)
    else:
        raise RuntimeError("未配置 DWG2DXF_BIN 或 ODA_FILE_CONVERTER")

    if not dst.exists() or dst.stat().st_size == 0:
        raise RuntimeError("DWG 转换失败")
    return dst

import json
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..config import MAX_UPLOAD_BYTES
from ..core.dwg import convert
from ..core.preview import render
from ..models import Drawing, User, Version
from ..storage import get_storage, sha256_file
from ..virus_scan import VirusFound, scan_bytes


def _next_version(db: Session, drawing_id: int) -> int:
    current = db.scalar(select(func.max(Version.version)).where(Version.drawing_id == drawing_id))
    return int(current or 0) + 1


def create_uploaded_version(db: Session, drawing: Drawing, user: User, file: UploadFile) -> Version:
    filename = file.filename or "upload.dxf"
    suffix = Path(filename).suffix.lower()
    if suffix not in (".dxf", ".dwg"):
        raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED", "message": "仅支持 DXF/DWG"})

    version_no = _next_version(db, drawing.id)
    key_dxf = f"{drawing.drawing_no}/v{version_no}_upload.dxf"
    key_png = f"{drawing.drawing_no}/v{version_no}_upload.png"

    with tempfile.TemporaryDirectory(prefix="cad-upload-") as tmp_dir:
        content = file.file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail={"code": "TOO_LARGE", "message": "文件超过上传上限"})
        try:
            scan_bytes(content)
        except VirusFound as exc:
            raise HTTPException(status_code=400, detail={"code": "VIRUS", "message": f"文件未通过病毒扫描: {exc}"}) from exc
        if suffix == ".dxf" and b"SECTION" not in content[:2048] and not content.lstrip().startswith(b"AutoCAD Binary DXF"):
            raise HTTPException(status_code=400, detail={"code": "BAD_DXF", "message": "不是有效的 DXF 文件"})
        tmp = Path(tmp_dir) / ("upload" + suffix)
        tmp.write_bytes(content)
        source = tmp
        if suffix == ".dwg":
            source = Path(tmp_dir) / "converted.dxf"
            try:
                convert(tmp, source)
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=400, detail={"code": "DWG_CONVERT", "message": f"DWG 转换失败: {exc}"}) from exc
        try:
            png = render(source, Path(tmp_dir) / "upload.png")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail={"code": "BAD_DXF", "message": f"图纸无法渲染: {exc}"}) from exc

        store = get_storage()
        store.save(source, key_dxf)
        store.save(png, key_png)
        sha = sha256_file(source)

    version = Version(
        drawing_id=drawing.id,
        version=version_no,
        file_path=key_dxf,
        preview_path=key_png,
        sha256=sha,
        params_json=json.dumps({"source": "upload", "filename": filename}, ensure_ascii=False),
        created_by=user.id,
    )
    db.add(version)
    db.flush()
    drawing.current_version_id = version.id
    drawing.status = "pending_review"
    write_audit(
        db, user.id, "version.upload", "drawing", drawing.drawing_no,
        {"version": version_no, "filename": filename},
    )
    db.commit()
    db.refresh(version)
    return version

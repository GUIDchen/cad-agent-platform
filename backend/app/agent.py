import json
import re

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .audit import write_audit
from .config import EXECUTION_MODE, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from .llm import parse_requirement
from .models import Drawing, Project, User
from .permissions import accessible_project_ids
from .services.generation import create_job, run_job

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_drawings",
            "description": "列出当前用户可见的图纸",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_drawing",
            "description": "创建图纸",
            "parameters": {
                "type": "object",
                "properties": {
                    "drawing_no": {"type": "string"},
                    "title": {"type": "string"},
                },
                "required": ["drawing_no"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_drawing",
            "description": "按参数生成 DXF 版本",
            "parameters": {
                "type": "object",
                "properties": {
                    "drawing_no": {"type": "string"},
                    "length": {"type": "number"},
                    "width": {"type": "number"},
                    "thickness": {"type": "number"},
                    "material": {"type": "string"},
                    "hole_count": {"type": "integer"},
                    "hole_diameter": {"type": "number"},
                },
                "required": ["drawing_no"],
            },
        },
    },
]


def _first_project(db: Session, user: User) -> Project:
    stmt = select(Project).order_by(Project.id)
    ids = accessible_project_ids(db, user)
    if ids is not None:
        stmt = stmt.where(Project.id.in_(ids)) if ids else stmt.where(Project.id == -1)
    project = db.scalar(stmt)
    if not project:
        raise HTTPException(status_code=400, detail={"code": "NO_PROJECT", "message": "没有可用项目"})
    return project


def _holes(count: int, diameter: float) -> list[dict]:
    points = [(20, 20), (160, 20), (20, 100), (160, 100)]
    return [{"x": x, "y": y, "d": diameter} for x, y in points[: max(1, min(count, 4))]]


def _create(db: Session, user: User, drawing_no: str, title: str = "") -> dict:
    existing = db.scalar(select(Drawing).where(Drawing.drawing_no == drawing_no))
    if existing:
        return {"drawing_no": existing.drawing_no, "id": existing.id, "existed": True}
    project = _first_project(db, user)
    drawing = Drawing(project_id=project.id, drawing_no=drawing_no, title=title or drawing_no)
    db.add(drawing)
    db.flush()
    write_audit(db, user.id, "drawing.create", "drawing", drawing.drawing_no, {"title": drawing.title, "by": "agent"})
    db.commit()
    db.refresh(drawing)
    return {"drawing_no": drawing.drawing_no, "id": drawing.id, "existed": False}


def _generate(db: Session, user: User, args: dict) -> dict:
    drawing = db.scalar(select(Drawing).where(Drawing.drawing_no == args["drawing_no"]))
    if not drawing:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "图纸不存在"})
    spec = {
        "length": float(args.get("length", 180)),
        "width": float(args.get("width", 120)),
        "thickness": float(args.get("thickness", 6)),
        "material": args.get("material", "304"),
        "surface": "拉丝",
        "holes": _holes(int(args.get("hole_count", 4)), float(args.get("hole_diameter", 6.6))),
    }
    job = create_job(db, drawing, user, spec, "generate_bracket")
    write_audit(db, user.id, "generate.request", "drawing", drawing.drawing_no, {"job_id": job.id, "by": "agent"})
    db.commit()
    if EXECUTION_MODE == "inline":
        run_job(job.id)
    return {"job_id": job.id, "drawing_no": drawing.drawing_no}


def _list(db: Session, user: User) -> dict:
    stmt = select(Drawing).order_by(Drawing.id.desc())
    ids = accessible_project_ids(db, user)
    if ids is not None:
        stmt = stmt.where(Drawing.project_id.in_(ids)) if ids else stmt.where(Drawing.project_id == -1)
    rows = list(db.scalars(stmt))
    return {"items": [{"drawing_no": d.drawing_no, "title": d.title, "status": d.status} for d in rows]}


def _run_tool(db: Session, user: User, name: str, args: dict) -> dict:
    if name == "list_drawings":
        return _list(db, user)
    if name == "create_drawing":
        return _create(db, user, args["drawing_no"], args.get("title", ""))
    if name == "generate_drawing":
        return _generate(db, user, args)
    raise HTTPException(status_code=400, detail={"code": "UNKNOWN_TOOL", "message": name})


def _fallback(db: Session, user: User, message: str) -> dict:
    steps: list[dict] = []
    match = re.search(r"(?:图号\s*)?([A-Za-z]{2,}-\d{4}-\d{3})", message)
    drawing_no = match.group(1) if match else ""

    if "创建" in message or "新建" in message:
        if not drawing_no:
            drawing_no = "SW-2026-999"
        title = message[:40]
        result = _create(db, user, drawing_no, title)
        steps.append({"tool": "create_drawing", "result": result})

    if "生成" in message or "出图" in message:
        if not drawing_no and steps:
            drawing_no = steps[-1]["result"]["drawing_no"]
        if drawing_no:
            spec, _ = parse_requirement(message)
            args = {
                "drawing_no": drawing_no,
                "length": spec["length"],
                "width": spec["width"],
                "thickness": spec["thickness"],
                "material": spec["material"],
                "hole_count": len(spec["holes"]),
                "hole_diameter": spec["holes"][0]["d"] if spec["holes"] else 6.6,
            }
            result = _generate(db, user, args)
            steps.append({"tool": "generate_drawing", "result": result})

    if not steps:
        result = _list(db, user)
        steps.append({"tool": "list_drawings", "result": result})

    return {"reply": "已完成：" + ", ".join(s["tool"] for s in steps), "steps": steps}


def _llm_agent(db: Session, user: User, message: str) -> dict:
    messages = [
        {"role": "system", "content": "你是 CAD 平台助手，按用户要求调用工具，最后用中文简要回复。"},
        {"role": "user", "content": message},
    ]
    steps: list[dict] = []
    for _ in range(5):
        response = httpx.post(
            f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json={"model": LLM_MODEL, "messages": messages, "tools": TOOLS, "temperature": 0.1},
            timeout=30,
        )
        response.raise_for_status()
        msg = response.json()["choices"][0]["message"]
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            return {"reply": msg.get("content", ""), "steps": steps}
        for call in calls:
            name = call["function"]["name"]
            args = json.loads(call["function"].get("arguments") or "{}")
            result = _run_tool(db, user, name, args)
            steps.append({"tool": name, "result": result})
            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result, ensure_ascii=False)}
            )
    return {"reply": "工具调用次数超限", "steps": steps}


def run_agent(db: Session, user: User, message: str) -> dict:
    if LLM_API_KEY and LLM_BASE_URL:
        try:
            return _llm_agent(db, user, message)
        except Exception:  # noqa: BLE001
            pass
    return _fallback(db, user, message)

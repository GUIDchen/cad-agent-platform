import json
import re

import httpx

from .config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

SYSTEM_PROMPT = (
    "你是制图参数抽取器。根据用户描述输出 JSON，字段："
    "length,width,thickness,material,surface,holes[{x,y,d}]。"
    "单位毫米；不确定时用默认值；只输出 JSON。"
)


def _normalize(data: dict, text: str) -> dict:
    holes = []
    for hole in data.get("holes", []) or []:
        holes.append({"x": float(hole["x"]), "y": float(hole["y"]), "d": float(hole["d"])})
    if not holes:
        holes = _corner_holes(4, 6.6)
    return {
        "length": float(data.get("length", 180)),
        "width": float(data.get("width", 120)),
        "thickness": float(data.get("thickness", 6)),
        "material": str(data.get("material", "304")),
        "surface": str(data.get("surface", "拉丝")),
        "holes": holes,
    }


def _corner_holes(count: int, d: float) -> list[dict]:
    points = [(20, 20), (160, 20), (20, 100), (160, 100)]
    return [{"x": x, "y": y, "d": d} for x, y in points[: max(1, min(count, 4))]]


def _fallback(text: str) -> dict:
    length, width = 180.0, 120.0
    match = re.search(r"(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)", text)
    if match:
        length, width = float(match.group(1)), float(match.group(2))

    count_match = re.search(r"(\d+)\s*个", text)
    count = int(count_match.group(1)) if count_match else 4
    dia_match = re.search(r"[Mm](\d+(?:\.\d+)?)", text)
    dia = float(dia_match.group(1)) if dia_match else 6.6
    material = "304" if "304" in text else "Q235"
    surface = "拉丝" if "拉丝" in text else "喷砂"

    return {
        "length": length,
        "width": width,
        "thickness": 6.0,
        "material": material,
        "surface": surface,
        "holes": _corner_holes(count, dia),
    }


def _remote(text: str) -> dict:
    response = httpx.post(
        f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        },
        timeout=20,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def parse_requirement(text: str) -> tuple[dict, str]:
    if LLM_API_KEY and LLM_BASE_URL:
        try:
            return _normalize(_remote(text), text), "llm"
        except Exception:  # noqa: BLE001
            pass
    return _normalize(_fallback(text), text), "fallback"

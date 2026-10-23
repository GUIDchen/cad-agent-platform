import json
import time
import uuid
from pathlib import Path

import httpx

from .config import COMFY_TIMEOUT, COMFY_URL, COMFY_WORKFLOW


def prepare_workflow(template, prompt: str, width: int, height: int, negative: str = "", seed: int | None = None):
    if isinstance(template, dict):
        return {
            key: prepare_workflow(value, prompt, width, height, negative, seed)
            for key, value in template.items()
        }
    if isinstance(template, list):
        return [prepare_workflow(value, prompt, width, height, negative, seed) for value in template]
    if isinstance(template, str):
        return (
            template.replace("{{PROMPT}}", prompt)
            .replace("{{NEGATIVE}}", negative)
            .replace("{{WIDTH}}", str(width))
            .replace("{{HEIGHT}}", str(height))
            .replace("{{SEED}}", str(seed if seed is not None else 0))
        )
    return template


def _load_workflow() -> dict:
    if not COMFY_WORKFLOW:
        raise RuntimeError("未配置 COMFY_WORKFLOW")
    data = json.loads(Path(COMFY_WORKFLOW).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise RuntimeError("ComfyUI 工作流为空或格式错误")
    classes = [node.get("class_type", "") for node in data.values() if isinstance(node, dict)]
    for required in ("KSampler", "CheckpointLoaderSimple", "SaveImage"):
        if required not in classes:
            raise RuntimeError(f"ComfyUI 工作流缺少节点 {required}")
    text = json.dumps(data, ensure_ascii=False)
    for placeholder in ("{{PROMPT}}", "{{WIDTH}}", "{{HEIGHT}}"):
        if placeholder not in text:
            raise RuntimeError(f"ComfyUI 工作流缺少占位符 {placeholder}")
    return data


def generate(prompt: str, width: int, height: int, negative: str = "", seed: int | None = None) -> bytes:
    if not COMFY_URL:
        raise RuntimeError("未配置 COMFY_URL")
    workflow = prepare_workflow(_load_workflow(), prompt, width, height, negative, seed)
    client_id = uuid.uuid4().hex

    response = httpx.post(
        f"{COMFY_URL.rstrip('/')}/prompt",
        json={"prompt": workflow, "client_id": client_id},
        timeout=30,
    )
    response.raise_for_status()
    prompt_id = response.json()["prompt_id"]

    deadline = time.time() + COMFY_TIMEOUT
    image = None
    while time.time() < deadline:
        history = httpx.get(f"{COMFY_URL.rstrip('/')}/history/{prompt_id}", timeout=10)
        history.raise_for_status()
        data = history.json().get(prompt_id, {})
        outputs = data.get("outputs") or {}
        for output in outputs.values():
            images = output.get("images") or []
            if images:
                image = images[0]
                break
        if image:
            break
        time.sleep(1)

    if not image:
        raise RuntimeError("ComfyUI 生成超时")

    view = httpx.get(
        f"{COMFY_URL.rstrip('/')}/view",
        params={
            "filename": image["filename"],
            "subfolder": image.get("subfolder", ""),
            "type": image.get("type", "output"),
        },
        timeout=30,
    )
    view.raise_for_status()
    return view.content

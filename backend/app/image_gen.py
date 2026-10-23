import io
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

from .config import COMFY_URL, COMFY_WORKFLOW, IMAGE_API_KEY, IMAGE_API_URL


def _font(size: int):
    for path in (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _mock(prompt: str, width: int, height: int) -> bytes:
    image = Image.new("RGB", (width, height), (15, 23, 42))
    draw = ImageDraw.Draw(image)
    font = _font(max(16, width // 40))
    small = _font(max(12, width // 80))
    for x in range(0, width, 40):
        draw.line([(x, 0), (x, height)], fill=(30, 41, 59))
    for y in range(0, height, 40):
        draw.line([(0, y), (width, y)], fill=(30, 41, 59))
    draw.rectangle([20, 20, width - 20, height - 20], outline=(56, 189, 248), width=3)
    draw.text((36, 36), prompt[:120], fill=(226, 232, 240), font=font)
    draw.text((36, height - 48), "mock image", fill=(148, 163, 184), font=small)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def generate(
    prompt: str,
    width: int = 1024,
    height: int = 768,
    negative_prompt: str = "",
    seed: int | None = None,
) -> tuple[bytes, str]:
    if COMFY_URL and COMFY_WORKFLOW:
        from .comfy import generate as comfy_generate

        return comfy_generate(prompt, width, height, negative_prompt, seed), "comfy"
    if IMAGE_API_URL:
        response = httpx.post(
            IMAGE_API_URL,
            headers={"Authorization": f"Bearer {IMAGE_API_KEY}"} if IMAGE_API_KEY else {},
            json={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "seed": seed,
                "width": width,
                "height": height,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.content, "remote"
    return _mock(prompt, width, height), "mock"

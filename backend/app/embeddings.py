import hashlib
import math
import os

import httpx

DIM = 64


def local_embed(text: str) -> list[float]:
    vec = [0.0] * DIM
    clean = "".join(text.lower().split())
    for index in range(max(0, len(clean) - 1)):
        gram = clean[index : index + 2]
        digest = int(hashlib.md5(gram.encode("utf-8")).hexdigest()[:8], 16)
        vec[digest % DIM] += 1.0
    norm = math.sqrt(sum(value * value for value in vec)) or 1.0
    return [value / norm for value in vec]


def embed(text: str) -> list[float]:
    url = os.getenv("EMBEDDING_API_URL", "")
    if url:
        model = os.getenv("EMBEDDING_MODEL", "bge-m3")
        try:
            response = httpx.post(url, json={"input": text, "model": model}, timeout=20)
            response.raise_for_status()
            data = response.json()
            if "data" in data:
                return [float(value) for value in data["data"][0]["embedding"]]
        except Exception:  # noqa: BLE001
            pass
    return local_embed(text)


def cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    ln = math.sqrt(sum(a * a for a in left)) or 1.0
    rn = math.sqrt(sum(b * b for b in right)) or 1.0
    return dot / (ln * rn)

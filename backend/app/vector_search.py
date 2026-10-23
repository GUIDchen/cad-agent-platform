import os

import httpx


def search(vector: list[float], limit: int = 5) -> list[dict] | None:
    url = os.getenv("VECTOR_SEARCH_URL", "")
    if not url:
        return None
    try:
        response = httpx.post(url, json={"vector": vector, "limit": limit}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("results") or []
    except Exception:  # noqa: BLE001
        return None

import hashlib


def content_hash(title: str, content: str) -> str:
    return hashlib.sha256((title + "\n" + content).encode("utf-8")).hexdigest()


def chunk_text(text: str, size: int = 400, overlap: int = 80) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    chunks = []
    start = 0
    step = max(1, size - overlap)
    while start < len(text):
        chunks.append(text[start : start + size])
        start += step
    return chunks

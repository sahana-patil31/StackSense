from typing import Iterable


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 120) -> list[str]:
    if not text:
        return []
    step = max(1, chunk_size - overlap)
    return [text[start:start + chunk_size] for start in range(0, len(text), step)]


def iter_chunks(text: str, chunk_size: int = 1200) -> Iterable[str]:
    return iter(chunk_text(text, chunk_size))

import json
import os
from pathlib import Path
from typing import List

import faiss

from app.config import settings
from app.embeddings import get_embedder


def _chunk_text(text: str, min_len: int = 40) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n\n")]
    return [p for p in paragraphs if len(p) >= min_len]


def load_kb_chunks(kb_dir: str) -> List[dict]:
    chunks = []
    for path in sorted(Path(kb_dir).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for chunk in _chunk_text(text):
            chunks.append({"source": path.name, "text": chunk})
    return chunks


def build_index(kb_dir: str = None, index_dir: str = None) -> int:
    kb_dir = kb_dir or settings.kb_dir
    index_dir = index_dir or settings.faiss_index_dir
    os.makedirs(index_dir, exist_ok=True)

    chunks = load_kb_chunks(kb_dir)
    if not chunks:
        raise ValueError(f"No chunks found in {kb_dir}")

    embeddings = get_embedder().encode([c["text"] for c in chunks])

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, os.path.join(index_dir, "index.faiss"))
    with open(os.path.join(index_dir, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    return len(chunks)


if __name__ == "__main__":
    count = build_index()
    print(f"Indexed {count} chunks from '{settings.kb_dir}' into '{settings.faiss_index_dir}'")

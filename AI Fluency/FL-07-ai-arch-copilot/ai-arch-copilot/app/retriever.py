import json
import os
from typing import List

import faiss

from app.config import settings
from app.embeddings import get_embedder


class Retriever:
    def __init__(self, index_dir: str = None):
        index_dir = index_dir or settings.faiss_index_dir
        index_path = os.path.join(index_dir, "index.faiss")
        chunks_path = os.path.join(index_dir, "chunks.json")

        if not os.path.exists(index_path) or not os.path.exists(chunks_path):
            raise FileNotFoundError(
                f"No FAISS index found in {index_dir}. Run `python -m app.ingest` first."
            )

        self.index = faiss.read_index(index_path)
        with open(chunks_path, encoding="utf-8") as f:
            self.chunks = json.load(f)

    def search(self, query: str, top_k: int = 3) -> List[dict]:
        vec = get_embedder().encode([query])
        scores, indices = self.index.search(vec, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append({**self.chunks[idx], "score": float(score)})
        return results

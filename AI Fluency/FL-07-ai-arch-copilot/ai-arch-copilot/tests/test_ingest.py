import json
import os

from app.embeddings import set_embedder
from app.ingest import build_index, load_kb_chunks
from tests.fakes import FakeWordOverlapEmbedder


def test_load_kb_chunks_splits_by_paragraph(tmp_path):
    doc = tmp_path / "sample.md"
    doc.write_text(
        "This is the first paragraph and it is long enough to count.\n\n"
        "Short.\n\n"
        "This is the second paragraph and it is also long enough to count."
    )
    chunks = load_kb_chunks(str(tmp_path))
    assert len(chunks) == 2  # "Short." dropped for being under min_len
    assert all(c["source"] == "sample.md" for c in chunks)


def test_build_index_writes_faiss_and_metadata(tmp_path):
    set_embedder(FakeWordOverlapEmbedder())

    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "doc.md").write_text(
        "Never implement features that were not approved in the spec.\n\n"
        "Chunk the source text by natural paragraph boundaries for RAG."
    )

    index_dir = tmp_path / "index"
    count = build_index(kb_dir=str(kb_dir), index_dir=str(index_dir))

    assert count == 2
    assert os.path.exists(index_dir / "index.faiss")
    with open(index_dir / "chunks.json") as f:
        chunks = json.load(f)
    assert len(chunks) == 2

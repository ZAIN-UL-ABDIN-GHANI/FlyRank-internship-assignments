from app.embeddings import set_embedder
from app.ingest import build_index
from app.retriever import Retriever
from tests.fakes import FakeWordOverlapEmbedder


def _build_real_kb_index(tmp_path):
    set_embedder(FakeWordOverlapEmbedder())
    index_dir = tmp_path / "index"
    build_index(kb_dir="kb", index_dir=str(index_dir))
    return Retriever(index_dir=str(index_dir))


def test_retrieves_approval_rule_for_unapproved_feature_query(tmp_path):
    retriever = _build_real_kb_index(tmp_path)
    results = retriever.search("should the agent implement features that were not approved", top_k=1)
    assert len(results) == 1
    assert results[0]["source"] == "development_rules.md"
    assert "approved" in results[0]["text"].lower()


def test_retrieves_faiss_chunking_rule_for_rag_query(tmp_path):
    retriever = _build_real_kb_index(tmp_path)
    results = retriever.search("how should I chunk documents for the FAISS index", top_k=1)
    assert len(results) == 1
    assert results[0]["source"] == "rag_best_practices.md"


def test_missing_index_raises_clear_error(tmp_path):
    try:
        Retriever(index_dir=str(tmp_path / "does_not_exist"))
        assert False, "expected FileNotFoundError"
    except FileNotFoundError as e:
        assert "app.ingest" in str(e)

# RAG and FAISS Best Practices

## Chunking
- Chunk by natural boundaries (paragraphs, sections) rather than fixed character counts when the source is structured text.
- Drop chunks that are too short to carry meaning; they add noise without useful signal.

## Embeddings
- Normalize embedding vectors and use inner-product (cosine) search for consistent, comparable similarity scores.
- Keep the embedding model consistent between ingestion and query time; mixing models breaks retrieval.

## Index Management
- Rebuild the FAISS index whenever the source documents change. Stale indexes silently return outdated context.
- Store chunk text and source metadata alongside the index so retrieved results can be traced back to their origin.

## Evaluation
- Test retrieval with a handful of known queries and expected sources before wiring it into an agent.
- Prefer a small top-k (2-4) for focused context over large top-k that dilutes relevance.

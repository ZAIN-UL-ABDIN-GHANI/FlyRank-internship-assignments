# Project Summary

**Goal:** LangGraph agent that gathers requirements, plans features, and reviews code against project rules + FAISS-retrieved context.

**Progress:** All 5 phases complete plus LLM provider swap. 23/23 tests passing.

**Completed:** FastAPI skeleton; FAISS RAG (sentence-transformers, KB in `kb/`); planning agent (structured `ImplementationPlan`); code review agent (structured `CodeReviewReport`); logging, startup config check, global error handler, pinned deps, README; LLM provider switched from Anthropic Claude to Google Gemini (`langchain-google-genai`, official `google-genai` SDK under the hood).

**Decisions:** Code review node runs only after requirements are complete; single-string `code` input for MVP; embedding tests use a fake local embedder (sandbox has no HF network access - real model works in normal environments); `_build_llm()` now returns `ChatGoogleGenerativeAI`, key read from `GOOGLE_API_KEY`.

**Known issues:** No multi-file/diff parsing; no server-side session store.

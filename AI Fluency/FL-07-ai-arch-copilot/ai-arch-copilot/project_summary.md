# Project Summary

**Goal:** LangGraph agent gathering requirements, planning features, and reviewing code against project rules + FAISS context.

**Progress:** FL-06 + FL-07 (4 sprints) complete. 48/48 tests passing.

**Completed:** RAG/FAISS, planning, code review (Gemini), sessions, diff/multi-file review, standalone review endpoint. Sprint 4: `Dockerfile` (builds FAISS index on first start if missing, volume-mounted `data/`), `.dockerignore`, `.github/workflows/ci.yml` (pytest + Docker build on push/PR).

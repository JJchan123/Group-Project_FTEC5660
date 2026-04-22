"""Tool-style retrieval helpers for the anti-scam RAG subsystem."""

from __future__ import annotations

from guardian.rag.retriever import RagRetriever


def retrieve_scam_patterns(
    query: str,
    top_k: int | None = None,
    category_filter: str | None = None,
) -> dict:
    retriever = RagRetriever()
    return retriever.retrieve_scam_patterns(
        query=query,
        top_k=top_k,
        category_filter=category_filter,
    ).to_dict()


def retrieve_transfer_guidance(
    query: str,
    top_k: int | None = None,
    category_filter: str | None = None,
) -> dict:
    retriever = RagRetriever()
    return retriever.retrieve_transfer_guidance(
        query=query,
        top_k=top_k,
        category_filter=category_filter,
    ).to_dict()

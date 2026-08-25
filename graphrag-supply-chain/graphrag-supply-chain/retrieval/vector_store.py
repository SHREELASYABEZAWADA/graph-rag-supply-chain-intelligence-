"""Embedding + semantic search over unstructured supply-chain text."""
from __future__ import annotations

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings


class VectorStore:
    def __init__(self):
        self._embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        )
        self._store = Chroma(
            collection_name=settings.vector_collection_name,
            embedding_function=self._embeddings,
            persist_directory=settings.chroma_persist_dir,
        )
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=100
        )

    def add_text(self, text: str, source: str, extra_metadata: dict | None = None):
        chunks = self._splitter.split_text(text)
        docs = [
            Document(
                page_content=chunk,
                metadata={
                    "source": source,
                    "chunk_id": f"{source}#chunk_{i}",
                    **(extra_metadata or {}),
                },
            )
            for i, chunk in enumerate(chunks)
        ]
        self._store.add_documents(docs)

    def similarity_search(self, query: str, k: int | None = None) -> list[Document]:
        return self._store.similarity_search(query, k=k or settings.top_k_vector)

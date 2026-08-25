"""
Hybrid retriever: runs semantic (vector) search to find relevant text and
candidate entities, then expands those entities in the graph to pull in
relationship context that pure vector search would miss (multi-hop
dependencies, exact chains, affected parties).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from retrieval.graph_store import GraphStore
from retrieval.vector_store import VectorStore
from config import settings


@dataclass
class RetrievedContext:
    vector_snippets: list[dict] = field(default_factory=list)   # {"text", "source"}
    graph_paths: list[dict] = field(default_factory=list)        # {"path_nodes", "path_rels"}
    dependency_rows: list[dict] = field(default_factory=list)    # supplier->product->warehouse->customer
    incidents: list[dict] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        parts = []

        if self.vector_snippets:
            parts.append("### Relevant documents (semantic search)")
            for s in self.vector_snippets:
                parts.append(f"- [{s['source']}] {s['text']}")

        if self.dependency_rows:
            parts.append("\n### Supply-chain dependency chains (graph)")
            for row in self.dependency_rows:
                parts.append(
                    f"- {row.get('supplier')} -> supplies -> {row.get('product')} "
                    f"-> stocked in -> {row.get('warehouse')} -> ships to -> {row.get('customer')}"
                )

        if self.graph_paths:
            parts.append("\n### Related graph paths")
            for p in self.graph_paths:
                nodes = p.get("path_nodes", [])
                rels = p.get("path_rels", [])
                chain = []
                for i, node in enumerate(nodes):
                    chain.append(str(node))
                    if i < len(rels):
                        chain.append(f"-[{rels[i]}]->")
                parts.append("- " + " ".join(chain))

        if self.incidents:
            parts.append("\n### Related incidents")
            for inc in self.incidents:
                parts.append(
                    f"- {inc.get('date')} ({inc.get('severity')}): "
                    f"{inc.get('description')} [affects: {inc.get('affected')}]"
                )

        return "\n".join(parts) if parts else "No relevant context found."


class HybridRetriever:
    def __init__(self, graph_store: GraphStore, vector_store: VectorStore):
        self.graph_store = graph_store
        self.vector_store = vector_store

    def retrieve(self, question: str, focus_entity: str | None = None) -> RetrievedContext:
        context = RetrievedContext()

        # 1. Vector search over unstructured docs
        docs = self.vector_store.similarity_search(question)
        context.vector_snippets = [
            {"text": d.page_content, "source": d.metadata.get("source", "unknown")}
            for d in docs
        ]

        # 2. Resolve a focus entity (explicit or best-guess from the question)
        candidate = focus_entity or self._guess_entity(question)
        if candidate:
            matches = self.graph_store.find_entity_by_name(candidate)
            if matches:
                node = matches[0]["node"]
                node_id = node.get("id")

                context.graph_paths = self.graph_store.expand_neighborhood(
                    node_id, depth=settings.graph_traversal_depth
                )
                context.dependency_rows = self.graph_store.find_dependency_chain(candidate)
                context.incidents = self.graph_store.find_related_incidents(candidate)

        return context

    @staticmethod
    def _guess_entity(question: str) -> str | None:
        """
        Very lightweight heuristic: pull out capitalized multi-word spans as
        likely entity names (e.g. 'Acme Metals', 'Northwind Traders').
        Swap this for an LLM-based NER call or function-calling extraction
        for production use.
        """
        import re

        matches = re.findall(r"\b([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)+)\b", question)
        return matches[0] if matches else None

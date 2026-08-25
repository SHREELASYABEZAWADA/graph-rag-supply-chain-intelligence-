"""Ingests free-text supply-chain documents: embeds the raw text for vector
search AND runs LLM entity extraction to merge new nodes/edges (e.g.
Incidents) into the graph."""
from __future__ import annotations

from pathlib import Path

from ingestion.entity_extractor import EntityExtractor
from retrieval.graph_store import GraphStore
from retrieval.vector_store import VectorStore


class UnstructuredLoader:
    def __init__(self, graph_store: GraphStore, vector_store: VectorStore):
        self.graph_store = graph_store
        self.vector_store = vector_store
        self.extractor = EntityExtractor()

    def load_file(self, path: str | Path):
        path = Path(path)
        text = path.read_text(encoding="utf-8")

        # 1. Embed for semantic search
        self.vector_store.add_text(text, source=path.name)

        # 2. Extract entities/relationships and merge into the graph
        extracted = self.extractor.extract(text)

        for entity in extracted["entities"]:
            self.graph_store.upsert_node(
                entity["label"], entity["id"], entity.get("properties", {})
            )

        for rel in extracted["relationships"]:
            source_label = self._label_lookup(extracted["entities"], rel["source_id"])
            target_label = self._label_lookup(extracted["entities"], rel["target_id"])
            if not (source_label and target_label):
                continue
            self.graph_store.upsert_relationship(
                source_label, rel["source_id"],
                target_label, rel["target_id"],
                rel["type"], rel.get("properties", {}),
            )

        print(
            f"  {path.name}: embedded text + extracted "
            f"{len(extracted['entities'])} entities / {len(extracted['relationships'])} relationships"
        )

    @staticmethod
    def _label_lookup(entities: list[dict], entity_id: str) -> str | None:
        for e in entities:
            if e["id"] == entity_id:
                return e["label"]
        return None

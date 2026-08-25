"""Ingest structured CSVs + unstructured incident notes into Neo4j + Chroma.

Usage:
    python scripts/build_graph.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ingestion.structured_loader import StructuredLoader
from ingestion.unstructured_loader import UnstructuredLoader
from retrieval.graph_store import GraphStore
from retrieval.vector_store import VectorStore
from schema.graph_schema import CONSTRAINT_STATEMENTS

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "sample_data"


def main():
    graph_store = GraphStore()
    vector_store = VectorStore()

    print("Applying schema constraints...")
    graph_store.apply_constraints(CONSTRAINT_STATEMENTS)

    print("\nLoading structured data (CSV -> Neo4j)...")
    StructuredLoader(graph_store, DATA_DIR).load_all()

    print("\nLoading unstructured data (text -> vector store + LLM extraction -> Neo4j)...")
    unstructured_loader = UnstructuredLoader(graph_store, vector_store)
    unstructured_loader.load_file(DATA_DIR / "incident_notes.txt")

    graph_store.close()
    print("\nDone. Graph and vector index are ready.")


if __name__ == "__main__":
    main()
